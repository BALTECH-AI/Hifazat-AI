from datetime import datetime
from typing import Literal
from uuid import UUID
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict, Field, field_validator


EvidenceSourceType = Literal[
    "government",
    "news",
    "weather_service",
    "social_media",
    "ngo",
    "other",
]


class EvidenceCreate(BaseModel):
    source_name: str = Field(min_length=2, max_length=200)
    source_type: EvidenceSourceType
    source_url: str = Field(min_length=8, max_length=2048)
    source_group: str | None = Field(default=None, max_length=200)
    title: str = Field(min_length=3, max_length=500)
    content_text: str = Field(min_length=1)
    published_at: datetime | None = None
    screenshot_uri: str | None = Field(default=None, max_length=2048)

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str) -> str:
        try:
            parsed = urlsplit(value)
            valid = (
                parsed.scheme in ("http", "https")
                and bool(parsed.hostname)
                and parsed.username is None
                and parsed.password is None
                and not any(char.isspace() for char in value)
            )
            if parsed.port is not None:
                valid = valid and 1 <= parsed.port <= 65535
        except ValueError:
            valid = False

        if not valid:
            raise ValueError("A valid HTTP or HTTPS source URL is required.")

        return value

    @field_validator("screenshot_uri")
    @classmethod
    def validate_screenshot_uri(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        try:
            parsed = urlsplit(value)
            valid = (
                parsed.scheme == "https"
                and bool(parsed.hostname)
                and parsed.username is None
                and parsed.password is None
                and not any(char.isspace() for char in value)
            )
            if parsed.port is not None:
                valid = valid and 1 <= parsed.port <= 65535
        except ValueError:
            valid = False

        if not valid:
            raise ValueError("Screenshot URI must be a valid HTTPS URL.")

        return value

class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    investigation_id: UUID
    source_name: str
    source_type: EvidenceSourceType
    source_url: str
    source_group: str | None
    title: str
    content_text: str
    content_hash: str
    published_at: datetime | None
    collected_at: datetime
    screenshot_uri: str | None
    created_at: datetime
