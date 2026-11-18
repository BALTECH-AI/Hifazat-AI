from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ClaimEvidence(Base):
    __tablename__ = "claim_evidence"

    __table_args__ = (
        ForeignKeyConstraint(
            ["claim_id", "investigation_id"],
            ["claims.id", "claims.investigation_id"],
            name="fk_claim_evidence_claim_investigation",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["evidence_id", "investigation_id"],
            ["evidence.id", "evidence.investigation_id"],
            name="fk_claim_evidence_evidence_investigation",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "relationship_type IN "
            "('supports', 'contradicts', 'mentions', 'context')",
            name="valid_relationship_type",
        ),
        Index(
            "ix_claim_evidence_investigation_id",
            "investigation_id",
        ),
        Index(
            "ix_claim_evidence_evidence_id",
            "evidence_id",
        ),
    )

    claim_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )

    evidence_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )

    investigation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )

    relationship_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )