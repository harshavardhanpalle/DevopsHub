"""
Unit tests for category-service.

NOT VERIFIED IN THIS ENVIRONMENT: no network access to `pip install`, so
these have not been executed. Run with:

    cd category-service
    pip install -r requirements.txt
    DATABASE_URL=sqlite:///./test_category.db JWT_SECRET=test-secret pytest -q
"""
import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_category_service.db")
os.environ.setdefault("JWT_SECRET", "test-secret")

import jwt  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

# TestClient() without a `with` block does not run FastAPI's startup event,
# so neither the tables nor the default-category seeding that on_startup()
# performs ever happen, and DB-touching tests fail ("no such table" / no
# seeded rows). Invoke the app's actual registered startup handler(s)
# directly -- this runs the exact same code the app runs when it boots for
# real (table creation + seeding), rather than duplicating that logic here.
for _handler in app.router.on_startup:
    _handler()

client = TestClient(app)


def _auth_header() -> dict:
    token = jwt.encode({"sub": str(uuid.uuid4())}, "test-secret", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "category-service"


def test_default_categories_seeded():
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()["items"]]
    assert "Docker" in names
    assert "Terraform" in names


def test_create_category_requires_auth():
    resp = client.post("/api/categories", json={"name": "Serverless"})
    assert resp.status_code in (401, 403)


def test_create_and_filter_category():
    resp = client.post("/api/categories", json={"name": "Observability"}, headers=_auth_header())
    assert resp.status_code == 201

    filtered = client.get("/api/categories", params={"q": "Observ"})
    assert filtered.status_code == 200
    assert any(c["name"] == "Observability" for c in filtered.json()["items"])


def test_duplicate_category_rejected():
    _auth = _auth_header()
    client.post("/api/categories", json={"name": "Security"}, headers=_auth)
    dup = client.post("/api/categories", json={"name": "Security"}, headers=_auth)
    assert dup.status_code == 409
