from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.database.dependencies import get_db
from app.models import (
    Claim,
    Investigation,
    User,
    VerificationResult,
)
from app.schemas.verification_result import (
    VerificationResultCreate,
    VerificationResultResponse,
)


router = APIRouter(tags=["Verification Results"])


@router.post(
    "/api/investigations/{investigation_id}/claims/"
    "{claim_id}/verification-results",
    response_model=VerificationResultResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_verification_result(
    investigation_id: UUID,
    claim_id: UUID,
    payload: VerificationResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "REVIEWER")
    ),
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

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found in this investigation.",
        )

    result = VerificationResult(
        claim_id=claim_id,
        investigation_id=investigation_id,
        **payload.model_dump(),
        verifier_type="human",
        verifier_name=current_user.email,
    )

    db.add(result)

    try:
        db.commit()
        db.refresh(result)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Verification result could not be created.",
        )

    return result


@router.get(
    "/api/investigations/{investigation_id}/claims/"
    "{claim_id}/verification-results",
    response_model=list[VerificationResultResponse],
)
def list_claim_verification_results(
    investigation_id: UUID,
    claim_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found in this investigation.",
        )

    statement = (
        select(VerificationResult)
        .where(
            VerificationResult.claim_id == claim_id,
            VerificationResult.investigation_id == investigation_id,
        )
        .order_by(
            VerificationResult.verified_at.desc(),
            VerificationResult.created_at.desc(),
            VerificationResult.id.desc(),
        )
    )

    return db.scalars(statement).all()


@router.get(
    "/api/verification-results/{result_id}",
    response_model=VerificationResultResponse,
)
def get_verification_result(
    result_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = db.get(VerificationResult, result_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification result not found.",
        )

    return result