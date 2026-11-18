
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class VerificationResult(Base):
    __tablename__ = "verification_results"

    __table_args__ = (
        ForeignKeyConstraint(
            ["claim_id", "investigation_id"],
            ["claims.id", "claims.investigation_id"],
            name="fk_verification_results_claim_investigation",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "status IN "
            "('verified', 'partially_verified', 'unverified', "
            "'contradicted', 'outdated')",
            name="valid_status",
        ),
        CheckConstraint(
            "confidence_score IS NULL OR "
            "(confidence_score >= 0 AND confidence_score <= 1)",
            name="valid_confidence_score",
        ),
        CheckConstraint(
            "verifier_type IN ('agent', 'human')",
            name="valid_verifier_type",
        ),
        CheckConstraint(
            "length(trim(rationale)) > 0",
            name="nonempty_rationale",
        ),
        CheckConstraint(
            "length(trim(methodology)) > 0",
            name="nonempty_methodology",
        ),
        Index(
            "ix_verification_results_claim_id",
            "claim_id",
        ),
        Index(
            "ix_verification_results_investigation_id",
            "investigation_id",
        ),
        Index(
            "ix_verification_results_status",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    claim_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )

    investigation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    rationale: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    methodology: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    confidence_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    verifier_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    verifier_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
