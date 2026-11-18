from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


UserRole = Literal["ADMIN", "ANALYST", "REVIEWER"]


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"