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


class Claim(Base):
    __tablename__ = "claims"

    __table_args__ = (
        CheckConstraint(
            "claim_type IN "
            "('event', 'location', 'impact', 'casualty', "
            "'infrastructure', 'weather', 'other')",
            name="valid_claim_type",
        ),
        UniqueConstraint(
            "id",
            "investigation_id",
            name="uq_claims_id_investigation_id",
        ),
        Index(
            "ix_claims_investigation_id",
            "investigation_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    investigation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "investigations.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    claim_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    claim_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="other",
        server_default="other",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )