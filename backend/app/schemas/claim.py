from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


ClaimType = Literal[
    "event",
    "location",
    "impact",
    "casualty",
    "infrastructure",
    "weather",
    "other",
]

ClaimEvidenceRelationship = Literal[
    "supports",
    "contradicts",
    "mentions",
    "context",
]


class ClaimCreate(BaseModel):
    claim_text: str = Field(
        min_length=5,
        max_length=10000,
    )

    claim_type: ClaimType = "other"

    @field_validator("claim_text")
    @classmethod
    def validate_claim_text(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 5:
            raise ValueError(
                "Claim text must contain at least 5 non-whitespace characters."
            )

        return value


class ClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    investigation_id: UUID
    claim_text: str
    claim_type: ClaimType
    created_at: datetime


class ClaimEvidenceCreate(BaseModel):
    evidence_id: UUID

    relationship_type: ClaimEvidenceRelationship


class ClaimEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    claim_id: UUID
    evidence_id: UUID
    investigation_id: UUID
    relationship_type: ClaimEvidenceRelationship
    created_at: datetime