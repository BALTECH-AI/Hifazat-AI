
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


IncidentType = Literal[
    "landslide",
    "flood",
    "earthquake",
    "avalanche",
    "road_blockage",
    "wildfire",
    "other",
]

IncidentSeverity = Literal[
    "low",
    "medium",
    "high",
    "critical",
]

IncidentStatus = Literal[
    "submitted",
    "investigating",
    "completed",
    "archived",
]


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    incident_type: IncidentType
    severity: IncidentSeverity = "medium"

    location_text: str | None = Field(
        default=None,
        max_length=500,
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    @model_validator(mode="after")
    def validate_coordinates(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError(
                "Latitude and longitude must be provided together."
            )
        return self


class IncidentUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        min_length=10,
    )
    incident_type: IncidentType | None = None
    severity: IncidentSeverity | None = None
    status: IncidentStatus | None = None

    location_text: str | None = Field(
        default=None,
        max_length=500,
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        latitude_provided = "latitude" in self.model_fields_set
        longitude_provided = "longitude" in self.model_fields_set

        if latitude_provided != longitude_provided:
            raise ValueError(
                "Latitude and longitude must be updated together."
            )

        if latitude_provided and (
            (self.latitude is None) != (self.longitude is None)
        ):
            raise ValueError(
                "Latitude and longitude must both be null "
                "or both be provided."
            )

        return self


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    incident_type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus
    location_text: str | None
    latitude: float | None
    longitude: float | None
    created_at: datetime
    updated_at: datetime
