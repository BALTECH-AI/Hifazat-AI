from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.dependencies import get_db
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import authenticate_user
from app.services.jwt import create_access_token


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        str(payload.email),
        payload.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user
