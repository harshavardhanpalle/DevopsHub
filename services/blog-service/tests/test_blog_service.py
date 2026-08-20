"""
Unit tests for blog-service.

NOT VERIFIED IN THIS ENVIRONMENT: no network access to `pip install`, so
these have not been executed. Run with:

    cd blog-service
    pip install -r requirements.txt
    DATABASE_URL=sqlite:///./test_blog.db JWT_SECRET=test-secret pytest -q
"""
import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_blog_service.db")
os.environ.setdefault("JWT_SECRET", "test-secret")

import jwt  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.database import Base, engine  # noqa: E402

# TestClient() without a `with` block does not run FastAPI's startup event,
# so the tables that on_startup() would normally create never get created
# and every DB-touching test fails with "no such table". Create them
# directly here (same call the app's own startup hook makes).
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def _auth_header(user_id: str = None) -> dict:
    user_id = user_id or str(uuid.uuid4())
    token = jwt.encode({"sub": user_id}, "test-secret", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "blog-service"


def test_create_requires_auth():
    resp = client.post("/api/articles", json={"title": "No auth", "content": "body"})
    assert resp.status_code in (401, 403)


def test_create_and_get_article():
    headers = _auth_header()
    create = client.post(
        "/api/articles",
        json={"title": "Terraform Basics", "summary": "Intro", "content": "Full body text"},
        headers=headers,
    )
    assert create.status_code == 201
    article = create.json()
    assert article["title"] == "Terraform Basics"
    assert article["slug"].startswith("terraform-basics")

    fetched = client.get(f"/api/articles/{article['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Terraform Basics"


def test_list_search_and_pagination():
    headers = _auth_header()
    for title in ["Docker Networking Deep Dive", "Docker Volumes Explained", "AWS IAM Basics"]:
        client.post("/api/articles", json={"title": title, "content": "x"}, headers=headers)

    resp = client.get("/api/articles", params={"q": "Docker", "page": 1, "page_size": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 2
    assert len(body["items"]) == 1


def test_update_forbidden_for_non_author():
    # Note: these must contain at least one non-digit hex character. An
    # all-numeric-looking UUID string (e.g. "11111111-1111-1111-1111-...")
    # gets coerced to a float by SQLite's numeric type affinity when passed
    # through the Postgres-specific UUID column type under this test's
    # SQLite backend -- a SQLite-only test artifact, not a real Postgres
    # issue (production always runs against real PostgreSQL per the
    # connection strings in docker-compose.yml).
    owner_headers = _auth_header("11111111-aaaa-1111-1111-111111111111")
    create = client.post(
        "/api/articles", json={"title": "Owned Article", "content": "x"}, headers=owner_headers
    )
    article_id = create.json()["id"]

    other_headers = _auth_header("22222222-bbbb-2222-2222-222222222222")
    resp = client.put(
        f"/api/articles/{article_id}", json={"title": "Hijacked"}, headers=other_headers
    )
    assert resp.status_code == 403
