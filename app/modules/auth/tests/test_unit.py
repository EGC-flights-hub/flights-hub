import os
import pytest
from flask import url_for
from flask_login import login_user, logout_user

from app.modules.auth.repositories import UserRepository
from app.modules.auth.services import AuthenticationService, ThrottleConfig
from app.modules.profile.repositories import UserProfileRepository


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Add HERE new elements to the database that you want to exist in the test context.
        # DO NOT FORGET to use db.session.add(<element>) and db.session.commit() to save the data.
        pass

    yield test_client


def test_login_success(test_client):
    response = test_client.post(
        "/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=True
    )

    assert response.request.path != url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_login_unsuccessful_bad_email(test_client):
    response = test_client.post(
        "/login", data=dict(email="bademail@example.com", password="test1234"), follow_redirects=True
    )

    assert response.request.path == url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_login_unsuccessful_bad_password(test_client):
    response = test_client.post(
        "/login", data=dict(email="test@example.com", password="basspassword"), follow_redirects=True
    )

    assert response.request.path == url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_signup_user_no_name(test_client):
    response = test_client.post(
        "/signup", data=dict(surname="Foo", email="test@example.com", password="test1234"), follow_redirects=True
    )
    assert response.request.path == url_for("auth.show_signup_form"), "Signup was unsuccessful"
    assert b"This field is required" in response.data, response.data


def test_signup_user_unsuccessful(test_client):
    email = "test@example.com"
    response = test_client.post(
        "/signup", data=dict(name="Test", surname="Foo", email=email, password="test1234"), follow_redirects=True
    )
    assert response.request.path == url_for("auth.show_signup_form"), "Signup was unsuccessful"
    assert f"Email {email} in use".encode("utf-8") in response.data


def test_signup_user_successful(test_client):
    response = test_client.post(
        "/signup",
        data=dict(name="Foo", surname="Example", email="foo@example.com", password="foo1234"),
        follow_redirects=True,
    )
    assert response.request.path == url_for("public.index"), "Signup was unsuccessful"


def test_service_create_with_profie_success(clean_database):
    data = {"name": "Test", "surname": "Foo", "email": "service_test@example.com", "password": "test1234"}

    AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 1
    assert UserProfileRepository().count() == 1


