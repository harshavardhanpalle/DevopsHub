"""
blog-service does not issue tokens -- only verifies them. The JWT secret
must be the same value configured for user-service (shared via the
JWT_SECRET environment variable in docker-compose.yml / .env). This is the
simplest workable approach for Stage 1; a dedicated introspection call to
user-service would be an alternative but adds a hard runtime dependency
between services for every write request.
"""
import os
import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-change-me")
JWT_ALGORITHM = "HS256"


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
