from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.auth import router as auth_router
from app.api.claims import router as claims_router
from app.api.evidence import router as evidence_router
from app.api.incidents import router as incidents_router
from app.api.investigations import router as investigations_router
from app.api.risk_assessments import router as risk_assessments_router
from app.api.verification_results import (
    router as verification_results_router,
)
from app.core.config import Settings, settings
from app.database.session import engine


def create_app(config: Settings) -> FastAPI:
    application = FastAPI(
        title=config.APP_NAME,
        description="Autonomous Disaster Response Intelligence Platform",
        version=config.APP_VERSION,
        debug=False,
        docs_url=None if config.is_production else "/docs",
        redoc_url=None if config.is_production else "/redoc",
        openapi_url=None if config.is_production else "/openapi.json",
    )

    if config.cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=config.cors_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )

    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=config.allowed_hosts,
    )

    application.include_router(incidents_router)
    application.include_router(investigations_router)
    application.include_router(evidence_router)
    application.include_router(claims_router)
    application.include_router(verification_results_router)
    application.include_router(risk_assessments_router)
    application.include_router(auth_router)

    @application.get("/", tags=["System"])
    async def root():
        return {
            "message": "Hifazat AI API is running",
            "version": config.APP_VERSION,
        }

    @application.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "ok",
            "service": "hifazat-ai-api",
            "version": config.APP_VERSION,
        }

    @application.get("/health/db", tags=["System"])
    async def database_health_check():
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))

            return {"status": "ok"}

        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed",
            )

    return application


app = create_app(settings)