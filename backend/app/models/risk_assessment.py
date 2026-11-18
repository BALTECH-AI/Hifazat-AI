
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    __table_args__ = (
        CheckConstraint(
            "risk_level IN ('low', 'moderate', 'high', 'critical')",
            name="valid_risk_level",
        ),
        CheckConstraint(
            "likelihood BETWEEN 1 AND 5",
            name="valid_likelihood",
        ),
        CheckConstraint(
            "impact BETWEEN 1 AND 5",
            name="valid_impact",
        ),
        CheckConstraint(
            "risk_score = likelihood * impact",
            name="consistent_risk_score",
        ),
        CheckConstraint(
            "(risk_score BETWEEN 1 AND 4 AND risk_level = 'low') OR "
            "(risk_score BETWEEN 5 AND 9 AND risk_level = 'moderate') OR "
            "(risk_score BETWEEN 10 AND 16 AND risk_level = 'high') OR "
            "(risk_score BETWEEN 17 AND 25 AND risk_level = 'critical')",
            name="consistent_risk_level",
        ),
        CheckConstraint(
            "assessor_type IN ('agent', 'human')",
            name="valid_assessor_type",
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
            "ix_risk_assessments_investigation_assessed_at",
            "investigation_id",
            "assessed_at",
        ),
        Index(
            "ix_risk_assessments_risk_level",
            "risk_level",
        ),
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

    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    likelihood: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    impact: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    risk_score: Mapped[int] = mapped_column(
        Integer,
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

    assessor_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    assessor_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
