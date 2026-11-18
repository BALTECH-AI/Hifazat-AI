from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.database.dependencies import get_db
from app.models import Investigation, RiskAssessment, User
from app.schemas.risk_assessment import (
    RiskAssessmentCreate,
    RiskAssessmentResponse,
)
from app.services.risk_calculation import calculate_risk


router = APIRouter(tags=["Risk Assessments"])


@router.post(
    "/api/investigations/{investigation_id}/risk-assessments",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_risk_assessment(
    investigation_id: UUID,
    payload: RiskAssessmentCreate,
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

    risk_score, risk_level = calculate_risk(
        likelihood=payload.likelihood,
        impact=payload.impact,
    )

    assessment = RiskAssessment(
        investigation_id=investigation_id,
        risk_score=risk_score,
        risk_level=risk_level,
        assessor_type="human",
        assessor_name=current_user.email,
        **payload.model_dump(),
    )

    db.add(assessment)

    try:
        db.commit()
        db.refresh(assessment)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Risk assessment could not be created.",
        )

    return assessment


@router.get(
    "/api/investigations/{investigation_id}/risk-assessments",
    response_model=list[RiskAssessmentResponse],
)
def list_risk_assessments(
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
        select(RiskAssessment)
        .where(
            RiskAssessment.investigation_id == investigation_id
        )
        .order_by(
            RiskAssessment.assessed_at.desc(),
            RiskAssessment.created_at.desc(),
            RiskAssessment.id.desc(),
        )
    )

    return db.scalars(statement).all()


@router.get(
    "/api/risk-assessments/{risk_assessment_id}",
    response_model=RiskAssessmentResponse,
)
def get_risk_assessment(
    risk_assessment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assessment = db.get(RiskAssessment, risk_assessment_id)

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk assessment not found.",
        )

    return assessment