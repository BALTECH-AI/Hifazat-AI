from datetime import datetime, timezone

import pytest


def create_incident(client, title="Verification Test Incident"):
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


def create_claim(client, investigation_id):
    response = client.post(
        f"/api/investigations/{investigation_id}/claims",
        json={
            "claim_text": "A landslide blocked the main road.",
            "claim_type": "event",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_verification_payload(**overrides):
    payload = {
        "status": "verified",
        "rationale": "Two independent sources support this claim.",
        "methodology": "Cross-source comparison and evidence review.",
        "confidence_score": "0.8500",
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(overrides)
    return payload


def create_test_context(client, title="Verification Test Incident"):
    incident = create_incident(client, title)
    investigation = create_investigation(client, incident["id"])
    claim = create_claim(client, investigation["id"])
    return investigation, claim


def post_verification(client, investigation_id, claim_id, payload=None):
    return client.post(
        f"/api/investigations/{investigation_id}/claims/"
        f"{claim_id}/verification-results",
        json=payload if payload is not None else create_verification_payload(),
    )


# ============================================================
# BASIC CREATE TESTS
# ============================================================

def test_create_verification_result(client, reviewer_client):
    investigation, claim = create_test_context(client)

    response = post_verification(
        reviewer_client,
        investigation["id"],
        claim["id"],
    )

    assert response.status_code == 201

    data = response.json()

    assert data["claim_id"] == claim["id"]
    assert data["investigation_id"] == investigation["id"]
    assert data["status"] == "verified"
    assert data["verifier_type"] == "human"
    assert data["verifier_name"]
    assert data["confidence_score"] == "0.8500"
    assert data["id"] is not None
    assert data["created_at"] is not None


def test_create_verification_result_with_null_confidence(
    client,
    reviewer_client,
):
    investigation, claim = create_test_context(client)

    response = post_verification(
        reviewer_client,
        investigation["id"],
        claim["id"],
        create_verification_payload(confidence_score=None),
    )

    assert response.status_code == 201
    assert response.json()["confidence_score"] is None


@pytest.mark.parametrize("score", ["0", "1", "0.5000"])
def test_create_verification_result_accepts_confidence_boundaries(
    client,
    reviewer_client,
    score,
):
    investigation, claim = create_test_context(client)

    response = post_verification(
        reviewer_client,
        investigation["id"],
        claim["id"],
        create_verification_payload(confidence_score=score),
    )

    assert response.status_code == 201


@pytest.mark.parametrize("score", ["-0.01", "1.01"])
def test_create_verification_result_rejects_invalid_confidence(
    client,
    reviewer_client,
    score,
):
    investigation, claim = create_test_context(client)

    response = post_verification(
        reviewer_client,
        investigation["id"],
        claim["id"],
        create_verification_payload(confidence_score=score),
    )

    assert response.status_code == 422


def test_create_verification_result_rejects_invalid_status(
    client,
    reviewer_client,
):
    investigation, claim = create_test_context(client)

    response = post_verification(
        reviewer_client,
        investigation["id"],
        claim["id"],
        create_verification_payload(status="pending"),
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field",
    ["rationale", "methodology"],
)
def test_create_verification_result_rejects_empty_text(
    client,
    reviewer_client,
    field,
):
    investigation, claim = create_test_context(client)

    response = post_verification(
        reviewer_client,
        investigation["id"],
        claim["id"],
        create_verification_payload(**{field: "   "}),
    )

    assert response.status_code == 422


def test_create_verification_result_rejects_naive_datetime(
    client,
    reviewer_client,
):
    investigation, claim = create_test_context(client)

    response = post_verification(
        reviewer_client,
        investigation["id"],
        claim["id"],
        create_verification_payload(
            verified_at="2026-11-06T12:00:00"
        ),
    )

    assert response.status_code == 422


# ============================================================
# RESOURCE VALIDATION TESTS
# ============================================================

def test_create_verification_result_missing_investigation(
    client,
    reviewer_client,
):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])
    claim = create_claim(client, investigation["id"])

    response = post_verification(
        reviewer_client,
        "00000000-0000-0000-0000-000000000000",
        claim["id"],
    )

    assert response.status_code == 404


def test_create_verification_result_claim_from_another_investigation(
    client,
    reviewer_client,
):
    investigation_a, claim_a = create_test_context(
        client,
        "Incident A",
    )

    investigation_b, _ = create_test_context(
        client,
        "Incident B",
    )

    response = post_verification(
        reviewer_client,
        investigation_b["id"],
        claim_a["id"],
    )

    assert response.status_code == 404


# ============================================================
# HISTORY TESTS
# ============================================================

def test_list_verification_results_preserves_history(
    client,
    reviewer_client,
):
    investigation, claim = create_test_context(client)

    older = create_verification_payload(
        status="partially_verified",
        verified_at="2026-11-05T10:00:00+05:00",
    )

    newer = create_verification_payload(
        status="verified",
        verified_at="2026-11-06T10:00:00+05:00",
    )

    first = post_verification(
        reviewer_client,
        investigation["id"],
        claim["id"],
        older,
    )

    second = post_verification(
        reviewer_client,
        investigation["id"],
        claim["id"],
        newer,
    )

    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(
        f"/api/investigations/{investigation['id']}/claims/"
        f"{claim['id']}/verification-results"
    )

    assert response.status_code == 200

    results = response.json()

    assert len(results) == 2
    assert results[0]["status"] == "verified"
    assert results[1]["status"] == "partially_verified"


def test_list_verification_results_missing_claim(client):
    incident = create_incident(client)
    investigation = create_investigation(client, incident["id"])

    response = client.get(
        f"/api/investigations/{investigation['id']}/claims/"
        "00000000-0000-0000-0000-000000000000/verification-results"
    )

    assert response.status_code == 404


def test_get_verification_result(client, reviewer_client):
    investigation, claim = create_test_context(client)

    created = post_verification(
        reviewer_client,
        investigation["id"],
        claim["id"],
    )

    assert created.status_code == 201

    result_id = created.json()["id"]

    response = client.get(
        f"/api/verification-results/{result_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == result_id
    assert response.json()["claim_id"] == claim["id"]


def test_get_missing_verification_result(client):
    from uuid import uuid4

    response = client.get(
        f"/api/verification-results/{uuid4()}"
    )

    assert response.status_code == 404


# ============================================================
# RBAC: CREATE PERMISSIONS
# ============================================================

def test_anonymous_user_cannot_create_verification_result(
    client,
    anonymous_client,
):
    investigation, claim = create_test_context(client)

    response = post_verification(
        anonymous_client,
        investigation["id"],
        claim["id"],
    )

    assert response.status_code == 401


def test_analyst_cannot_create_verification_result(
    client,
    analyst_client,
):
    investigation, claim = create_test_context(client)

    response = post_verification(
        analyst_client,
        investigation["id"],
        claim["id"],
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "role_fixture",
    ["admin_client", "reviewer_client"],
)
def test_authorized_roles_can_create_verification_result(
    request,
    client,
    role_fixture,
):
    authorized_client = request.getfixturevalue(role_fixture)

    investigation, claim = create_test_context(client)

    response = post_verification(
        authorized_client,
        investigation["id"],
        claim["id"],
    )

    assert response.status_code == 201

    data = response.json()

    assert data["verifier_type"] == "human"
    assert data["verifier_name"]


# ============================================================
# RBAC: READ HISTORY PERMISSIONS
# ============================================================

@pytest.mark.parametrize(
    "role_fixture",
    ["admin_client", "analyst_client", "reviewer_client"],
)
def test_authenticated_roles_can_read_verification_history(
    request,
    client,
    reviewer_client,
    role_fixture,
):
    reader = request.getfixturevalue(role_fixture)

    investigation, claim = create_test_context(client)

    created = post_verification(
        reviewer_client,
        investigation["id"],
        claim["id"],
    )

    assert created.status_code == 201

    response = reader.get(
        f"/api/investigations/{investigation['id']}/claims/"
        f"{claim['id']}/verification-results"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_anonymous_user_cannot_read_verification_history(
    client,
    reviewer_client,
    anonymous_client,
):
    investigation, claim = create_test_context(client)

    created = post_verification(
        reviewer_client,
        investigation["id"],
        claim["id"],
    )

    assert created.status_code == 201

    response = anonymous_client.get(
        f"/api/investigations/{investigation['id']}/claims/"
        f"{claim['id']}/verification-results"
    )

    assert response.status_code == 401


# ============================================================
# RBAC: READ INDIVIDUAL RESULT PERMISSIONS
# ============================================================

@pytest.mark.parametrize(
    "role_fixture",
    ["admin_client", "analyst_client", "reviewer_client"],
)
def test_authenticated_roles_can_read_verification_result(
    request,
    client,
    reviewer_client,
    role_fixture,
):
    reader = request.getfixturevalue(role_fixture)

    investigation, claim = create_test_context(client)

    created = post_verification(
        reviewer_client,
        investigation["id"],
        claim["id"],
    )

    assert created.status_code == 201

    result_id = created.json()["id"]

    response = reader.get(
        f"/api/verification-results/{result_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == result_id


def test_anonymous_user_cannot_read_verification_result(
    client,
    reviewer_client,
    anonymous_client,
):
    investigation, claim = create_test_context(client)

    created = post_verification(
        reviewer_client,
        investigation["id"],
        claim["id"],
    )

    assert created.status_code == 201

    result_id = created.json()["id"]

    response = anonymous_client.get(
        f"/api/verification-results/{result_id}"
    )

    assert response.status_code == 401


# ============================================================
# SECURITY: PREVENT ATTRIBUTION SPOOFING
# ============================================================

@pytest.mark.parametrize(
    "spoofed_fields",
    [
        {"verifier_type": "agent"},
        {"verifier_type": "human"},
        {"verifier_name": "Fake Agent"},
    ],
)
def test_client_cannot_spoof_verifier_attribution(
    client,
    reviewer_client,
    spoofed_fields,
):
    investigation, claim = create_test_context(client)

    payload = create_verification_payload(**spoofed_fields)

    response = post_verification(
        reviewer_client,
        investigation["id"],
        claim["id"],
        payload,
    )

    assert response.status_code == 422