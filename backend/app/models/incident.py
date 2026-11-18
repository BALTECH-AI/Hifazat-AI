from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    __table_args__ = (
        CheckConstraint(
            "incident_type IN "
            "('landslide', 'flood', 'earthquake', "
            "'avalanche', 'road_blockage', 'wildfire', 'other')",
            name="valid_incident_type",
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="valid_severity",
        ),
        CheckConstraint(
            "status IN "
            "('submitted', 'investigating', 'completed', 'archived')",
            name="valid_status",
        ),
        CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR "
            "(latitude IS NOT NULL AND longitude IS NOT NULL)",
            name="coordinates_pair",
        ),
        CheckConstraint(
            "latitude IS NULL OR latitude BETWEEN -90 AND 90",
            name="valid_latitude",
        ),
        CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180",
            name="valid_longitude",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    incident_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
        server_default="medium",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="submitted",
        server_default="submitted",
    )

    location_text: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )