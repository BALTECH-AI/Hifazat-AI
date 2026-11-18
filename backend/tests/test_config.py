import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings


def make_settings(**overrides):
    values = {
        "POSTGRES_PASSWORD": "hifazat_app123",
        "JWT_SECRET_KEY": SecretStr("x" * 32),
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_development_defaults_are_secure():
    config = make_settings()

    assert config.APP_ENV == "development"
    assert config.allowed_hosts == [
        "localhost",
        "127.0.0.1",
        "testserver",
    ]
    assert "http://localhost:5173" in config.cors_origins
    assert config.is_production is False


def test_custom_origins_and_hosts_are_parsed():
    config = make_settings(
        CORS_ORIGINS="https://frontend.example.com,http://localhost:5173",
        ALLOWED_HOSTS="api.example.com,localhost",
    )

    assert config.cors_origins == [
        "https://frontend.example.com",
        "http://localhost:5173",
    ]
    assert config.allowed_hosts == ["api.example.com", "localhost"]


def test_production_requires_explicit_allowed_hosts():
    with pytest.raises(ValidationError):
        make_settings(APP_ENV="production")


def test_production_rejects_wildcard_hosts():
    with pytest.raises(ValidationError):
        make_settings(
            APP_ENV="production",
            ALLOWED_HOSTS="*",
        )


def test_wildcard_cors_origin_is_rejected():
    with pytest.raises(ValidationError):
        make_settings(CORS_ORIGINS="*")


def test_production_documentation_flag():
    config = make_settings(
        APP_ENV="production",
        ALLOWED_HOSTS="api.example.com",
    )

    assert config.is_production is True