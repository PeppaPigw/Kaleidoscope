# Backend Directory Structure

> How the Kaleidoscope backend codebase is organized.

---

## Overview

The backend follows a **modular monolith** pattern — a single deployable with clear module boundaries that can be split into microservices later if needed.

---

## Directory Layout

```
backend/
├── app/
│   ├── main.py                    # FastAPI app factory, middleware, CORS
│   ├── config.py                  # Settings via pydantic-settings (.env)
│   ├── dependencies.py            # Shared FastAPI dependencies (DB sessions, etc.)
│   │
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── paper.py               # Paper, PaperVersion
│   │   ├── author.py              # Author, AuthorAlias
│   │   ├── institution.py         # Institution
│   │   ├── journal.py             # Journal, Conference
│   │   ├── dataset.py             # Dataset, Method, Metric
│   │   ├── experiment.py          # Experiment, Result
│   │   ├── claim.py               # Claim, Evidence
│   │   ├── collection.py          # Collection, Tag, ReadingStatus
│   │   ├── user.py                # User, Role, Permission
│   │   └── audit.py               # AuditLog
│   │
│   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── paper.py
│   │   ├── search.py
│   │   ├── collection.py
│   │   └── ...
│   │
│   ├── api/                       # FastAPI routers (thin layer)
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── papers.py          # /api/v1/papers
│   │   │   ├── search.py          # /api/v1/search
│   │   │   ├── collections.py     # /api/v1/collections
│   │   │   ├── graph.py           # /api/v1/graph
│   │   │   ├── authors.py         # /api/v1/authors
│   │   │   └── agent.py           # /api/v1/agent (MCP-compatible)
│   │   └── deps.py                # Route-level dependencies
│   │
│   ├── services/                  # Business logic (core layer)
│   │   ├── __init__.py
│   │   ├── ingestion/             # Paper ingestion pipeline
│   │   │   ├── __init__.py
│   │   │   ├── rss_poller.py      # RSS feed polling
│   │   │   ├── api_fetcher.py     # CrossRef, OpenAlex, S2 API clients
│   │   │   ├── pdf_downloader.py  # Full-text PDF acquisition
│   │   │   ├── deduplicator.py    # DOI/title-based deduplication
│   │   │   └── metadata_enricher.py # Fill missing metadata
│   │   ├── parsing/               # Document parsing
│   │   │   ├── __init__.py
│   │   │   ├── grobid_client.py   # GROBID API client
│   │   │   ├── pdf_figures.py     # Figure/table extraction
│   │   │   ├── reference_linker.py # Link references to paper objects
│   │   │   └── ocr.py             # OCR for image-only PDFs
│   │   ├── extraction/            # LLM-powered extraction
│   │   │   ├── __init__.py
│   │   │   ├── summarizer.py      # Multi-level summaries
│   │   │   ├── claim_extractor.py # Claim & evidence extraction
│   │   │   ├── method_extractor.py # Method/dataset/metric extraction
│   │   │   └── structured_fields.py # Background, objective, results, etc.
│   │   ├── search/                # Search & retrieval
│   │   │   ├── __init__.py
│   │   │   ├── keyword_search.py  # Meilisearch wrapper
│   │   │   ├── vector_search.py   # Qdrant wrapper
│   │   │   ├── graph_search.py    # Neo4j traversal queries
│   │   │   └── hybrid_search.py   # RRF fusion of multiple signals
│   │   ├── graph/                 # Graph operations
│   │   │   ├── __init__.py
│   │   │   ├── citation_graph.py  # Citation network analysis
│   │   │   ├── coauthor_graph.py  # Co-authorship network
│   │   │   └── analytics.py       # PageRank, centrality, clustering
│   │   ├── recommendation.py      # Paper recommendations
│   │   ├── collection_service.py  # Collection/tag management
│   │   └── export_service.py      # BibTeX, RIS, CSL-JSON export
│   │
│   ├── tasks/                     # Celery async tasks
│   │   ├── __init__.py
│   │   ├── ingest_tasks.py        # RSS polling, batch import
│   │   ├── parse_tasks.py         # GROBID parsing, figure extraction
│   │   ├── extract_tasks.py       # LLM extraction tasks
│   │   ├── index_tasks.py         # Search index updates
│   │   └── notification_tasks.py  # Email/webhook notifications
│   │
│   ├── clients/                   # External API clients
│   │   ├── __init__.py
│   │   ├── crossref.py
│   │   ├── openalex.py
│   │   ├── semantic_scholar.py
│   │   ├── unpaywall.py
│   │   ├── papers_with_code.py
│   │   ├── arxiv.py
│   │   └── llm_client.py         # OpenAI/Anthropic unified client
│   │
│   ├── graph_db/                  # Neo4j operations
│   │   ├── __init__.py
│   │   ├── driver.py              # Neo4j driver setup
│   │   ├── queries.py             # Cypher query templates
│   │   └── sync.py                # PostgreSQL → Neo4j sync
│   │
│   └── utils/                     # Shared utilities
│       ├── __init__.py
│       ├── doi.py                 # DOI normalization & validation
│       ├── text.py                # Text similarity, normalization
│       ├── provenance.py          # Field-level provenance tracking
│       └── rate_limiter.py        # API rate limiting
│
├── alembic/                       # Database migrations
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── conftest.py
│   ├── test_ingestion/
│   ├── test_parsing/
│   ├── test_search/
│   └── test_api/
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml         # All services
│
├── pyproject.toml                 # Dependencies (uv/poetry)
├── alembic.ini
├── .env.example
└── README.md
```

---

## Module Boundaries

### Rules

1. **Routers** (`api/`) — Thin layer. Only request validation, call service, return response. No business logic.
2. **Services** (`services/`) — All business logic lives here. Services can call other services.
3. **Models** (`models/`) — SQLAlchemy models. No business logic, only data definition.
4. **Schemas** (`schemas/`) — Pydantic models for API input/output. Separate from ORM models.
5. **Tasks** (`tasks/`) — Celery tasks. Thin wrappers around service calls. Handle retries and error reporting.
6. **Clients** (`clients/`) — External API wrappers. Handle rate limiting, retries, response parsing.

### Dependency Direction

```
api/ → services/ → models/
                  → clients/
                  → graph_db/
tasks/ → services/
```

**Never**: `models/` → `services/`, `clients/` → `services/`, `api/` → `tasks/` directly

---

## Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Files | `snake_case.py` | `pdf_downloader.py` |
| Classes | `PascalCase` | `PaperService` |
| Functions | `snake_case` | `fetch_by_doi()` |
| Constants | `UPPER_SNAKE` | `MAX_RETRIES` |
| DB tables | `snake_case`, plural | `papers`, `paper_versions` |
| DB columns | `snake_case` | `published_at`, `citation_count` |
| API paths | `kebab-case` | `/api/v1/papers/{id}/related-work` |

---

## Key Patterns

### Service Pattern

```python
# services/ingestion/rss_poller.py
class RSSPollerService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis

    async def poll_feed(self, feed_url: str) -> list[Paper]:
        """Poll a single RSS feed and return new papers."""
        ...
```

### Client Pattern

```python
# clients/crossref.py
class CrossRefClient:
    BASE_URL = "https://api.crossref.org"
    
    def __init__(self, email: str, rate_limiter: RateLimiter):
        self.email = email
        self.rate_limiter = rate_limiter

    async def get_work(self, doi: str) -> CrossRefWork:
        """Fetch metadata for a DOI."""
        ...
```
