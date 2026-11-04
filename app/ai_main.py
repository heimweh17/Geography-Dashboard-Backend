import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers.ai import router as ai_router
from app.core.request_id import RequestIdMiddleware
from app.core.logging import configure_logging
from app.core.metrics import MetricsMiddleware, metrics_response
from app.db.database import check_database_connection

log = logging.getLogger("ai_service")


# ------------------------
# AI Microservice App
# ------------------------

def create_ai_app() -> FastAPI:
    configure_logging("geo-dashboard-ai", settings.log_level)
    app = FastAPI(
        title="Geo Dashboard AI Service",
        description="Dedicated microservice for AI-powered geospatial insights",
        version="0.1.0",
    )
    
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(MetricsMiddleware, service_name="geo-dashboard-ai")
    # CORS (same frontend as main backend)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount AI router
    app.include_router(
        ai_router,
        prefix="/ai",
        tags=["AI Insights"],
    )
    
    @app.get("/health")
    @app.get("/healthz", include_in_schema=False)
    def health_check():
        return {
            "status": "ok",
            "service": "ai",
        }

    @app.get("/readyz", include_in_schema=False)
    def readyz():
        if not settings.gemini_api_key:
            raise HTTPException(status_code=503, detail="Gemini API key is not configured")
        try:
            check_database_connection()
        except Exception:
            log.exception("Readiness check failed")
            raise HTTPException(status_code=503, detail="Database unavailable")
        return {"status": "ready", "service": "ai"}

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return metrics_response()

    return app


app = create_ai_app()
