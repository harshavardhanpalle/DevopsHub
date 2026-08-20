"""
Unit tests for user-service.

NOT VERIFIED IN THIS ENVIRONMENT: this sandbox has no network access, so
`pip install -r requirements.txt` cannot run here and these tests have not
actually been executed. They are written to run under pytest + FastAPI's
TestClient against an in-memory SQLite DB (via DATABASE_URL override) once
dependencies are installed, e.g.:

    cd user-service
    pip install -r requirements.txt
    DATABASE_URL=sqlite:///./test.db pytest -q
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_user_service.db")
os.environ.setdefault("JWT_SECRET", "test-secret")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.database import Base, engine  # noqa: E402

# TestClient() without a `with` block does not run FastAPI's startup event,
# so the tables that on_startup() would normally create never get created
# and every DB-touching test fails with "no such table". Create them
# directly here (same call the app's own startup hook makes).
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def _register(email="alice@example.com", username="alice", password="supersecret1"):
    return client.post(
        "/api/auth/register",
        json={"email": email, "username": username, "password": password, "full_name": "Alice"},
    )


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "user-service"


def test_register_success():
    resp = _register()
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert body["user"]["email"] == "alice@example.com"


def test_register_duplicate_email_rejected():
    _register(email="bob@example.com", username="bob1")
    resp = _register(email="bob@example.com", username="bob2")
    assert resp.status_code == 409


def test_login_success_and_failure():
    _register(email="carol@example.com", username="carol", password="correcthorse1")
    ok = client.post(
        "/api/auth/login", json={"email": "carol@example.com", "password": "correcthorse1"}
    )
    assert ok.status_code == 200
    assert "access_token" in ok.json()

    bad = client.post(
        "/api/auth/login", json={"email": "carol@example.com", "password": "wrongpassword"}
    )
    assert bad.status_code == 401


def test_get_current_user_requires_token():
    resp = client.get("/api/users/me")
    assert resp.status_code in (401, 403)


def test_get_current_user_with_token():
    reg = _register(email="dave@example.com", username="dave", password="passw0rd123")
    token = reg.json()["access_token"]
    resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "dave@example.com"
