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
# 0. Activate conda environment
conda activate Russell
cd backend/

# 1. Start infrastructure (7 services)
docker compose -f docker/docker-compose.yml up -d

# 2. Run migrations + seed data (first time only)
alembic upgrade head
python -m app.seed_feeds

# 3. Start API server (port 8003; 8000 is occupied by grok2api)
uvicorn app.main:app --reload --port 8003

# 4. Start Celery worker (separate terminal)
celery -A app.worker worker --loglevel=info -Q ingestion,parsing,indexing

# 5. Start Celery beat scheduler (RSS polling, separate terminal)
celery -A app.worker beat --loglevel=info
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

# Check service health
curl http://localhost:8003/health
curl http://localhost:8003/health/services
```

### API Endpoints
```
Swagger UI:     http://localhost:8003/docs
Health:         GET  /health
Service Health: GET  /health/services
Import Paper:   POST /api/v1/papers/import
Batch Import:   POST /api/v1/papers/batch-import
List Papers:    GET  /api/v1/papers
Paper Detail:   GET  /api/v1/papers/{id}
Search:         GET  /api/v1/search?q=...&mode=hybrid
List Feeds:     GET  /api/v1/feeds
Trigger Poll:   POST /api/v1/feeds/poll
```

### Environment Variables
```bash
# Copy .env.example → .env and fill in values
cp .env.example .env

# Key variables (see .env.example for full list):
DATABASE_URL=postgresql+asyncpg://kaleidoscope:kaleidoscope@localhost:5432/kaleidoscope
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687
QDRANT_URL=http://localhost:6333
MEILI_URL=http://localhost:7700
MINIO_ENDPOINT=localhost:9000
GROBID_URL=http://localhost:8070
OPENAI_API_KEY=sk-...
```

---

**Language**: All code comments and documentation in **English**.
