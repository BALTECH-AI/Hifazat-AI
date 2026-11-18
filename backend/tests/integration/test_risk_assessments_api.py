
from datetime import datetime, timezone
from uuid import uuid4

import pytest


def create_incident(client, title="Risk Assessment Test Incident"):
    response = client.post(
        "/api/incidents",
        json={
            "title": title,
            "description": "Hypothetical test incident.",
            "incident_type": "landslide",
            "severity": "high",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_investigation(client, incident_id):
    response = client.post(
        f"/api/incidents/{incident_id}/investigate",
        json={},
    )
    assert response.status_code == 201
    return response.json()


def create_test_context(client, title="Risk Assessment Test Incident"):
    incident = create_incident(client, title)
    investigation = create_investigation(client, incident["id"])
    return investigation


def create_risk_payload(**overrides):
    payload = {
        "likelihood": 4,
        "impact": 5,
        "rationale": "Multiple independent sources indicate possible infrastructure damage.",
        "methodology": "Assessment based on verified evidence and reported impact.",
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(overrides)
    return payload


def post_risk_assessment(reviewer_client, investigation_id, payload=None):
    return reviewer_client.post(
        f"/api/investigations/{investigation_id}/risk-assessments",
        json=payload or create_risk_payload(),
    )


def test_create_risk_assessment(client, reviewer_client):
    investigation = create_test_context(client)

    response = post_risk_assessment(
        reviewer_client,
        investigation["id"],
    )

    assert response.status_code == 201

    data = response.json()
    assert data["investigation_id"] == investigation["id"]
    assert data["likelihood"] == 4
    assert data["impact"] == 5
    assert data["risk_score"] == 20
    assert data["risk_level"] == "critical"
    assert data["assessor_type"] == "human"
    assert data["assessor_name"] is not None
    assert data["id"] is not None
    assert data["created_at"] is not None


def test_create_risk_assessment_with_human_assessor(client, reviewer_client):
    investigation = create_test_context(client)

    response = post_risk_assessment(
        reviewer_client,
        investigation["id"],
        create_risk_payload(
            assessor_type="human",
            assessor_name="Human Reviewer",
        ),
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("likelihood", "impact", "expected_score", "expected_level"),
    [
        (1, 1, 1, "low"),
        (1, 4, 4, "low"),
        (1, 5, 5, "moderate"),
        (3, 3, 9, "moderate"),
        (2, 5, 10, "high"),
        (4, 4, 16, "high"),
        (5, 4, 20, "critical"),
        (5, 5, 25, "critical"),
    ],
)
def test_create_risk_assessment_calculates_score_and_level(
    client,
    reviewer_client,
    likelihood,
    impact,
    expected_score,
    expected_level,
):
    investigation = create_test_context(client)

    response = post_risk_assessment(
        reviewer_client,
        investigation["id"],
        create_risk_payload(
            likelihood=likelihood,
            impact=impact,
        ),
    )

    assert response.status_code == 201
    assert response.json()["risk_score"] == expected_score
    assert response.json()["risk_level"] == expected_level


@pytest.mark.parametrize("likelihood", [0, 6, -1])
def test_create_risk_assessment_rejects_invalid_likelihood(
    client,
    reviewer_client,
    likelihood,
):
    investigation = create_test_context(client)

    response = post_risk_assessment(
        reviewer_client,
        investigation["id"],
        create_risk_payload(likelihood=likelihood),
    )

    assert response.status_code == 422


@pytest.mark.parametrize("impact", [0, 6, -1])
def test_create_risk_assessment_rejects_invalid_impact(
    client,
    reviewer_client,
    impact,
):
    investigation = create_test_context(client)

    response = post_risk_assessment(
        reviewer_client,
        investigation["id"],
        create_risk_payload(impact=impact),
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field",
    ["risk_score", "risk_level"],
)
def test_create_risk_assessment_rejects_client_generated_fields(
    client,
    reviewer_client,
    field,
):
    investigation = create_test_context(client)

    response = post_risk_assessment(
        reviewer_client,
        investigation["id"],
        create_risk_payload(**{field: 20 if field == "risk_score" else "critical"}),
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field",
    ["rationale", "methodology"],
)
def test_create_risk_assessment_rejects_empty_text(
    client,
    reviewer_client,
    field,
):
    investigation = create_test_context(client)

    response = post_risk_assessment(
        reviewer_client,
        investigation["id"],
        create_risk_payload(**{field: "   "}),
    )

    assert response.status_code == 422


def test_create_risk_assessment_rejects_naive_datetime(client, reviewer_client):
    investigation = create_test_context(client)

    response = post_risk_assessment(
        reviewer_client,
        investigation["id"],
        create_risk_payload(
            assessed_at="2026-11-07T12:00:00",
        ),
    )

    assert response.status_code == 422


def test_create_risk_assessment_rejects_invalid_assessor_type(client, reviewer_client):
    investigation = create_test_context(client)

    response = post_risk_assessment(
        reviewer_client,
        investigation["id"],
        create_risk_payload(assessor_type="system"),
    )

    assert response.status_code == 422


def test_create_risk_assessment_rejects_unknown_fields(client, reviewer_client):
    investigation = create_test_context(client)

    response = post_risk_assessment(
        reviewer_client,
        investigation["id"],
        create_risk_payload(unexpected_field="not allowed"),
    )

    assert response.status_code == 422


def test_create_risk_assessment_missing_investigation(client, reviewer_client):
    response = post_risk_assessment(
        reviewer_client,
        "00000000-0000-0000-0000-000000000000",
    )

    assert response.status_code == 404


def test_list_risk_assessments_preserves_history(client, reviewer_client):
    investigation = create_test_context(client)

    older = create_risk_payload(
        likelihood=2,
        impact=2,
        assessed_at="2026-11-05T10:00:00+05:00",
    )
    newer = create_risk_payload(
        likelihood=5,
        impact=5,
        assessed_at="2026-11-06T10:00:00+05:00",
    )

    first = post_risk_assessment(
        reviewer_client,
        investigation["id"],
        older,
    )
    second = post_risk_assessment(
        reviewer_client,
        investigation["id"],
        newer,
    )

    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(
        f"/api/investigations/{investigation['id']}/risk-assessments"
    )

    assert response.status_code == 200

    assessments = response.json()
    assert len(assessments) == 2
    assert assessments[0]["id"] == second.json()["id"]
    assert assessments[1]["id"] == first.json()["id"]
    assert assessments[0]["risk_level"] == "critical"
    assert assessments[1]["risk_level"] == "low"


def test_list_risk_assessments_returns_empty_list(client, reviewer_client):
    investigation = create_test_context(client)

    response = client.get(
        f"/api/investigations/{investigation['id']}/risk-assessments"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_risk_assessments_missing_investigation(client, reviewer_client):
    response = client.get(
        f"/api/investigations/{uuid4()}/risk-assessments"
    )

    assert response.status_code == 404


def test_get_risk_assessment(client, reviewer_client):
    investigation = create_test_context(client)

    created = post_risk_assessment(
        reviewer_client,
        investigation["id"],
    )
    assert created.status_code == 201

    assessment_id = created.json()["id"]

    response = client.get(
        f"/api/risk-assessments/{assessment_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == assessment_id
    assert response.json()["investigation_id"] == investigation["id"]


def test_get_missing_risk_assessment(client, reviewer_client):
    response = client.get(
        f"/api/risk-assessments/{uuid4()}"
    )

    assert response.status_code == 404


def test_risk_assessments_api_has_no_update_or_delete_routes(client, reviewer_client):
    paths = {
        (method, route.path)
        for route in client.app.routes
        if hasattr(route, "methods")
        for method in route.methods
    }

    assessment_path = "/api/risk-assessments/{risk_assessment_id}"

    assert ("GET", assessment_path) in paths
    assert ("PUT", assessment_path) not in paths
    assert ("PATCH", assessment_path) not in paths
    assert ("DELETE", assessment_path) not in paths
