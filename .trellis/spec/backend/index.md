# Backend Development Guidelines

> Conventions for Kaleidoscope's Python/FastAPI backend.

---

## Overview

Kaleidoscope backend is a **Python 3.12+ FastAPI** application with:
- **PostgreSQL** (relational data + JSONB metadata)
- **Neo4j** (citation/co-authorship graph)
- **Qdrant** (vector embeddings)
- **Meilisearch** (full-text search)
- **Celery + Redis** (async task queue)
- **MinIO/S3** (PDF/file storage)
- **GROBID** (PDF parsing, Docker service)

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Monorepo layout, module organization | ✅ Filled |
| [Database Guidelines](./database-guidelines.md) | PostgreSQL schema, Neo4j patterns, migrations | ✅ Filled |
| [API Guidelines](./api-guidelines.md) | FastAPI endpoints, request/response schemas | ✅ Filled |
| [Ingestion Pipeline](./ingestion-pipeline.md) | RSS, PDF download, GROBID, LLM extraction | ✅ Filled |
| [Error Handling](./error-handling.md) | Error types, handling strategies | ✅ Filled |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, linting, testing | ✅ Filled |
| [Logging Guidelines](./logging-guidelines.md) | Structured logging, log levels | ✅ Filled |

---

## Quick Reference

### Run Development Server
```bash
# Start all services
docker compose up -d  # PostgreSQL, Neo4j, Qdrant, Meilisearch, Redis, MinIO, GROBID
uvicorn app.main:app --reload --port 8000
celery -A app.worker worker --loglevel=info
```

### Key Commands
```bash
# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"

# Linting & formatting
ruff check .
ruff format .
mypy app/

# Testing
pytest tests/ -v
pytest tests/ -k "test_specific" --cov=app
```

### Environment Variables
```bash
# See .env.example for all variables
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/kaleidoscope
NEO4J_URI=bolt://localhost:7687
QDRANT_URL=http://localhost:6333
MEILI_URL=http://localhost:7700
REDIS_URL=redis://localhost:6379
MINIO_ENDPOINT=localhost:9000
GROBID_URL=http://localhost:8070
OPENAI_API_KEY=sk-...
```

---

**Language**: All code comments and documentation in **English**.
