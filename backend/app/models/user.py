from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "role IN ('ADMIN', 'ANALYST', 'REVIEWER')",
            name="valid_role",
        ),
        CheckConstraint(
            "email = lower(email)",
            name="email_lowercase",
        ),
        CheckConstraint(
            "length(email) BETWEEN 3 AND 320",
            name="valid_email_length",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ANALYST",
        server_default="ANALYST",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
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
