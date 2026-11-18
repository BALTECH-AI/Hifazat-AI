from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


InvestigationStatus = Literal[
    "queued",
    "running",
    "completed",
    "failed",
    "cancelled",
]

InvestigationTriggerType = Literal[
    "manual",
    "autonomous",
    "scheduled",
]


class InvestigationCreate(BaseModel):
    trigger_type: InvestigationTriggerType = Field(
        default="manual"
    )


class InvestigationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_id: UUID
    status: InvestigationStatus
    trigger_type: InvestigationTriggerType
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
