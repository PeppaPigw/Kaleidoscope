"""Application settings via pydantic-settings, loaded from .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration. All values can be overridden via environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "Kaleidoscope"
    debug: bool = False

    # --- PostgreSQL ---
    database_url: str = "postgresql+asyncpg://kaleidoscope:kaleidoscope@localhost:5432/kaleidoscope"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Neo4j ---
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "kaleidoscope"

    # --- Qdrant ---
    qdrant_url: str = "http://localhost:6333"

    # --- Meilisearch ---
    meili_url: str = "http://localhost:7700"
    meili_master_key: str = "kaleidoscope-meili-key"

    # --- MinIO / S3 ---
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "kaleidoscope"
    minio_secret_key: str = "kaleidoscope"
    minio_bucket: str = "kaleidoscope-papers"
    minio_secure: bool = False

    # --- GROBID ---
    grobid_url: str = "http://localhost:8070"

    # --- External API Keys ---
    unpaywall_email: str = ""
    elsevier_tdm_api_key: str = ""
    wiley_token: str = ""
    springer_api_key: str = ""
    openai_api_key: str = ""

    # --- Celery ---
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # --- RSS ---
    rss_poll_interval_minutes: int = 30


settings = Settings()
