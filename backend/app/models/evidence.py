from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Evidence(Base):
    __tablename__ = "evidence"

    __table_args__ = (
    CheckConstraint(
        "source_type IN "
        "('government', 'news', 'weather_service', "
        "'social_media', 'ngo', 'other')",
        name="valid_source_type",
    ),
    CheckConstraint(
        "length(content_hash) = 64 "
        "AND content_hash = lower(content_hash)",
        name="valid_content_hash",
    ),
    UniqueConstraint(
    "id",
    "investigation_id",
    name="uq_evidence_id_investigation_id",
),
    Index("ix_evidence_investigation_id", "investigation_id"),
    Index("ix_evidence_content_hash", "content_hash"),
    Index("ix_evidence_source_group", "source_group"),
)

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    investigation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("investigations.id", ondelete="RESTRICT"),
        nullable=False,
    )

    source_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    source_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    source_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    source_group: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    content_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    screenshot_uri: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
