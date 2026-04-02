"""Application settings via pydantic-settings, loaded from .env."""

from typing import Any

from pydantic import field_validator
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
    # Override with KALEIDOSCOPE_ALLOWED_ORIGINS=http://app.example.com,http://localhost:3000
    allowed_origins: list[str] = ["*"]

    # --- PostgreSQL ---
    database_url: str = (
        "postgresql+asyncpg://kaleidoscope:kaleidoscope@localhost:5432/kaleidoscope"
    )

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
    open_base_url: str = "https://api.openai.com/v1"  # legacy name kept for .env compat

    # --- BLSC / OpenAI-compatible LLM API ---
    llm_api_key: str = ""
    llm_base_url: str = "https://llmapi.blsc.cn"
    llm_model: str = "Qwen3-235B-A22B"
    embed_model: str = "Doubao-Embedding-Large-Text"
    rerank_model: str = "GLM-Rerank"

    # --- Translation API (NVIDIA) ---
    translate_base_url: str = "https://integrate.api.nvidia.com"
    translate_model: str = "openai/gpt-oss-120b"
    translate_api_key: str = ""

    # --- RAGFlow Sidecar ---
    ragflow_api_url: str = "http://localhost:9380"
    ragflow_api_key: str = ""
    ragflow_dataset_papers: str = ""
    ragflow_sync_enabled: bool = False
    ragflow_sync_freshness_minutes: int = 15

    # --- MinerU ---
    mineru_api_token: str = ""
    mineru_concurrency: int = 50  # max parallel MinerU tasks

    # --- Aliyun OSS (image host for paper figures) ---
    img_host_access_key: str = ""
    img_host_access_key_secret: str = ""
    img_host_bucket_name: str = "wqy-kaleidoscope"
    img_host_url: str = "https://oss-cn-shanghai.aliyuncs.com"
    img_host_concurrency: int = 100  # max parallel OSS uploads

    # --- Celery ---
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # --- RSS ---
    rss_poll_interval_minutes: int = 30

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: Any) -> Any:
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return ["*"]
            if raw.startswith("["):
                return raw
            return [item.strip() for item in raw.split(",") if item.strip()]
        return value


settings = Settings()
