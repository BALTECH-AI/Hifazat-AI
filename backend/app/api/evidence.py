
import hashlib
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.database.dependencies import get_db
from app.models import Evidence, Investigation, User
from app.schemas.evidence import EvidenceCreate, EvidenceResponse

router = APIRouter(tags=["Evidence"])


@router.post(
    "/api/investigations/{investigation_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_evidence(
    investigation_id: UUID,
    payload: EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "ANALYST")),
):
    investigation = db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    content_hash = hashlib.sha256(
        payload.content_text.encode("utf-8")
    ).hexdigest()

    evidence = Evidence(
        investigation_id=investigation_id,
        content_hash=content_hash,
        **payload.model_dump(),
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return evidence


@router.get(
    "/api/investigations/{investigation_id}/evidence",
    response_model=list[EvidenceResponse],
)
def list_investigation_evidence(
    investigation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    investigation = db.get(Investigation, investigation_id)

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    statement = (
        select(Evidence)
        .where(Evidence.investigation_id == investigation_id)
        .order_by(
            Evidence.collected_at.desc(),
            Evidence.id.desc(),
        )
    )

    return db.scalars(statement).all()


@router.get(
    "/api/evidence/{evidence_id}",
    response_model=EvidenceResponse,
)
def get_evidence(
    evidence_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evidence = db.get(Evidence, evidence_id)

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found.",
        )

    return evidence
