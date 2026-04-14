"""Application settings via pydantic-settings, loaded from backend/.env."""

from pathlib import Path
from typing import Annotated, Any

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """Application configuration. All values can be overridden via environment variables."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(...)
    debug: bool = Field(...)
    allowed_origins: Annotated[list[str], NoDecode] = Field(...)

    database_url: str = Field(...)

    redis_url: str = Field(...)

    neo4j_uri: str = Field(...)
    neo4j_user: str = Field(...)
    neo4j_password: str = Field(...)

    qdrant_url: str = Field(...)

    meili_url: str = Field(...)
    meili_master_key: str = Field(...)

    minio_endpoint: str = Field(...)
    minio_access_key: str = Field(...)
    minio_secret_key: str = Field(...)
    minio_bucket: str = Field(...)
    minio_secure: bool = Field(...)

    grobid_url: str = Field(...)

    unpaywall_email: str = Field(...)
    elsevier_tdm_api_key: str = Field(...)
    wiley_token: str = Field(...)
    springer_api_key: str = Field(
        ...,
        validation_alias=AliasChoices("SPRINGER_API_KEY", "SPRINGER_OPEN_ACCESS_KEY"),
    )
    openai_api_key: str = Field(...)
    open_base_url: str = Field(...)

    llm_api_key: str = Field(...)
    llm_base_url: str = Field(...)
    llm_model: str = Field(...)
    embed_model: str = Field(...)
    rerank_model: str = Field(...)
    rerank_base_url: str = Field(
        default=""
    )  # Override base URL for rerank (e.g. non-standard path)

    translate_base_url: str = Field(...)
    translate_model: str = Field(...)
    translate_api_key: str = Field(...)

    ragflow_api_url: str = Field(...)
    ragflow_api_key: str = Field(...)
    ragflow_dataset_papers: str = Field(...)
    ragflow_sync_enabled: bool = Field(...)
    ragflow_sync_freshness_minutes: int = Field(...)

    mineru_api_token: str = Field(...)
    mineru_concurrency: int = Field(...)

    img_host_access_key: str = Field(...)
    img_host_access_key_secret: str = Field(...)
    img_host_bucket_name: str = Field(...)
    img_host_url: str = Field(...)
    img_host_concurrency: int = Field(...)

    image_api_key: str = Field(...)
    image_api_url: str = Field(...)
    image_model: str = Field(...)

    links_api_key: str = Field(...)
    links_api_url: str = Field(...)
    links_model: str = Field(...)

    # --- DeepXiv ---
    deepxiv_token: str = Field(default="")
    deepxiv_base_url: str = Field(default="https://data.rag.ac.cn")
    deepxiv_timeout: int = Field(default=60)
    deepxiv_max_retries: int = Field(default=2)

    openalex_api_url: str = Field(default="https://api.openalex.org")
    openalex_email: str = Field(default="")
    openalex_search_limit: int = Field(default=20)
    openalex_search_max: int = Field(default=50)
    openalex_refs_per_paper: int = Field(default=40)
    openalex_related_per_paper: int = Field(default=10)

    # --- Paper QA ---
    paper_qa_embed_recall_top_k: int = Field(default=10)
    paper_qa_rerank_top_n: int = Field(default=5)
    paper_qa_answer_model: str = Field(default="")
    paper_qa_sweep_interval_minutes: int = Field(
        default=60
    )  # how often to scan for un-embedded papers
    paper_qa_sweep_batch_size: int = Field(default=50)  # max papers to queue per sweep

    celery_broker_url: str = Field(...)
    celery_result_backend: str = Field(...)

    rss_poll_interval_minutes: int = Field(...)

    # --- Admin auth ---
    admin_username: str = Field(default="admin")
    admin_password: str = Field(default="kaleidoscope")

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
