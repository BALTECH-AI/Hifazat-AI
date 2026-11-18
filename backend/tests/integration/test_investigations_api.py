from uuid import uuid4

import pytest


def valid_incident_payload():
    return {
        "title": "Hunza Landslide Test",
        "description": "Hypothetical incident for investigation API testing.",
        "incident_type": "landslide",
        "severity": "high",
        "location_text": "Hunza, Gilgit-Baltistan",
        "latitude": 36.3167,
        "longitude": 74.65,
    }


def create_incident(client):
    response = client.post(
        "/api/incidents",
        json=valid_incident_payload(),
    )
    assert response.status_code == 201
    return response.json()


def create_investigation(client, incident_id, payload=None):
    response = client.post(
        f"/api/incidents/{incident_id}/investigate",
        json=payload or {},
    )
    assert response.status_code == 201
    return response.json()


def test_create_investigation_with_default_trigger(client):
    incident = create_incident(client)

    investigation = create_investigation(
        client,
        incident["id"],
    )

    assert investigation["id"] is not None
    assert investigation["incident_id"] == incident["id"]
    assert investigation["status"] == "queued"
    assert investigation["trigger_type"] == "manual"
    assert investigation["created_at"] is not None


@pytest.mark.parametrize(
    "trigger_type",
    ["manual", "autonomous", "scheduled"],
)
def test_create_investigation_with_valid_trigger(
    client,
    trigger_type,
):
    incident = create_incident(client)

    investigation = create_investigation(
        client,
        incident["id"],
        {"trigger_type": trigger_type},
    )

    assert investigation["trigger_type"] == trigger_type


def test_create_investigation_rejects_invalid_trigger(client):
    incident = create_incident(client)

    response = client.post(
        f"/api/incidents/{incident['id']}/investigate",
        json={"trigger_type": "automatic"},
    )

    assert response.status_code == 422


def test_create_investigation_for_missing_incident(client):
    response = client.post(
        f"/api/incidents/{uuid4()}/investigate",
        json={},
    )

    assert response.status_code == 404


def test_get_investigation(client):
    incident = create_incident(client)
    created = create_investigation(client, incident["id"])

    response = client.get(
        f"/api/investigations/{created['id']}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["incident_id"] == incident["id"]


def test_get_missing_investigation(client):
    response = client.get(
        f"/api/investigations/{uuid4()}"
    )

    assert response.status_code == 404


def test_list_incident_investigations(client):
    incident = create_incident(client)

    first = create_investigation(client, incident["id"])
    second = create_investigation(
        client,
        incident["id"],
        {"trigger_type": "autonomous"},
    )

    response = client.get(
        f"/api/incidents/{incident['id']}/investigations"
    )

    assert response.status_code == 200

    investigations = response.json()

    assert len(investigations) == 2
    returned_ids = {item["id"] for item in investigations}
    assert returned_ids == {first["id"], second["id"]}


def test_list_investigations_for_missing_incident(client):
    response = client.get(
        f"/api/incidents/{uuid4()}/investigations"
    )

    assert response.status_code == 404


def test_incident_can_have_multiple_independent_investigations(client):
    incident = create_incident(client)

    first = create_investigation(client, incident["id"])
    second = create_investigation(client, incident["id"])

    assert first["id"] != second["id"]
    assert first["incident_id"] == second["incident_id"]


def test_anonymous_user_cannot_create_investigation(
    analyst_client,
    anonymous_client,
):
    incident = create_incident(analyst_client)

    response = anonymous_client.post(
        f"/api/incidents/{incident['id']}/investigate",
        json={},
    )

    assert response.status_code == 401


def test_reviewer_cannot_create_investigation(
    analyst_client,
    reviewer_client,
):
    incident = create_incident(analyst_client)

    response = reviewer_client.post(
        f"/api/incidents/{incident['id']}/investigate",
        json={},
    )

    assert response.status_code == 403


def test_analyst_can_create_investigation(
    analyst_client,
):
    incident = create_incident(analyst_client)

    response = analyst_client.post(
        f"/api/incidents/{incident['id']}/investigate",
        json={},
    )

    assert response.status_code == 201


def test_admin_can_create_investigation(
    admin_client,
    analyst_client,
):
    incident = create_incident(analyst_client)

    response = admin_client.post(
        f"/api/incidents/{incident['id']}/investigate",
        json={},
    )

    assert response.status_code == 201


@pytest.mark.parametrize(
    "role",
    ["ADMIN", "ANALYST", "REVIEWER"],
)
def test_all_authenticated_roles_can_read_investigation(
    client_factory,
    analyst_client,
    role,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )

    role_client = client_factory(role)

    response = role_client.get(
        f"/api/investigations/{investigation['id']}"
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "role",
    ["ADMIN", "ANALYST", "REVIEWER"],
)
def test_all_authenticated_roles_can_list_investigations(
    client_factory,
    analyst_client,
    role,
):
    incident = create_incident(analyst_client)
    create_investigation(analyst_client, incident["id"])

    role_client = client_factory(role)

    response = role_client.get(
        f"/api/incidents/{incident['id']}/investigations"
    )

    assert response.status_code == 200


def test_anonymous_user_cannot_read_investigation(
    analyst_client,
    anonymous_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )

    response = anonymous_client.get(
        f"/api/investigations/{investigation['id']}"
    )

    assert response.status_code == 401


def test_anonymous_user_cannot_list_investigations(
    analyst_client,
    anonymous_client,
):
    incident = create_incident(analyst_client)
    create_investigation(analyst_client, incident["id"])

    response = anonymous_client.get(
        f"/api/incidents/{incident['id']}/investigations"
    )

    assert response.status_code == 401