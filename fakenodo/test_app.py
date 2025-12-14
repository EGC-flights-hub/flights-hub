import pytest
from app import app as fakenodo_app, db


@pytest.fixture
def app():
    db.clear()
    yield fakenodo_app


@pytest.fixture
def client(app):
    return app.test_client()


def test_health_check(client):
    """Prueba que el servicio está vivo."""
    rv = client.get("/")
    assert rv.status_code == 200
    assert b"fakenodo_running" in rv.data


def test_create_record(client):
    rv = client.post("/api/deposit/depositions", json={})
    assert rv.status_code == 201
    assert rv.json["state"] == "unsubmitted"
    assert rv.json["files_changed"] == False
    assert rv.json["conceptrecid"] == "100"


def test_publish_record(client):
    rv_create = client.post("/api/deposit/depositions", json={})
    dep_id = rv_create.json["id"]

    rv_publish = client.post(f"/api/deposit/depositions/{dep_id}/actions/publish")
    assert rv_publish.status_code == 202
    assert rv_publish.json["state"] == "published"
    assert "doi" in rv_publish.json


def test_doi_versioning_logic(client):
    rv_v1 = client.post("/api/deposit/depositions", json={})
    v1_id = rv_v1.json["id"]
    v1_concept = rv_v1.json["conceptrecid"]

    rv_pub1 = client.post(f"/api/deposit/depositions/{v1_id}/actions/publish")
    doi_v1 = rv_pub1.json["doi"]

    rv_v2 = client.post("/api/deposit/depositions", json={"metadata": {"conceptrecid": v1_concept}})
    v2_id = rv_v2.json["id"]

    rv_pub2 = client.post(f"/api/deposit/depositions/{v2_id}/actions/publish")
    doi_v2 = rv_pub2.json["doi"]

    assert doi_v1 == doi_v2

    rv_v3 = client.post("/api/deposit/depositions", json={"metadata": {"conceptrecid": v1_concept}})
    v3_id = rv_v3.json["id"]

    client.post(f"/api/deposit/depositions/{v3_id}/files")

    rv_pub3 = client.post(f"/api/deposit/depositions/{v3_id}/actions/publish")
    doi_v3 = rv_pub3.json["doi"]

    assert doi_v3 != doi_v1
