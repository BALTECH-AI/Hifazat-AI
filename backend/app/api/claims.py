
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.database.dependencies import get_db
from app.models import Claim, ClaimEvidence, Evidence, Investigation, User
from app.schemas.claim import (
    ClaimCreate,
    ClaimEvidenceCreate,
    ClaimEvidenceResponse,
    ClaimResponse,
)

router = APIRouter(tags=["Claims"])


@router.post(
    "/api/investigations/{investigation_id}/claims",
    response_model=ClaimResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_claim(
    investigation_id: UUID,
    payload: ClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "ANALYST")),
):
    investigation = db.get(Investigation, investigation_id)

    if investigation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found.",
        )

    claim = Claim(
        investigation_id=investigation_id,
        **payload.model_dump(),
    )

    db.add(claim)
    db.commit()
    db.refresh(claim)

    return claim


@router.get(
    "/api/investigations/{investigation_id}/claims",
    response_model=list[ClaimResponse],
)
def list_investigation_claims(
    investigation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    investigation = db.get(Investigation, investigation_id)

    if investigation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found.",
        )

    statement = (
        select(Claim)
        .where(Claim.investigation_id == investigation_id)
        .order_by(Claim.created_at.desc(), Claim.id.desc())
    )

    return db.scalars(statement).all()


@router.get(
    "/api/claims/{claim_id}",
    response_model=ClaimResponse,
)
def get_claim(
    claim_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    claim = db.get(Claim, claim_id)

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found.",
        )

    return claim


@router.post(
    "/api/investigations/{investigation_id}/claims/{claim_id}/evidence",
    response_model=ClaimEvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def link_claim_evidence(
    investigation_id: UUID,
    claim_id: UUID,
    payload: ClaimEvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "ANALYST")),
):
    investigation = db.get(Investigation, investigation_id)

    if investigation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found.",
        )

    claim = db.scalar(
        select(Claim).where(
            Claim.id == claim_id,
            Claim.investigation_id == investigation_id,
        )
    )

    evidence = db.scalar(
        select(Evidence).where(
            Evidence.id == payload.evidence_id,
            Evidence.investigation_id == investigation_id,
        )
    )

    if claim is None or evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim or evidence not found in this investigation.",
        )

    existing_link = db.get(
        ClaimEvidence,
        (claim_id, payload.evidence_id),
    )

    if existing_link is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This evidence is already linked to the claim.",
        )

    link = ClaimEvidence(
        claim_id=claim_id,
        evidence_id=payload.evidence_id,
        investigation_id=investigation_id,
        relationship_type=payload.relationship_type,
    )

    db.add(link)

    try:
        db.commit()
        db.refresh(link)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Claim-evidence relationship could not be created.",
        )

    return link


@router.get(
    "/api/claims/{claim_id}/evidence",
    response_model=list[ClaimEvidenceResponse],
)
def list_claim_evidence(
    claim_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    claim = db.get(Claim, claim_id)

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found.",
        )

    statement = (
        select(ClaimEvidence)
        .where(ClaimEvidence.claim_id == claim_id)
        .order_by(ClaimEvidence.created_at.desc())
    )

    return db.scalars(statement).all()
