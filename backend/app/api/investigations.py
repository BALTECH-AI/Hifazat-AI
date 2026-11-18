from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.database.dependencies import get_db
from app.models import Incident, Investigation, User
from app.schemas.investigation import (
    InvestigationCreate,
    InvestigationResponse,
)


router = APIRouter(tags=["Investigations"])


@router.post(
    "/api/incidents/{incident_id}/investigate",
    response_model=InvestigationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_investigation(
    incident_id: UUID,
    payload: InvestigationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "ANALYST")
    ),
):
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    investigation = Investigation(
        incident_id=incident_id,
        trigger_type=payload.trigger_type,
    )

    db.add(investigation)
    db.commit()
    db.refresh(investigation)

    return investigation


@router.get(
    "/api/investigations/{investigation_id}",
    response_model=InvestigationResponse,
)
def get_investigation(
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

    return investigation


@router.get(
    "/api/incidents/{incident_id}/investigations",
    response_model=list[InvestigationResponse],
)
def list_incident_investigations(
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    statement = (
        select(Investigation)
        .where(Investigation.incident_id == incident_id)
        .order_by(
            Investigation.created_at.desc(),
            Investigation.id.desc(),
        )
    )

    return db.scalars(statement).all()