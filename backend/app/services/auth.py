from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


password_hasher = PasswordHash.recommended()

_DUMMY_PASSWORD_HASH = password_hasher.hash(
    "hifazat-ai-invalid-account-timing-protection"
)


def hash_password(password: str) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")

    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    if not isinstance(plain_password, str):
        return False

    if not isinstance(hashed_password, str) or not hashed_password:
        return False

    return password_hasher.verify(
        plain_password,
        hashed_password,
    )


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    user = db.scalar(
        select(User).where(User.email == email)
    )

    hash_to_verify = (
        user.password_hash if user is not None
        else _DUMMY_PASSWORD_HASH
    )

    password_valid = verify_password(
        password,
        hash_to_verify,
    )

    if user is None or not user.is_active or not password_valid:
        return None

    return user