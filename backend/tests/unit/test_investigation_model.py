
import pytest
from datetime import datetime
from uuid import UUID

from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.models import Incident, Investigation


def create_test_incident(db_session):
    incident = Incident(
        title="Test landslide",
        description="Test incident for Investigation model.",
        incident_type="landslide",
    )

    db_session.add(incident)
    db_session.flush()

    return incident


def test_investigation_generates_uuid_and_defaults(db_session):
    incident = create_test_incident(db_session)

    investigation = Investigation(
        incident_id=incident.id,
    )

    db_session.add(investigation)
    db_session.flush()

    assert isinstance(investigation.id, UUID)
    assert investigation.status == "queued"
    assert investigation.trigger_type == "manual"


def test_multiple_investigations_can_belong_to_one_incident(db_session):
    incident = create_test_incident(db_session)

    first = Investigation(incident_id=incident.id)
    second = Investigation(
        incident_id=incident.id,
        trigger_type="autonomous",
    )

    db_session.add_all([first, second])
    db_session.flush()

    assert first.id != second.id
    assert first.incident_id == second.incident_id
    assert db_session.query(Investigation).count() == 2


@pytest.mark.parametrize(
    "invalid_status",
    ["invalid", "pending", "unknown"],
)
def test_invalid_investigation_status_is_rejected(
    db_session,
    invalid_status,
):
    incident = create_test_incident(db_session)

    investigation = Investigation(
        incident_id=incident.id,
        status=invalid_status,
    )

    db_session.add(investigation)

    with pytest.raises(IntegrityError):
        db_session.flush()

    db_session.rollback()


@pytest.mark.parametrize(
    "invalid_trigger",
    ["invalid", "automatic", "unknown"],
)
def test_invalid_trigger_type_is_rejected(
    db_session,
    invalid_trigger,
):
    incident = create_test_incident(db_session)

    investigation = Investigation(
        incident_id=incident.id,
        trigger_type=invalid_trigger,
    )

    db_session.add(investigation)

    with pytest.raises(IntegrityError):
        db_session.flush()

    db_session.rollback()


def test_investigation_foreign_key_definition():
    foreign_keys = list(Investigation.__table__.foreign_keys)

    assert len(foreign_keys) == 1

    foreign_key = foreign_keys[0]

    assert foreign_key.parent.name == "incident_id"
    assert foreign_key.target_fullname == "incidents.id"
    assert foreign_key.ondelete == "RESTRICT"


def test_investigation_indexes_exist():
    indexes = inspect(Investigation).local_table.indexes

    index_names = {index.name for index in indexes}

    assert "ix_investigations_incident_id" in index_names
    assert "ix_investigations_status" in index_names


def test_investigation_timestamps_and_optional_fields(db_session):
    incident = create_test_incident(db_session)

    investigation = Investigation(
        incident_id=incident.id,
    )

    db_session.add(investigation)
    db_session.flush()

    assert isinstance(investigation.created_at, datetime)
    assert isinstance(investigation.updated_at, datetime)

    assert investigation.started_at is None
    assert investigation.completed_at is None
    assert investigation.error_message is None
