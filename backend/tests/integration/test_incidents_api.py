from uuid import uuid4

import pytest


def valid_incident_payload():
    return {
        "title": "Hunza Landslide Test",
        "description": (
            "Hypothetical landslide incident "
            "for automated API testing."
        ),
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


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_incident(client):
    response = client.post(
        "/api/incidents",
        json=valid_incident_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Hunza Landslide Test"
    assert data["incident_type"] == "landslide"
    assert data["severity"] == "high"
    assert data["status"] == "submitted"
    assert data["id"] is not None
    assert data["created_at"] is not None


def test_list_incidents(client):
    created = create_incident(client)

    response = client.get("/api/incidents")

    assert response.status_code == 200

    incidents = response.json()

    assert len(incidents) == 1
    assert incidents[0]["id"] == created["id"]


def test_list_incidents_pagination(client):
    create_incident(client)
    create_incident(client)

    response = client.get(
        "/api/incidents",
        params={"offset": 0, "limit": 1},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_incident(client):
    created = create_incident(client)

    response = client.get(
        f"/api/incidents/{created['id']}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_update_incident(client):
    created = create_incident(client)

    response = client.patch(
        f"/api/incidents/{created['id']}",
        json={
            "title": "Updated Hunza Landslide",
            "severity": "critical",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated Hunza Landslide"
    assert data["severity"] == "critical"


def test_archive_incident(client):
    created = create_incident(client)

    response = client.post(
        f"/api/incidents/{created['id']}/archive"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "archived"


def test_invalid_incident_type(client):
    payload = valid_incident_payload()
    payload["incident_type"] = "unknown_disaster"

    response = client.post(
        "/api/incidents",
        json=payload,
    )

    assert response.status_code == 422


def test_create_incident_with_partial_coordinates(client):
    payload = valid_incident_payload()
    payload.pop("longitude")

    response = client.post(
        "/api/incidents",
        json=payload,
    )

    assert response.status_code == 422


def test_empty_incident_update(client):
    created = create_incident(client)

    response = client.patch(
        f"/api/incidents/{created['id']}",
        json={},
    )

    assert response.status_code == 422


def test_update_with_partial_coordinates(client):
    created = create_incident(client)

    response = client.patch(
        f"/api/incidents/{created['id']}",
        json={"latitude": 35.5},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", ""),
        ("patch", ""),
        ("post", "/archive"),
    ],
)
def test_incident_not_found(client, method, path):
    missing_id = uuid4()
    url = f"/api/incidents/{missing_id}{path}"

    if method == "get":
        response = client.get(url)

    elif method == "patch":
        response = client.patch(
            url,
            json={"title": "Updated title"},
        )

    else:
        response = client.post(url)

    assert response.status_code == 404


def test_create_incident_requires_authentication(
    anonymous_client,
):
    response = anonymous_client.post(
        "/api/incidents",
        json=valid_incident_payload(),
    )

    assert response.status_code == 401


def test_reviewer_cannot_create_incident(
    reviewer_client,
):
    response = reviewer_client.post(
        "/api/incidents",
        json=valid_incident_payload(),
    )

    assert response.status_code == 403


def test_analyst_can_create_incident(
    analyst_client,
):
    response = analyst_client.post(
        "/api/incidents",
        json=valid_incident_payload(),
    )

    assert response.status_code == 201


def test_admin_can_create_incident(
    admin_client,
):
    response = admin_client.post(
        "/api/incidents",
        json=valid_incident_payload(),
    )

    assert response.status_code == 201


def test_anonymous_user_cannot_update_incident(
    client,
    anonymous_client,
):
    created = client.post(
        "/api/incidents",
        json=valid_incident_payload(),
    )
    incident_id = created.json()["id"]

    response = anonymous_client.patch(
        f"/api/incidents/{incident_id}",
        json={"title": "Unauthorized Update"},
    )

    assert response.status_code == 401


def test_reviewer_cannot_update_incident(
    analyst_client,
    reviewer_client,
):
    created = analyst_client.post(
        "/api/incidents",
        json=valid_incident_payload(),
    )
    incident_id = created.json()["id"]

    response = reviewer_client.patch(
        f"/api/incidents/{incident_id}",
        json={"title": "Unauthorized Update"},
    )

    assert response.status_code == 403


def test_anonymous_user_cannot_archive_incident(
    client,
    anonymous_client,
):
    created = client.post(
        "/api/incidents",
        json=valid_incident_payload(),
    )
    incident_id = created.json()["id"]

    response = anonymous_client.post(
        f"/api/incidents/{incident_id}/archive",
    )

    assert response.status_code == 401


def test_reviewer_cannot_archive_incident(
    analyst_client,
    reviewer_client,
):
    created = analyst_client.post(
        "/api/incidents",
        json=valid_incident_payload(),
    )
    incident_id = created.json()["id"]

    response = reviewer_client.post(
        f"/api/incidents/{incident_id}/archive",
    )

    assert response.status_code == 403
