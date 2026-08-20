"""
Background SQS long-poll consumer for notification events.

USER_REGISTERED  -> welcome notification for that user
ARTICLE_PUBLISHED -> "your article was published" notification for the author

Runs in a daemon thread started on FastAPI startup so the HTTP server and
the queue consumer share one process/container (kept simple for Stage 1,
per the assignment's "do not overcomplicate" rule). A separate worker
process/container would be a reasonable production hardening step but is
not required to satisfy the assignment's scope.
"""
import json
import logging
import os
import threading
import time
import uuid

import boto3

from .database import SessionLocal
from .models import Notification

logger = logging.getLogger("sqs_consumer")

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
SQS_ENDPOINT_URL = os.getenv("SQS_ENDPOINT_URL")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
POLL_WAIT_SECONDS = int(os.getenv("SQS_POLL_WAIT_SECONDS", "10"))

_stop_event = threading.Event()


def _get_client():
    kwargs = {"region_name": AWS_REGION}
    if SQS_ENDPOINT_URL:
        kwargs["endpoint_url"] = SQS_ENDPOINT_URL
        kwargs["aws_access_key_id"] = os.getenv("AWS_ACCESS_KEY_ID", "local")
        kwargs["aws_secret_access_key"] = os.getenv("AWS_SECRET_ACCESS_KEY", "local")
    return boto3.client("sqs", **kwargs)


def _message_for(event_type: str, payload: dict):
    if event_type == "USER_REGISTERED":
        return payload.get("user_id"), f"Welcome, {payload.get('username', 'there')}!"
    if event_type == "ARTICLE_PUBLISHED":
        return payload.get("author_id"), f"Your article \"{payload.get('title', '')}\" was published."
    return None, None


def _handle_message(body: str) -> bool:
    """Process one SQS message body.

    Returns True only when the message was either successfully committed to
    the database or intentionally skipped (unknown/unmapped event type --
    retrying it would produce the same no-op forever). Returns False when
    processing or database storage actually failed, so the caller knows the
    message must NOT be deleted and should remain in the queue for retry.
    """
    try:
        data = json.loads(body)
        event_type = data.get("event_type")
        payload = data.get("payload", {})
    except (json.JSONDecodeError, AttributeError):
        logger.warning("Skipping malformed SQS message body")
        return False

    user_id, message = _message_for(event_type, payload)
    if not user_id or not message:
        logger.info("No notification mapping for event_type=%s; skipping", event_type)
        return True

    db = SessionLocal()
    try:
        db.add(
            Notification(
                user_id=uuid.UUID(user_id),
                event_type=event_type,
                message=message,
            )
        )
        db.commit()
        return True
    except Exception:
        logger.exception("Failed to store notification for event_type=%s", event_type)
        db.rollback()
        return False
    finally:
        db.close()


def _poll_loop():
    if not SQS_QUEUE_URL:
        logger.warning("SQS_QUEUE_URL not set; notification consumer thread will not start")
        return

    client = _get_client()
    logger.info("SQS consumer started, queue=%s", SQS_QUEUE_URL)
    while not _stop_event.is_set():
        try:
            resp = client.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=POLL_WAIT_SECONDS,
            )
            messages = resp.get("Messages", [])
            for msg in messages:
                success = _handle_message(msg["Body"])
                if success:
                    client.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"])
                else:
                    logger.warning(
                        "Leaving message on queue for retry (receipt=%s)", msg["ReceiptHandle"][:12]
                    )
        except Exception:
            logger.exception("SQS poll iteration failed; backing off")
            time.sleep(5)


def start_consumer_thread():
    thread = threading.Thread(target=_poll_loop, daemon=True, name="sqs-consumer")
    thread.start()
    return thread


def stop_consumer():
    _stop_event.set()
