from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.database.dependencies import get_db
from app.models import Incident, User
from app.schemas import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
)


router = APIRouter(
    prefix="/api/incidents",
    tags=["Incidents"],
)


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "ANALYST")
    ),
):
    incident = Incident(**payload.model_dump())

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return incident


@router.get("", response_model=list[IncidentResponse])
def list_incidents(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(Incident)
        .order_by(Incident.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(statement).all()


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
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

    return incident


@router.patch("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: UUID,
    payload: IncidentUpdate,
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

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(incident, field, value)

    db.commit()
    db.refresh(incident)

    return incident


@router.post(
    "/{incident_id}/archive",
    response_model=IncidentResponse,
)
def archive_incident(
    incident_id: UUID,
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

    incident.status = "archived"

    db.commit()
    db.refresh(incident)

    return incident