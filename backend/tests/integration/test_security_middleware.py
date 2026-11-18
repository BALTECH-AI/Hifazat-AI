from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def make_production_app():
    config = Settings(
        _env_file=None,
        APP_ENV="production",
        ALLOWED_HOSTS="api.example.com",
        CORS_ORIGINS="",
        POSTGRES_PASSWORD="test-password",
        JWT_SECRET_KEY="x" * 32,
    )

    return create_app(config)


def test_trusted_host_allows_testserver(anonymous_client):
    response = anonymous_client.get(
        "/health",
        headers={"Host": "testserver"},
    )

    assert response.status_code == 200


def test_trusted_host_rejects_unknown_host(anonymous_client):
    response = anonymous_client.get(
        "/health",
        headers={"Host": "malicious.example"},
    )

    assert response.status_code == 400


def test_cors_allows_configured_origin(anonymous_client):
    response = anonymous_client.options(
        "/api/incidents",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:5173"
    )


def test_cors_rejects_unconfigured_origin(anonymous_client):
    response = anonymous_client.options(
        "/api/incidents",
        headers={
            "Origin": "https://malicious.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert (
        "access-control-allow-origin"
        not in response.headers
    )


def test_openapi_docs_are_available_in_development(anonymous_client):
    docs_response = anonymous_client.get("/docs")
    openapi_response = anonymous_client.get("/openapi.json")
    redoc_response = anonymous_client.get("/redoc")

    assert docs_response.status_code == 200
    assert openapi_response.status_code == 200
    assert redoc_response.status_code == 200


def test_production_disables_api_documentation():
    production_app = make_production_app()

    with TestClient(production_app) as client:
        headers = {"Host": "api.example.com"}

        assert client.get("/docs", headers=headers).status_code == 404
        assert client.get("/redoc", headers=headers).status_code == 404
        assert (
            client.get("/openapi.json", headers=headers).status_code
            == 404
        )


def test_production_accepts_configured_host():
    production_app = make_production_app()

    with TestClient(production_app) as client:
        response = client.get(
            "/health",
            headers={"Host": "api.example.com"},
        )

    assert response.status_code == 200


def test_production_rejects_unconfigured_host():
    production_app = make_production_app()

    with TestClient(production_app) as client:
        response = client.get(
            "/health",
            headers={"Host": "malicious.example"},
        )

    assert response.status_code == 400


def test_cors_preflight_rejects_unknown_host(anonymous_client):
    response = anonymous_client.options(
        "/api/incidents",
        headers={
            "Host": "malicious.example",
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
