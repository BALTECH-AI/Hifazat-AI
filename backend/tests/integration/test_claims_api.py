from uuid import uuid4

import pytest


def create_incident(client, title="Claims Test Incident"):
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


def create_evidence(client, investigation_id):
    response = client.post(
        f"/api/investigations/{investigation_id}/evidence",
        json={
            "source_name": "Test Government Source",
            "source_type": "government",
            "source_url": "https://example.org/report",
            "title": "Hypothetical Test Report",
            "content_text": "A hypothetical report about a landslide.",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_claim(client, investigation_id, payload=None):
    response = client.post(
        f"/api/investigations/{investigation_id}/claims",
        json=payload or {
            "claim_text": "A landslide blocked the main road.",
            "claim_type": "event",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_claim(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    claim = create_claim(client, investigation["id"])

    assert claim["investigation_id"] == investigation["id"]
    assert claim["claim_text"] == (
        "A landslide blocked the main road."
    )
    assert claim["claim_type"] == "event"
    assert claim["id"] is not None
    assert claim["created_at"] is not None


def test_create_claim_with_default_type(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    claim = create_claim(
        client,
        investigation["id"],
        {"claim_text": "The road is currently blocked."},
    )

    assert claim["claim_type"] == "other"


def test_create_claim_trims_whitespace(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    claim = create_claim(
        client,
        investigation["id"],
        {"claim_text": "  The road is blocked.  "},
    )

    assert claim["claim_text"] == "The road is blocked."


@pytest.mark.parametrize(
    "claim_text",
    [
        "",
        "    ",
        "abc",
    ],
)
def test_create_claim_rejects_invalid_text(
    client,
    claim_text,
):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    response = client.post(
        f"/api/investigations/{investigation['id']}/claims",
        json={"claim_text": claim_text},
    )

    assert response.status_code == 422


def test_create_claim_rejects_invalid_type(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    response = client.post(
        f"/api/investigations/{investigation['id']}/claims",
        json={
            "claim_text": "A landslide blocked the road.",
            "claim_type": "rumour",
        },
    )

    assert response.status_code == 422


def test_create_claim_for_missing_investigation(client):
    response = client.post(
        f"/api/investigations/{uuid4()}/claims",
        json={"claim_text": "A landslide blocked the road."},
    )

    assert response.status_code == 404


def test_list_investigation_claims(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    first = create_claim(client, investigation["id"])
    second = create_claim(
        client,
        investigation["id"],
        {
            "claim_text": "Several houses were damaged.",
            "claim_type": "impact",
        },
    )

    response = client.get(
        f"/api/investigations/{investigation['id']}/claims"
    )

    assert response.status_code == 200

    claims = response.json()
    assert len(claims) == 2
    assert {item["id"] for item in claims} == {
        first["id"],
        second["id"],
    }


def test_list_claims_for_missing_investigation(client):
    response = client.get(
        f"/api/investigations/{uuid4()}/claims"
    )

    assert response.status_code == 404


def test_get_claim(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])
    claim = create_claim(client, investigation["id"])

    response = client.get(f"/api/claims/{claim['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == claim["id"]


def test_get_missing_claim(client):
    response = client.get(f"/api/claims/{uuid4()}")

    assert response.status_code == 404


def test_link_evidence_to_claim(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    claim = create_claim(client, investigation["id"])
    evidence = create_evidence(client, investigation["id"])

    response = client.post(
        f"/api/investigations/{investigation['id']}"
        f"/claims/{claim['id']}/evidence",
        json={
            "evidence_id": evidence["id"],
            "relationship_type": "supports",
        },
    )

    assert response.status_code == 201

    link = response.json()
    assert link["claim_id"] == claim["id"]
    assert link["evidence_id"] == evidence["id"]
    assert link["investigation_id"] == investigation["id"]
    assert link["relationship_type"] == "supports"
    assert link["created_at"] is not None


@pytest.mark.parametrize(
    "relationship_type",
    [
        "supports",
        "contradicts",
        "mentions",
        "context",
    ],
)
def test_link_evidence_with_valid_relationship_types(
    client,
    relationship_type,
):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    claim = create_claim(client, investigation["id"])
    evidence = create_evidence(client, investigation["id"])

    response = client.post(
        f"/api/investigations/{investigation['id']}"
        f"/claims/{claim['id']}/evidence",
        json={
            "evidence_id": evidence["id"],
            "relationship_type": relationship_type,
        },
    )

    assert response.status_code == 201
    assert response.json()["relationship_type"] == relationship_type


def test_link_evidence_rejects_invalid_relationship_type(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    claim = create_claim(client, investigation["id"])
    evidence = create_evidence(client, investigation["id"])

    response = client.post(
        f"/api/investigations/{investigation['id']}"
        f"/claims/{claim['id']}/evidence",
        json={
            "evidence_id": evidence["id"],
            "relationship_type": "unrelated",
        },
    )

    assert response.status_code == 422


def test_duplicate_claim_evidence_link_returns_conflict(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    claim = create_claim(client, investigation["id"])
    evidence = create_evidence(client, investigation["id"])

    endpoint = (
        f"/api/investigations/{investigation['id']}"
        f"/claims/{claim['id']}/evidence"
    )
    payload = {
        "evidence_id": evidence["id"],
        "relationship_type": "supports",
    }

    first = client.post(endpoint, json=payload)
    second = client.post(endpoint, json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_link_rejects_claim_from_another_investigation(client):
    first_incident = create_incident(client, "First Test Incident")
    second_incident = create_incident(client, "Second Test Incident")

    first_investigation = create_investigation(
        client,
        first_incident["id"],
    )
    second_investigation = create_investigation(
        client,
        second_incident["id"],
    )

    foreign_claim = create_claim(
        client,
        second_investigation["id"],
    )
    evidence = create_evidence(
        client,
        first_investigation["id"],
    )

    response = client.post(
        f"/api/investigations/{first_investigation['id']}"
        f"/claims/{foreign_claim['id']}/evidence",
        json={
            "evidence_id": evidence["id"],
            "relationship_type": "supports",
        },
    )

    assert response.status_code == 404


def test_link_rejects_evidence_from_another_investigation(client):
    first_incident = create_incident(client, "First Test Incident")
    second_incident = create_incident(client, "Second Test Incident")

    first_investigation = create_investigation(
        client,
        first_incident["id"],
    )
    second_investigation = create_investigation(
        client,
        second_incident["id"],
    )

    claim = create_claim(client, first_investigation["id"])
    foreign_evidence = create_evidence(
        client,
        second_investigation["id"],
    )

    response = client.post(
        f"/api/investigations/{first_investigation['id']}"
        f"/claims/{claim['id']}/evidence",
        json={
            "evidence_id": foreign_evidence["id"],
            "relationship_type": "supports",
        },
    )

    assert response.status_code == 404


def test_link_rejects_missing_investigation(client):
    response = client.post(
        f"/api/investigations/{uuid4()}"
        f"/claims/{uuid4()}/evidence",
        json={
            "evidence_id": str(uuid4()),
            "relationship_type": "supports",
        },
    )

    assert response.status_code == 404


def test_list_claim_evidence(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    claim = create_claim(client, investigation["id"])
    first_evidence = create_evidence(client, investigation["id"])

    second_response = client.post(
        f"/api/investigations/{investigation['id']}/evidence",
        json={
            "source_name": "Second Test Source",
            "source_type": "news",
            "source_url": "https://news.example.org/report",
            "title": "Second Hypothetical Report",
            "content_text": "A second independent hypothetical report.",
        },
    )
    assert second_response.status_code == 201
    second_evidence = second_response.json()

    endpoint = (
        f"/api/investigations/{investigation['id']}"
        f"/claims/{claim['id']}/evidence"
    )

    for evidence in (first_evidence, second_evidence):
        response = client.post(
            endpoint,
            json={
                "evidence_id": evidence["id"],
                "relationship_type": "supports",
            },
        )
        assert response.status_code == 201

    response = client.get(
        f"/api/claims/{claim['id']}/evidence"
    )

    assert response.status_code == 200
    links = response.json()
    assert len(links) == 2
    assert {item["evidence_id"] for item in links} == {
        first_evidence["id"],
        second_evidence["id"],
    }


def test_list_evidence_for_missing_claim(client):
    response = client.get(
        f"/api/claims/{uuid4()}/evidence"
    )

    assert response.status_code == 404



# =========================
# CLAIMS API RBAC TESTS
# =========================

def test_anonymous_user_cannot_create_claim(
    analyst_client,
    anonymous_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )

    response = anonymous_client.post(
        f"/api/investigations/{investigation['id']}/claims",
        json={"claim_text": "A landslide blocked the road."},
    )

    assert response.status_code == 401


def test_reviewer_cannot_create_claim(
    analyst_client,
    reviewer_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )

    response = reviewer_client.post(
        f"/api/investigations/{investigation['id']}/claims",
        json={"claim_text": "A landslide blocked the road."},
    )

    assert response.status_code == 403


def test_analyst_can_create_claim(analyst_client):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )

    response = analyst_client.post(
        f"/api/investigations/{investigation['id']}/claims",
        json={"claim_text": "A landslide blocked the road."},
    )

    assert response.status_code == 201


def test_admin_can_create_claim(
    analyst_client,
    admin_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )

    response = admin_client.post(
        f"/api/investigations/{investigation['id']}/claims",
        json={"claim_text": "A landslide blocked the road."},
    )

    assert response.status_code == 201


def test_anonymous_user_cannot_link_evidence(
    analyst_client,
    anonymous_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )
    claim = create_claim(analyst_client, investigation["id"])
    evidence = create_evidence(analyst_client, investigation["id"])

    response = anonymous_client.post(
        f"/api/investigations/{investigation['id']}"
        f"/claims/{claim['id']}/evidence",
        json={
            "evidence_id": evidence["id"],
            "relationship_type": "supports",
        },
    )

    assert response.status_code == 401


def test_reviewer_cannot_link_evidence(
    analyst_client,
    reviewer_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )
    claim = create_claim(analyst_client, investigation["id"])
    evidence = create_evidence(analyst_client, investigation["id"])

    response = reviewer_client.post(
        f"/api/investigations/{investigation['id']}"
        f"/claims/{claim['id']}/evidence",
        json={
            "evidence_id": evidence["id"],
            "relationship_type": "supports",
        },
    )

    assert response.status_code == 403


def test_analyst_can_link_evidence(
    analyst_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )
    claim = create_claim(analyst_client, investigation["id"])
    evidence = create_evidence(analyst_client, investigation["id"])

    response = analyst_client.post(
        f"/api/investigations/{investigation['id']}"
        f"/claims/{claim['id']}/evidence",
        json={
            "evidence_id": evidence["id"],
            "relationship_type": "supports",
        },
    )

    assert response.status_code == 201


def test_admin_can_link_evidence(
    analyst_client,
    admin_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )
    claim = create_claim(analyst_client, investigation["id"])
    evidence = create_evidence(analyst_client, investigation["id"])

    response = admin_client.post(
        f"/api/investigations/{investigation['id']}"
        f"/claims/{claim['id']}/evidence",
        json={
            "evidence_id": evidence["id"],
            "relationship_type": "supports",
        },
    )

    assert response.status_code == 201


@pytest.mark.parametrize(
    "role",
    ["ADMIN", "ANALYST", "REVIEWER"],
)
def test_all_authenticated_roles_can_read_claims(
    analyst_client,
    client_factory,
    role,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )
    claim = create_claim(analyst_client, investigation["id"])

    role_client = client_factory(role)

    list_response = role_client.get(
        f"/api/investigations/{investigation['id']}/claims"
    )
    detail_response = role_client.get(
        f"/api/claims/{claim['id']}"
    )

    assert list_response.status_code == 200
    assert detail_response.status_code == 200


@pytest.mark.parametrize(
    "role",
    ["ADMIN", "ANALYST", "REVIEWER"],
)
def test_all_authenticated_roles_can_read_claim_evidence(
    analyst_client,
    client_factory,
    role,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )
    claim = create_claim(analyst_client, investigation["id"])
    evidence = create_evidence(analyst_client, investigation["id"])

    link_response = analyst_client.post(
        f"/api/investigations/{investigation['id']}"
        f"/claims/{claim['id']}/evidence",
        json={
            "evidence_id": evidence["id"],
            "relationship_type": "supports",
        },
    )
    assert link_response.status_code == 201

    role_client = client_factory(role)

    response = role_client.get(
        f"/api/claims/{claim['id']}/evidence"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_anonymous_user_cannot_list_investigation_claims(
    analyst_client,
    anonymous_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )

    response = anonymous_client.get(
        f"/api/investigations/{investigation['id']}/claims"
    )

    assert response.status_code == 401


def test_anonymous_user_cannot_get_claim(
    analyst_client,
    anonymous_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )
    claim = create_claim(analyst_client, investigation["id"])

    response = anonymous_client.get(
        f"/api/claims/{claim['id']}"
    )

    assert response.status_code == 401


def test_anonymous_user_cannot_list_claim_evidence(
    analyst_client,
    anonymous_client,
):
    incident = create_incident(analyst_client)
    investigation = create_investigation(
        analyst_client,
        incident["id"],
    )
    claim = create_claim(analyst_client, investigation["id"])

    response = anonymous_client.get(
        f"/api/claims/{claim['id']}/evidence"
    )

    assert response.status_code == 401
