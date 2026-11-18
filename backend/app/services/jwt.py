from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt

from app.core.config import settings


def create_access_token(user_id: UUID) -> str:
    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithms=[settings.JWT_ALGORITHM],
        options={
            "require": ["sub", "iat", "exp"],
        },
    )

    subject = payload.get("sub")

    if not isinstance(subject, str):
        raise jwt.InvalidTokenError("Invalid token subject.")

    try:
        UUID(subject)
    except (ValueError, TypeError, AttributeError) as exc:
        raise jwt.InvalidTokenError(
            "Token subject must be a valid UUID."
        ) from exc

    return payload
