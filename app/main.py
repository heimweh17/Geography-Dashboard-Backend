import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.request_id import RequestIdMiddleware



from app.routers import auth, datasets, analysis, places, osm
from app.db.database import Base, check_database_connection, engine
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.metrics import MetricsMiddleware, metrics_response
# Import models to ensure they're registered with Base.metadata
from app.db import models  # noqa: F401
from app.routers import ai, ai_proxy

log = logging.getLogger("core_api")

def create_app() -> FastAPI:
	"""
	Create and configure the FastAPI application instance.
	"""
	configure_logging(settings.service_name, settings.log_level)
	app = FastAPI(
		title="Geography Dashboard API",
		version="0.1.0",
		description="Backend API for a geospatial analytics platform."
	)
	app.add_middleware(RequestIdMiddleware)
	app.add_middleware(MetricsMiddleware, service_name=settings.service_name)
	# CORS: use configured origins (production-ready)
	app.add_middleware(
		CORSMiddleware,
		allow_origins=settings.cors_origins_list,
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	# Include routers
	app.include_router(auth.router, prefix="/auth", tags=["auth"])
	app.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
	app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
	app.include_router(places.router, prefix="/places", tags=["places"])
	app.include_router(osm.router, prefix="/osm", tags=["osm"])
	insights = ai_proxy if settings.ai_mode == "remote" else ai
	app.include_router(insights.router, prefix="/ai", tags=["ai"])

	@app.get("/healthz", include_in_schema=False)
	def healthz():
		return {"status": "ok", "service": settings.service_name, "environment": settings.environment}

	@app.get("/readyz", include_in_schema=False)
	def readyz():
		try:
			check_database_connection()
		except Exception:
			log.exception("Readiness check failed")
			raise HTTPException(status_code=503, detail="Database unavailable")
		return {"status": "ready", "service": settings.service_name}

	@app.get("/metrics", include_in_schema=False)
	def metrics():
		return metrics_response()

	return app


# Initialize a fresh deployment database unless explicitly disabled.
# This keeps Render and other hosts from starting with an empty SQLite database.
auto_create = os.getenv("AUTO_CREATE_TABLES", "true").lower()

if auto_create == "true":
	Base.metadata.create_all(bind=engine)

app = create_app()


