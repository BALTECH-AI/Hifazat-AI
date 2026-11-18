import hashlib
from uuid import uuid4

import pytest


def create_incident(client):
    response = client.post(
        "/api/incidents",
        json={
            "title": "Hunza Landslide Test",
            "description": "Hypothetical incident for evidence API testing.",
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


def valid_evidence_payload():
    return {
        "source_name": "Gilgit-Baltistan Disaster Management",
        "source_type": "government",
        "source_url": "https://example.org/disaster-report",
        "source_group": "gb-disaster-management",
        "title": "Hypothetical Hunza Landslide Report",
        "content_text": "A hypothetical report describing a landslide.",
        "published_at": "2026-11-06T10:00:00Z",
    }


def create_evidence(client, investigation_id, payload=None):
    response = client.post(
        f"/api/investigations/{investigation_id}/evidence",
        json=payload or valid_evidence_payload(),
    )
    assert response.status_code == 201
    return response.json()


def test_create_evidence(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    payload = valid_evidence_payload()
    evidence = create_evidence(
        client,
        investigation["id"],
        payload,
    )

    expected_hash = hashlib.sha256(
        payload["content_text"].encode("utf-8")
    ).hexdigest()

    assert evidence["investigation_id"] == investigation["id"]
    assert evidence["source_name"] == payload["source_name"]
    assert evidence["source_type"] == "government"
    assert evidence["content_hash"] == expected_hash
    assert evidence["published_at"] is not None
    assert evidence["collected_at"] is not None


def test_create_evidence_with_optional_fields_omitted(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    payload = valid_evidence_payload()
    payload.pop("published_at")
    payload.pop("source_group")

    evidence = create_evidence(
        client,
        investigation["id"],
        payload,
    )

    assert evidence["published_at"] is None
    assert evidence["source_group"] is None
    assert evidence["screenshot_uri"] is None


@pytest.mark.parametrize(
    "source_type",
    [
        "government",
        "news",
        "weather_service",
        "social_media",
        "ngo",
        "other",
    ],
)
def test_create_evidence_with_valid_source_types(client, source_type):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    payload = valid_evidence_payload()
    payload["source_type"] = source_type

    evidence = create_evidence(
        client,
        investigation["id"],
        payload,
    )

    assert evidence["source_type"] == source_type


def test_create_evidence_rejects_invalid_source_type(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    payload = valid_evidence_payload()
    payload["source_type"] = "unknown"

    response = client.post(
        f"/api/investigations/{investigation['id']}/evidence",
        json=payload,
    )

    assert response.status_code == 422


def test_create_evidence_rejects_invalid_source_url(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    payload = valid_evidence_payload()
    payload["source_url"] = "javascript:alert(1)"

    response = client.post(
        f"/api/investigations/{investigation['id']}/evidence",
        json=payload,
    )

    assert response.status_code == 422


def test_create_evidence_for_missing_investigation(client):
    response = client.post(
        f"/api/investigations/{uuid4()}/evidence",
        json=valid_evidence_payload(),
    )

    assert response.status_code == 404


def test_list_investigation_evidence(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    first = create_evidence(client, investigation["id"])

    second_payload = valid_evidence_payload()
    second_payload["source_name"] = "Weather Service"
    second_payload["source_type"] = "weather_service"
    second_payload["source_url"] = "https://weather.example.org/report"

    second = create_evidence(
        client,
        investigation["id"],
        second_payload,
    )

    response = client.get(
        f"/api/investigations/{investigation['id']}/evidence"
    )

    assert response.status_code == 200

    evidence_items = response.json()
    assert len(evidence_items) == 2

    returned_ids = {item["id"] for item in evidence_items}
    assert returned_ids == {first["id"], second["id"]}


def test_list_evidence_for_missing_investigation(client):
    response = client.get(
        f"/api/investigations/{uuid4()}/evidence"
    )

    assert response.status_code == 404


def test_get_evidence(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])
    created = create_evidence(client, investigation["id"])

    response = client.get(f"/api/evidence/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["content_hash"] == created["content_hash"]


def test_get_missing_evidence(client):
    response = client.get(f"/api/evidence/{uuid4()}")

    assert response.status_code == 404


def test_same_content_produces_same_hash_without_discarding_source_records(
    client,
):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    first_payload = valid_evidence_payload()
    second_payload = valid_evidence_payload()
    second_payload["source_name"] = "Another News Source"
    second_payload["source_type"] = "news"
    second_payload["source_url"] = "https://news.example.org/report"

    first = create_evidence(
        client,
        investigation["id"],
        first_payload,
    )
    second = create_evidence(
        client,
        investigation["id"],
        second_payload,
    )

    assert first["content_hash"] == second["content_hash"]
    assert first["id"] != second["id"]

@pytest.mark.parametrize(
    "source_url",
    [
        "javascript:alert(1)",
        "https://",
        "https:///missing-host",
        "https://user:password@example.org/report",
        "not-a-url",
        "https://example.org:99999/report",
    ],
)
def test_create_evidence_rejects_malformed_source_urls(
    client,
    source_url,
):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    payload = valid_evidence_payload()
    payload["source_url"] = source_url

    response = client.post(
        f"/api/investigations/{investigation['id']}/evidence",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "screenshot_uri",
    [
        "file:///etc/passwd",
        "http://example.org/screenshot.png",
        "javascript:alert(1)",
        "https://",
    ],
)
def test_create_evidence_rejects_invalid_screenshot_uris(
    client,
    screenshot_uri,
):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    payload = valid_evidence_payload()
    payload["screenshot_uri"] = screenshot_uri

    response = client.post(
        f"/api/investigations/{investigation['id']}/evidence",
        json=payload,
    )

    assert response.status_code == 422


def test_anonymous_user_cannot_create_evidence(
    analyst_client,
    anonymous_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )

    response = anonymous_client.post(
        f"/api/investigations/{investigation['id']}/evidence",
        json=valid_evidence_payload(),
    )

    assert response.status_code == 401


def test_reviewer_cannot_create_evidence(
    analyst_client,
    reviewer_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )

    response = reviewer_client.post(
        f"/api/investigations/{investigation['id']}/evidence",
        json=valid_evidence_payload(),
    )

    assert response.status_code == 403


def test_analyst_can_create_evidence(
    analyst_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )

    response = analyst_client.post(
        f"/api/investigations/{investigation['id']}/evidence",
        json=valid_evidence_payload(),
    )

    assert response.status_code == 201


def test_admin_can_create_evidence(
    analyst_client,
    admin_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )

    response = admin_client.post(
        f"/api/investigations/{investigation['id']}/evidence",
        json=valid_evidence_payload(),
    )

    assert response.status_code == 201


@pytest.mark.parametrize(
    "role",
    ["ADMIN", "ANALYST", "REVIEWER"],
)
def test_all_authenticated_roles_can_list_evidence(
    analyst_client,
    client_factory,
    role,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )
    create_evidence(analyst_client, investigation["id"])

    role_client = client_factory(role)

    response = role_client.get(
        f"/api/investigations/{investigation['id']}/evidence"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.parametrize(
    "role",
    ["ADMIN", "ANALYST", "REVIEWER"],
)
def test_all_authenticated_roles_can_get_evidence(
    analyst_client,
    client_factory,
    role,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )
    evidence = create_evidence(
        analyst_client,
        investigation["id"],
    )

    role_client = client_factory(role)

    response = role_client.get(
        f"/api/evidence/{evidence['id']}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == evidence["id"]


def test_anonymous_user_cannot_list_evidence(
    analyst_client,
    anonymous_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )

    response = anonymous_client.get(
        f"/api/investigations/{investigation['id']}/evidence"
    )

    assert response.status_code == 401


def test_anonymous_user_cannot_get_evidence(
    analyst_client,
    anonymous_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )
    evidence = create_evidence(
        analyst_client,
        investigation["id"],
    )

    response = anonymous_client.get(
        f"/api/evidence/{evidence['id']}"
    )

    assert response.status_code == 401
