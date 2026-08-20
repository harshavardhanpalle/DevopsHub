"""
Thin SQS publisher shared by services that emit notification events.

Local development: point SQS_ENDPOINT_URL at the local SQS-compatible
component (ElasticMQ, see docker-compose.yml) so no AWS credentials are
needed to run the full app locally.

Production: leave SQS_ENDPOINT_URL unset so boto3 talks to real Amazon SQS
in AWS_REGION, using IAM role credentials (never hardcoded keys).

Publishing is best-effort: a notification-queue outage must not block the
primary HTTP request (e.g. registering a user) from succeeding, so failures
are logged, not raised.
"""
import json
import logging
import os

import boto3

logger = logging.getLogger("events")

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
SQS_ENDPOINT_URL = os.getenv("SQS_ENDPOINT_URL")  # e.g. http://local-sqs:9324
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")  # queue URL, local or AWS

_client = None


def _get_client():
    global _client
    if _client is None:
        kwargs = {"region_name": AWS_REGION}
        if SQS_ENDPOINT_URL:
            kwargs["endpoint_url"] = SQS_ENDPOINT_URL
            # Local ElasticMQ does not validate real credentials.
            kwargs["aws_access_key_id"] = os.getenv("AWS_ACCESS_KEY_ID", "local")
            kwargs["aws_secret_access_key"] = os.getenv("AWS_SECRET_ACCESS_KEY", "local")
        _client = boto3.client("sqs", **kwargs)
    return _client


def publish_event(event_type: str, payload: dict) -> bool:
    if not SQS_QUEUE_URL:
        logger.warning("SQS_QUEUE_URL not configured; skipping event %s", event_type)
        return False
    message = {"event_type": event_type, "payload": payload}
    try:
        _get_client().send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(message, default=str),
        )
        return True
    except Exception:  # noqa: BLE001 -- publishing must never break the caller
        logger.exception("Failed to publish event %s to SQS", event_type)
        return False
