from collections.abc import Callable
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.models import User
from app.services.jwt import decode_access_token


bearer_scheme = HTTPBearer(auto_error=False)

VALID_ROLES = {"ADMIN", "ANALYST", "REVIEWER"}


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required or token is invalid.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise authentication_error()

    if credentials.scheme.lower() != "bearer":
        raise authentication_error()

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError, TypeError):
        raise authentication_error()

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        raise authentication_error()

    if user.role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role is invalid.",
        )

    return user


def require_roles(*allowed_roles: str) -> Callable:
    if not allowed_roles:
        raise ValueError("At least one allowed role is required.")

    if any(role not in VALID_ROLES for role in allowed_roles):
        raise ValueError("One or more roles are invalid.")

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return current_user

    return role_checker
