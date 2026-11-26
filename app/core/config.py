from datetime import timedelta
from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field
import os


def normalize_database_url(url: str) -> str:
	"""
	Normalize DATABASE_URL for SQLAlchemy.
	- If postgres://, convert to postgresql+psycopg2://
	- Otherwise return as-is
	"""
	if url.startswith("postgres://"):
		return url.replace("postgres://", "postgresql+psycopg2://", 1)
	return url


class Settings(BaseSettings):
	secret_key: str = Field(default=os.getenv("SECRET_KEY", "dev-secret-change-me"))
	access_token_expire_minutes: int = 60 * 24  # 24 hours
	jwt_algorithm: str = "HS256"
	database_url: str = Field(default=os.getenv("DATABASE_URL", "sqlite:///./geo.db"))
	upload_dir: str = Field(default=os.getenv("UPLOAD_DIR", "storage/uploads"))
	cors_origins: str = Field(default=os.getenv("CORS_ORIGINS", "http://localhost:5173,https://thegeodashboard.vercel.app,https://geo-dashboard-alex-lius-projects-ca62d274.vercel.app"))
	navigator_toolkit_api_key: str | None = Field(default=os.getenv("NAVIGATOR_TOOLKIT_API_KEY"))
	navigator_model: str = Field(default=os.getenv("NAVIGATOR_MODEL", "llama-3.3-70b-instruct"))
	ai_max_output_tokens: int = Field(default=int(os.getenv("AI_MAX_OUTPUT_TOKENS", "600")))
	ai_mode: Literal["embedded", "remote"] = "embedded"
	ai_service_url: str | None = Field(default=os.getenv("AI_SERVICE_URL"))
	service_name: str = Field(default=os.getenv("SERVICE_NAME", "geo-dashboard-api"))
	environment: str = Field(default=os.getenv("ENVIRONMENT", "development"))
	log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))
	@property
	def access_token_expires(self) -> timedelta:
		return timedelta(minutes=self.access_token_expire_minutes)

	@property
	def sqlalchemy_database_url(self) -> str:
		"""Normalized database URL for SQLAlchemy."""
		return normalize_database_url(self.database_url)

	@property
	def cors_origins_list(self) -> list[str]:
		"""Parse CORS origins from comma-separated string."""
		return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()


