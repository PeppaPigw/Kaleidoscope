# Logging Guidelines

> Structured logging conventions for Kaleidoscope backend.

---

## Library

Use **structlog** for structured JSON logging:

```python
import structlog
logger = structlog.get_logger()
```

---

## Log Levels

| Level | Use For | Example |
|-------|---------|---------|
| `DEBUG` | Detailed flow, SQL queries | `logger.debug("Querying CrossRef", doi=doi)` |
| `INFO` | Normal operations | `logger.info("Paper ingested", doi=doi, source="rss")` |
| `WARNING` | Recoverable issues | `logger.warning("Unpaywall returned no OA", doi=doi)` |
| `ERROR` | Failed operations | `logger.error("GROBID parse failed", paper_id=id, exc_info=True)` |
| `CRITICAL` | System-level failures | `logger.critical("Database connection lost")` |

---

## Required Context Fields

Always include relevant identifiers:

```python
# ✅ Good — includes context
logger.info("Paper parsed successfully",
    paper_id=paper.id,
    doi=paper.doi,
    parser="grobid",
    sections_count=len(sections),
    duration_ms=elapsed)

# ❌ Bad — no context
logger.info("Paper parsed")
```

### Standard Fields

| Field | Type | When to Include |
|-------|------|----------------|
| `paper_id` | UUID | Any paper operation |
| `doi` | str | When available |
| `source` | str | Ingestion operations |
| `duration_ms` | int | Performance-sensitive operations |
| `task_id` | str | Celery task context |
| `error_type` | str | Error logs |

---

## Pipeline Logging

Each pipeline stage should log entry and exit:

```python
async def enrich_metadata(paper: Paper) -> Paper:
    logger.info("metadata_enrichment.start", paper_id=paper.id, doi=paper.doi)
    try:
        result = await crossref_client.get_work(paper.doi)
        logger.info("metadata_enrichment.complete",
            paper_id=paper.id,
            fields_updated=updated_fields)
        return paper
    except ExternalAPIError as e:
        logger.error("metadata_enrichment.failed",
            paper_id=paper.id,
            service=e.service,
            status=e.status)
        raise
```

---

## Rules

1. **Never log sensitive data** (API keys, user credentials)
2. **Always use structured fields** — not string interpolation
3. **Log at function boundaries** — entry/exit of significant operations
4. **Include timing** for external API calls and heavy processing