def test_service_create_with_profile_fail_no_email(clean_database):
    data = {"name": "Test", "surname": "Foo", "email": "", "password": "1234"}

    with pytest.raises(ValueError, match="Email is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


def test_service_create_with_profile_fail_no_password(clean_database):
    data = {"name": "Test", "surname": "Foo", "email": "test@example.com", "password": ""}

    with pytest.raises(ValueError, match="Password is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


def test_service_is_email_available(clean_database):
    """
    Comprueba que is_email_available devuelve True para correos libres
    y False cuando ya existe un usuario con ese email.
    """
    service = AuthenticationService()

    # Al principio, el email no existe en la BD
    assert service.is_email_available("free@example.com") is True

    # Creamos un usuario con ese email
    service.create_with_profile(
        name="Test",
        surname="User",
        email="taken@example.com",
        password="secret1234",
    )

    assert service.is_email_available("taken@example.com") is False


def test_temp_folder_by_user_uses_uploads_folder(monkeypatch, clean_database):
    """
    Verifica que temp_folder_by_user construye correctamente la ruta
    en función de uploads_folder_name() y del id del usuario.
    """
    service = AuthenticationService()

    user = service.create_with_profile(
        name="Temp",
        surname="User",
        email="tempfolder@example.com",
        password="temp1234",
    )

    # Fijamos un valor controlado para uploads_folder_name
    fake_base = "/var/uploads"

    monkeypatch.setattr(
        "app.modules.auth.services.uploads_folder_name",
        lambda: fake_base,
        raising=False,
    )

    path = service.temp_folder_by_user(user)

    expected = os.path.join(fake_base, "temp", str(user.id))
    assert path == expected


def test_login_throttle_blocks_after_max_attempts(clean_database, test_client):
    """
    Si se supera el número máximo de intentos fallidos, el servicio
    bloquea el acceso y sigue bloqueando aunque las credenciales
    posteriores sean correctas.
    """
    # Creamos usuario de prueba
    creator_service = AuthenticationService()
    creator_service.create_with_profile(
        name="Throttle",
        surname="User",
        email="throttle@example.com",
        password="secret1234",
    )

    # Configuramos el throttle muy agresivo para el test
    tcfg = ThrottleConfig(
        max_attempts=2,
        window_seconds=60,
        lock_seconds=300,
    )
    auth_service = AuthenticationService(throttle_config=tcfg)

    ip = "198.51.100.5"

    # Primer intento fallido: aún no debe bloquear
    with test_client.application.test_request_context(
        "/login",
        method="POST",
        environ_overrides={"REMOTE_ADDR": ip},
    ):
        ok = auth_service.login("throttle@example.com", "wrongpass")
        assert ok is False
        assert auth_service.error_code == "invalid_credentials"
        assert auth_service.remaining_attempts == 1

    # Segundo intento fallido: debe activar el bloqueo
    with test_client.application.test_request_context(
        "/login",
        method="POST",
        environ_overrides={"REMOTE_ADDR": ip},
    ):
        ok = auth_service.login("throttle@example.com", "wrongpass")
        assert ok is False
        assert auth_service.error_code == "too_many_failed_attempts"
        assert auth_service.remaining_attempts == 0

    # Tercer intento con contraseña correcta: sigue bloqueado
    with test_client.application.test_request_context(
        "/login",
        method="POST",
        environ_overrides={"REMOTE_ADDR": ip},
    ):
        ok = auth_service.login("throttle@example.com", "secret1234")
        assert ok is False
        assert auth_service.error_code == "too_many_failed_attempts"
        assert auth_service.remaining_attempts == 0


def test_login_success_resets_failures(clean_database, test_client):
    """
    Tras varios intentos fallidos, un login correcto debe resetear el
    contador de fallos para ese email+IP.
    """
    # Creamos usuario
    creator_service = AuthenticationService()
    creator_service.create_with_profile(
        name="Reset",
        surname="User",
        email="reset@example.com",
        password="reset1234",
    )

    tcfg = ThrottleConfig(
        max_attempts=5,
        window_seconds=300,
        lock_seconds=600,
    )
    auth_service = AuthenticationService(throttle_config=tcfg)

    ip = "203.0.113.10"

    # Dos intentos fallidos
    with test_client.application.test_request_context(
        "/login",
        method="POST",
        environ_overrides={"REMOTE_ADDR": ip},
    ):
        assert auth_service.login("reset@example.com", "bad1") is False

    with test_client.application.test_request_context(
        "/login",
        method="POST",
        environ_overrides={"REMOTE_ADDR": ip},
    ):
        assert auth_service.login("reset@example.com", "bad2") is False

    # Verificamos que el contador interno de fallos es 2
    key = auth_service._key("reset@example.com", ip)
    rec = auth_service._fails.get(key)
    assert rec is not None
    assert rec["count"] == 2

    # Login correcto
    with test_client.application.test_request_context(
        "/login",
        method="POST",
        environ_overrides={"REMOTE_ADDR": ip},
    ):
        assert auth_service.login("reset@example.com", "reset1234") is True

    # El contador debe haberse reseteado
    rec_after = auth_service._fails.get(key)
    assert rec_after is not None
    assert rec_after["count"] == 0
    assert rec_after["locked_until"] is None


def test_throttle_is_per_email_and_ip(clean_database, test_client):
    """
    Un email bloqueado desde una IP no implica bloqueo para otra IP distinta.
    """
    service = AuthenticationService(
        throttle_config=ThrottleConfig(
            max_attempts=2,    # ahora el bloqueo se activa en el segundo fallo
            window_seconds=300,
            lock_seconds=600,
        )
    )
    email = "nope@example.com"
    ip1 = "203.0.113.1"
    ip2 = "203.0.113.2"

    # Primer intento desde ip1: aún no bloquea
    with test_client.application.test_request_context(
        "/login",
        method="POST",
        environ_overrides={"REMOTE_ADDR": ip1},
    ):
        ok = service.login(email, "x")
        assert ok is False
        assert service.error_code == "invalid_credentials"

    # Segundo intento desde ip1: ahora sí debe estar bloqueado
    with test_client.application.test_request_context(
        "/login",
        method="POST",
        environ_overrides={"REMOTE_ADDR": ip1},
    ):
        ok = service.login(email, "x")
        assert ok is False
        assert service.error_code == "too_many_failed_attempts"

    # Primer intento desde ip2: no hereda el bloqueo de ip1
    with test_client.application.test_request_context(
        "/login",
        method="POST",
        environ_overrides={"REMOTE_ADDR": ip2},
    ):
        ok = service.login(email, "x")
        assert ok is False
        # En esta IP es el primer fallo, así que vuelve a ser invalid_credentials
        assert service.error_code == "invalid_credentials"


def test_throttle_window_resets_after_window(monkeypatch, clean_database, test_client):
    """
    Si pasa la ventana de tiempo, el contador de fallos se reinicia y no se bloquea
    aunque se vuelva a fallar.
    """
    tcfg = ThrottleConfig(max_attempts=2, window_seconds=10, lock_seconds=60)
    service = AuthenticationService(throttle_config=tcfg)

    base_time = [1000.0]

    def fake_time():
        return base_time[0]

    # Parcheamos time.time dentro del módulo del servicio
    monkeypatch.setattr("app.modules.auth.services.time.time", fake_time)

    email = "nope2@example.com"
    ip = "203.0.113.50"

    # Primer intento en t=1000
    with test_client.application.test_request_context(
        "/login",
        method="POST",
        environ_overrides={"REMOTE_ADDR": ip},
    ):
        assert service.login(email, "x") is False
        assert service.error_code == "invalid_credentials"

    # Avanzamos el tiempo más allá de window_seconds
    base_time[0] = 1015.0

    # Segundo intento tras la ventana: el contador debe haberse reiniciado,
    # así que se comporta como un primer intento de nuevo.
    with test_client.application.test_request_context(
        "/login",
        method="POST",
        environ_overrides={"REMOTE_ADDR": ip},
    ):
        assert service.login(email, "x") is False
        assert service.error_code == "invalid_credentials"
        assert service.remaining_attempts == tcfg.max_attempts - 1


def test_client_ip_uses_x_forwarded_for_first_item(test_client):
    """
    _client_ip debe priorizar el primer valor de X-Forwarded-For
    sobre REMOTE_ADDR.
    """
    service = AuthenticationService()

    with test_client.application.test_request_context(
        "/login",
        method="POST",
        headers={"X-Forwarded-For": "198.51.100.42, 10.0.0.1"},
        environ_overrides={"REMOTE_ADDR": "203.0.113.99"},
    ):
        ip = service._client_ip()
        assert ip == "198.51.100.42"


def test_get_authenticated_user_and_profile(test_client, clean_database):
    """
    Comprueba que los métodos get_authenticated_* devuelven el usuario
    y perfil cuando hay sesión iniciada, y None cuando no la hay.
    """
    service = AuthenticationService()
    user = service.create_with_profile(
        name="Auth",
        surname="User",
        email="authuser@example.com",
        password="secret1234",
    )

    with test_client.application.test_request_context("/"):
        # Nos aseguramos de partir de un estado anónimo, por si algún test previo
        # dejó la sesión abierta.
        logout_user()

        # Sin login aún
        assert service.get_authenticated_user() is None
        assert service.get_authenticated_user_profile() is None

        # Hacemos login manual con flask-login
        login_user(user)

        current = service.get_authenticated_user()
        profile = service.get_authenticated_user_profile()

        assert current is not None
        assert current.id == user.id

        assert profile is not None
        assert profile.user_id == user.id

        # Cerramos sesión y comprobamos que vuelve a None
        logout_user()
        assert service.get_authenticated_user() is None
        assert service.get_authenticated_user_profile() is None


def test_login_success_clears_error_state(clean_database, test_client):
    """
    Tras un intento fallido, un login correcto debe limpiar error_code,
    error_message y remaining_attempts.
    """
    tcfg = ThrottleConfig(
        max_attempts=3,
        window_seconds=300,
        lock_seconds=600,
    )
    service = AuthenticationService(throttle_config=tcfg)

    # Creamos usuario
    service.create_with_profile(
        name="State",
        surname="User",
        email="state@example.com",
        password="goodpass123",
    )

    ip = "198.51.100.200"

    # 1) Intento fallido: se rellenan los campos de error
    with test_client.application.test_request_context(
        "/login",
        method="POST",
        environ_overrides={"REMOTE_ADDR": ip},
    ):
        ok = service.login("state@example.com", "badpass")
        assert ok is False
        assert service.error_code == "invalid_credentials"
        assert service.error_message is not None
        assert service.remaining_attempts == tcfg.max_attempts - 1

    # 2) Intento exitoso: se deben limpiar los campos de error
    with test_client.application.test_request_context(
        "/login",
        method="POST",
        environ_overrides={"REMOTE_ADDR": ip},
    ):
        ok = service.login("state@example.com", "goodpass123")
        assert ok is True
        assert service.error_code is None
        assert service.error_message is None
        assert service.remaining_attempts is None


def test_norm_ip_invalid_returns_unknown():
    """
    _norm_ip debe devolver 'unknown' cuando la IP es inválida y se lanza
    una excepción al normalizarla.
    """
    service = AuthenticationService()

    assert service._norm_ip("no-es-una-ip") == "unknown"
    assert service._norm_ip("") == "unknown"


def test_update_profile_with_valid_form(monkeypatch):
    """
    Si form.validate() devuelve True, update_profile debe llamar a update
    y devolver (instancia_actualizada, None).
    """

    # Fake de update que no toca BD
    def fake_update(self, obj_id, **data):
        return {"id": obj_id, **data}

    monkeypatch.setattr(AuthenticationService, "update", fake_update)

    class DummyForm:
        def __init__(self):
            self.data = {"name": "Nuevo", "surname": "Apellido"}
            self._valid = True
            self.errors = {}

        def validate(self):
            return self._valid

    service = AuthenticationService()
    form = DummyForm()

    updated, errors = service.update_profile(123, form)

    assert errors is None
    assert updated is not None
    assert updated["id"] == 123
    assert updated["name"] == "Nuevo"
    assert updated["surname"] == "Apellido"


def test_update_profile_with_invalid_form(monkeypatch):
    """
    Si form.validate() devuelve False, update_profile no debe llamar a update
    y debe devolver (None, form.errors).
    """

    # Fake de update que fallaría si llegara a llamarse
    def fake_update(self, obj_id, **data):
        raise AssertionError("update no debería ser llamado cuando el formulario es inválido")

    monkeypatch.setattr(AuthenticationService, "update", fake_update)

    class DummyForm:
        def __init__(self):
            self.data = {"name": "NoImporta", "surname": "Tampoco"}
            self._valid = False
            self.errors = {"name": ["error en nombre"]}

        def validate(self):
            return self._valid

    service = AuthenticationService()
    form = DummyForm()

    updated, errors = service.update_profile(456, form)

    assert updated is None
    assert errors == form.errors
