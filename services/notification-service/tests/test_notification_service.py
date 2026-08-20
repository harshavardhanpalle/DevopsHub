"""
Unit tests for notification-service.

NOT VERIFIED IN THIS ENVIRONMENT: no network access to `pip install`, so
these have not been executed. Run with:

    cd notification-service
    pip install -r requirements.txt
    DATABASE_URL=sqlite:///./test_notif.db JWT_SECRET=test-secret pytest -q

Note: SQS_QUEUE_URL is intentionally left unset for these tests, so the
background consumer thread exits immediately (see sqs_consumer._poll_loop)
and message handling is tested directly against _handle_message instead of
through a real/local SQS queue.
"""
import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_notification_service.db")
os.environ.setdefault("JWT_SECRET", "test-secret")

import jwt  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.database import Base, engine, SessionLocal  # noqa: E402
from app import sqs_consumer  # noqa: E402

# TestClient() without a `with` block does not run FastAPI's startup event,
# so the tables that on_startup() would normally create never get created
# and every DB-touching test fails with "no such table". Create them
# directly here (same call the app's own startup hook makes).
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def _auth_header(user_id: str) -> dict:
    token = jwt.encode({"sub": user_id}, "test-secret", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "notification-service"


def test_list_requires_auth():
    resp = client.get("/api/notifications")
    assert resp.status_code in (401, 403)


def test_sqs_message_handling_creates_notification():
    import json

    user_id = str(uuid.uuid4())
    body = json.dumps(
        {"event_type": "USER_REGISTERED", "payload": {"user_id": user_id, "username": "eve"}}
    )
    sqs_consumer._handle_message(body)

    resp = client.get("/api/notifications", headers=_auth_header(user_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["unread_count"] == 1
    assert "Welcome" in body["items"][0]["message"]


def test_mark_as_read():
    import json

    user_id = str(uuid.uuid4())
    sqs_consumer._handle_message(
        json.dumps(
            {
                "event_type": "ARTICLE_PUBLISHED",
                "payload": {"author_id": user_id, "title": "My Post"},
            }
        )
    )
    listing = client.get("/api/notifications", headers=_auth_header(user_id)).json()
    notif_id = listing["items"][0]["id"]

    marked = client.post(f"/api/notifications/{notif_id}/read", headers=_auth_header(user_id))
    assert marked.status_code == 200
    assert marked.json()["is_read"] is True

    listing_after = client.get("/api/notifications", headers=_auth_header(user_id)).json()
    assert listing_after["unread_count"] == 0


def test_malformed_message_is_skipped_gracefully():
    # Should not raise
    sqs_consumer._handle_message("not valid json")
