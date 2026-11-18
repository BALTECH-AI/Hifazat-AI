
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Investigation(Base):
    __tablename__ = "investigations"

    __table_args__ = (
        CheckConstraint(
            "status IN "
            "('queued', 'running', 'completed', 'failed', 'cancelled')",
            name="valid_status",
        ),
        CheckConstraint(
            "trigger_type IN ('manual', 'autonomous', 'scheduled')",
            name="valid_trigger_type",
        ),
        Index("ix_investigations_incident_id", "incident_id"),
        Index("ix_investigations_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    incident_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("incidents.id", ondelete="RESTRICT"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="queued",
        server_default="queued",
    )

    trigger_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="manual",
        server_default="manual",
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
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
