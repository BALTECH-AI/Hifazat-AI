from datetime import datetime, timezone
from uuid import uuid4

import pytest


def create_investigation(client):
    incident_response = client.post(
        "/api/incidents",
        json={
            "title": "Risk RBAC Test Incident",
            "description": "Hypothetical test incident.",
            "incident_type": "landslide",
            "severity": "high",
        },
    )
    assert incident_response.status_code == 201

    investigation_response = client.post(
        f"/api/incidents/{incident_response.json()['id']}/investigate",
        json={},
    )
    assert investigation_response.status_code == 201
    return investigation_response.json()


def risk_payload(**overrides):
    payload = {
        "likelihood": 4,
        "impact": 5,
        "rationale": "Assessment based on multiple independent evidence sources.",
        "methodology": "Human review of available evidence and reported impact.",
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(overrides)
    return payload


def submit_assessment(client, investigation_id, payload=None):
    return client.post(
        f"/api/investigations/{investigation_id}/risk-assessments",
        json=payload or risk_payload(),
    )


def test_anonymous_user_cannot_submit_risk_assessment(
    anonymous_client,
    analyst_client,
):
    investigation = create_investigation(analyst_client)

    response = submit_assessment(
        anonymous_client,
        investigation["id"],
    )

    assert response.status_code == 401


def test_analyst_cannot_submit_risk_assessment(analyst_client):
    investigation = create_investigation(analyst_client)

    response = submit_assessment(
        analyst_client,
        investigation["id"],
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    ("role", "email"),
    [
        ("ADMIN", "risk-admin@example.com"),
        ("REVIEWER", "risk-reviewer@example.com"),
    ],
)
def test_admin_and_reviewer_can_submit_human_assessment(
    role,
    email,
    analyst_client,
    client_factory,
):
    writer = client_factory(role, email=email)
    investigation = create_investigation(analyst_client)

    response = submit_assessment(
        writer,
        investigation["id"],
    )

    print("STATUS:", response.status_code)
    print("RESPONSE:", response.json())
    assert response.status_code == 201
    data = response.json()
    assert data["assessor_type"] == "human"
    assert data["assessor_name"] == email


@pytest.mark.parametrize(
    "field",
    ["assessor_type", "assessor_name"],
)
def test_client_cannot_spoof_assessor_attribution(
    reviewer_client,
    analyst_client,
    field,
):
    investigation = create_investigation(analyst_client)
    spoofed_value = "agent" if field == "assessor_type" else "Forged Identity"

    response = submit_assessment(
        reviewer_client,
        investigation["id"],
        risk_payload(**{field: spoofed_value}),
    )

    assert response.status_code == 422


def test_all_authenticated_roles_can_read_risk_assessments(
    analyst_client,
    reviewer_client,
    admin_client,
):
    investigation = create_investigation(analyst_client)

    created = submit_assessment(
        reviewer_client,
        investigation["id"],
    )
    assert created.status_code == 201

    assessment_id = created.json()["id"]
    investigation_id = investigation["id"]

    for authenticated_client in (
        analyst_client,
        reviewer_client,
        admin_client,
    ):
        history_response = authenticated_client.get(
            f"/api/investigations/{investigation_id}/risk-assessments"
        )
        detail_response = authenticated_client.get(
            f"/api/risk-assessments/{assessment_id}"
        )

        assert history_response.status_code == 200
        assert detail_response.status_code == 200


def test_anonymous_user_cannot_read_risk_assessment_history(
    anonymous_client,
    analyst_client,
):
    investigation = create_investigation(analyst_client)

    response = anonymous_client.get(
        f"/api/investigations/{investigation['id']}/risk-assessments"
    )

    assert response.status_code == 401


def test_anonymous_user_cannot_read_risk_assessment_detail(
    anonymous_client,
):
    response = anonymous_client.get(
        f"/api/risk-assessments/{uuid4()}"
    )

    assert response.status_code == 401
