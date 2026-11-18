from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


VerificationStatus = Literal[
    "verified",
    "partially_verified",
    "unverified",
    "contradicted",
    "outdated",
]

VerifierType = Literal["agent", "human"]


class VerificationResultCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: VerificationStatus

    rationale: str = Field(
        min_length=1,
        max_length=20000,
    )

    methodology: str = Field(
        min_length=1,
        max_length=10000,
    )

    confidence_score: Decimal | None = Field(
        default=None,
        ge=0,
        le=1,
        max_digits=5,
        decimal_places=4,
    )

    verified_at: datetime

    @field_validator("rationale", "methodology")
    @classmethod
    def validate_nonempty_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty.")

        return value

    @field_validator("verified_at")
    @classmethod
    def validate_verified_at_timezone(
        cls,
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "verified_at must include timezone information."
            )

        return value


class VerificationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_id: UUID
    investigation_id: UUID
    status: VerificationStatus
    rationale: str
    methodology: str
    confidence_score: Decimal | None
    verifier_type: VerifierType
    verifier_name: str | None
    verified_at: datetime
    created_at: datetime