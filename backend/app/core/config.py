
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    APP_NAME: str = "Hifazat AI"
    APP_VERSION: str = "0.1.0"
    APP_ENV: Literal["development", "production"] = "development"

    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "hifazat_ai"
    POSTGRES_USER: str = "hifazat_app"
    POSTGRES_PASSWORD: str

    JWT_SECRET_KEY: SecretStr
    JWT_ALGORITHM: Literal["HS256"] = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    CORS_ORIGINS: str = ""
    ALLOWED_HOSTS: str = ""

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, value: SecretStr) -> SecretStr:
        secret = value.get_secret_value()

        if len(secret.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 bytes.")

        return value

    @field_validator("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    @classmethod
    def validate_token_expiry(cls, value: int) -> int:
        if not 1 <= value <= 60:
            raise ValueError(
                "JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 60."
            )
        return value

    @model_validator(mode="after")
    def validate_environment_security(self):
        if self.APP_ENV == "development":
            if not self.ALLOWED_HOSTS.strip():
                self.ALLOWED_HOSTS = "localhost,127.0.0.1,testserver"

            if not self.CORS_ORIGINS.strip():
                self.CORS_ORIGINS = (
                    "http://localhost:3000,http://localhost:5173"
                )

        if self.APP_ENV == "production":
            if not self.ALLOWED_HOSTS.strip():
                raise ValueError(
                    "ALLOWED_HOSTS must be configured in production."
                )

            if "*" in self.ALLOWED_HOSTS:
                raise ValueError(
                    "Wildcard hosts are not allowed in production."
                )

        if "*" in self.CORS_ORIGINS:
            raise ValueError(
                "Wildcard CORS origins are not allowed."
            )

        return self

    @property
    def allowed_hosts(self) -> list[str]:
        return [
            host.strip()
            for host in self.ALLOWED_HOSTS.split(",")
            if host.strip()
        ]

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
