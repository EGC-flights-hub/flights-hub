import os
import time
import threading
import ipaddress
from dataclasses import dataclass
from typing import Optional
from flask import request
from flask_login import current_user, login_user

from app.modules.auth.models import User
from app.modules.auth.repositories import UserRepository
from app.modules.profile.models import UserProfile
from app.modules.profile.repositories import UserProfileRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService


@dataclass
class ThrottleConfig:
    max_attempts: int = 5  # nº de intentos fallidos permitidos
    window_seconds: int = 300  # ventana de cómputo
    lock_seconds: int = 600  # duración del bloqueo


class AuthenticationService(BaseService):
    def __init__(self, throttle_config: Optional[ThrottleConfig] = None):
        super().__init__(UserRepository())
        self.user_profile_repository = UserProfileRepository()

        # Config y estado de último login
        self.tcfg = throttle_config or ThrottleConfig()
        self.error_code: Optional[str] = None
        self.error_message: Optional[str] = None
        self.remaining_attempts: Optional[int] = None

        self._fails: dict[str, dict] = {}
        self._fails_lock = threading.Lock()

    # ---------- Helpers ----------
    def _client_ip(self) -> str:
        xff = request.headers.get("X-Forwarded-For", "")
        if xff:
            return xff.split(",")[0].strip()
        return request.remote_addr or "0.0.0.0"

    def _norm_ip(self, ip: str) -> str:
        try:
            return str(ipaddress.ip_address(ip))
        except Exception:
            return "unknown"

    def _key(self, email: str, ip: str) -> str:
        email = (email or "").strip().lower()
        ip = self._norm_ip(ip)
        return f"{email}|{ip}"

    def _purge_if_expired(self, rec: dict) -> None:
        now = time.time()
        first_ts = rec.get("first_ts", now)
        locked_until = rec.get("locked_until")
        if locked_until is None and (now - first_ts) >= self.tcfg.window_seconds:
            rec["count"] = 0
            rec["first_ts"] = now

    def _is_locked(self, email: str, ip: str) -> bool:
        k = self._key(email, ip)
        now = time.time()
        with self._fails_lock:
            rec = self._fails.get(k)
            if not rec:
                return False
            lu = rec.get("locked_until")
            if lu is None:
                self._purge_if_expired(rec)
                return False
            if now >= lu:
                # bloqueo caducado → limpiar y permitir
                rec["locked_until"] = None
                rec["count"] = 0
                rec["first_ts"] = now
                return False
            return True

    def _register_failure(self, email: str, ip: str) -> int:
        """
        Incrementa fallos y aplica bloqueo si procede.
        Devuelve el contador de fallos tras este intento (>=1).
        """
        k = self._key(email, ip)
        now = time.time()
        with self._fails_lock:
            rec = self._fails.get(k)
            if rec is None:
                rec = {"count": 0, "first_ts": now, "locked_until": None}
                self._fails[k] = rec

            if rec["locked_until"] is not None and now >= rec["locked_until"]:
                rec["locked_until"] = None
                rec["count"] = 0
                rec["first_ts"] = now

            if rec["locked_until"] is None:
                if (now - rec["first_ts"]) >= self.tcfg.window_seconds:
                    rec["count"] = 0
                    rec["first_ts"] = now

                rec["count"] += 1

                if rec["count"] >= self.tcfg.max_attempts:
                    rec["locked_until"] = now + self.tcfg.lock_seconds

            return rec["count"]

    def _reset_failures(self, email: str, ip: str) -> None:
        k = self._key(email, ip)
        now = time.time()
        with self._fails_lock:
            rec = self._fails.get(k)
            if rec:
                rec["count"] = 0
                rec["first_ts"] = now
                rec["locked_until"] = None

    def login(self, email, password, remember=True):
        self.error_code = None
        self.error_message = None
        self.remaining_attempts = None

        ip = self._client_ip()

        if self._is_locked(email, ip):
            self.error_code = "too_many_failed_attempts"
            self.error_message = "Too many failed sign-in attempts. Your access is temporarily blocked."
            self.remaining_attempts = 0
            return False

        user = self.repository.get_by_email(email)

        if user is None:
            count = self._register_failure(email, ip)

            if self._is_locked(email, ip):
                self.error_code = "too_many_failed_attempts"
                self.error_message = "Too many failed sign-in attempts. Your access is temporarily blocked."
                self.remaining_attempts = 0
                return False

            self.error_code = "invalid_credentials"
            self.error_message = "Invalid credentials. Please try again later or reset your password."
            self.remaining_attempts = max(self.tcfg.max_attempts - count, 0)
            return False

        if user.check_password(password):
            login_user(user, remember=remember)
            self._reset_failures(email, ip)
            return True

        count = self._register_failure(email, ip)

        if self._is_locked(email, ip):
            self.error_code = "too_many_failed_attempts"
            self.error_message = "Too many failed sign-in attempts. Your access is temporarily blocked."
            self.remaining_attempts = 0
            return False

        self.error_code = "invalid_credentials"
        self.error_message = "Invalid credentials. Please try again later or reset your password."
        self.remaining_attempts = max(self.tcfg.max_attempts - count, 0)
        return False

    def is_email_available(self, email: str) -> bool:
        return self.repository.get_by_email(email) is None

    def create_with_profile(self, **kwargs):
        try:
            email = kwargs.pop("email", None)
            password = kwargs.pop("password", None)
            name = kwargs.pop("name", None)
            surname = kwargs.pop("surname", None)

            if not email:
                raise ValueError("Email is required.")
            if not password:
                raise ValueError("Password is required.")
            if not name:
                raise ValueError("Name is required.")
            if not surname:
                raise ValueError("Surname is required.")

            user_data = {"email": email, "password": password}

            profile_data = {
                "name": name,
                "surname": surname,
            }

            user = self.create(commit=False, **user_data)
            profile_data["user_id"] = user.id
            self.user_profile_repository.create(**profile_data)
            self.repository.session.commit()
        except Exception as exc:
            self.repository.session.rollback()
            raise exc
        return user

    def update_profile(self, user_profile_id, form):
        if form.validate():
            updated_instance = self.update(user_profile_id, **form.data)
            return updated_instance, None

        return None, form.errors

    def get_authenticated_user(self) -> User | None:
        if current_user.is_authenticated:
            return current_user
        return None

    def get_authenticated_user_profile(self) -> UserProfile | None:
        if current_user.is_authenticated:
            return current_user.profile
        return None

    def temp_folder_by_user(self, user: User) -> str:
        return os.path.join(uploads_folder_name(), "temp", str(user.id))
