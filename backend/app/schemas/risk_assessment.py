
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


RiskLevel = Literal[
    "low",
    "moderate",
    "high",
    "critical",
]

AssessorType = Literal["agent", "human"]



class RiskAssessmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)

    rationale: str = Field(min_length=1, max_length=20000)
    methodology: str = Field(min_length=1, max_length=10000)

    assessed_at: datetime

    @field_validator("rationale", "methodology")
    @classmethod
    def validate_nonempty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value

    @field_validator("assessed_at")
    @classmethod
    def validate_assessed_at_timezone(
        cls,
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "assessed_at must include timezone information."
            )
        return value


class RiskAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    investigation_id: UUID
    risk_level: RiskLevel
    likelihood: int
    impact: int
    risk_score: int
    rationale: str
    methodology: str
    assessor_type: AssessorType
    assessor_name: str | None
    assessed_at: datetime
    created_at: datetime
