# Error Handling

> Error handling conventions for Kaleidoscope backend.

---

## Error Categories

| Category | HTTP Code | Retry | Example |
|----------|----------|-------|---------|
| `VALIDATION_ERROR` | 400/422 | No | Invalid DOI format |
| `NOT_FOUND` | 404 | No | Paper not in database |
| `RATE_LIMITED` | 429 | Yes | External API throttled |
| `EXTERNAL_API_ERROR` | 502 | Yes (3x) | CrossRef timeout |
| `PARSING_ERROR` | 500 | No | GROBID failed on PDF |
| `LLM_ERROR` | 500 | Yes (2x) | OpenAI API error |
| `STORAGE_ERROR` | 500 | Yes (3x) | MinIO unavailable |

---

## Patterns

### API Layer — HTTPException

```python
from fastapi import HTTPException

raise HTTPException(
    status_code=404,
    detail={
        "code": "PAPER_NOT_FOUND",
        "message": f"No paper found with DOI: {doi}",
        "doi": doi
    }
)
```

### Service Layer — Custom Exceptions

```python
# app/exceptions.py
class KaleidoscopeError(Exception):
    """Base exception."""

class PaperNotFoundError(KaleidoscopeError):
    """Paper does not exist in database."""

class ExternalAPIError(KaleidoscopeError):
    """External API call failed."""
    def __init__(self, service: str, status: int, message: str):
        self.service = service
        self.status = status
        super().__init__(f"{service} returned {status}: {message}")

class RateLimitError(ExternalAPIError):
    """API rate limit hit."""
    def __init__(self, service: str, retry_after: int):
        self.retry_after = retry_after
        super().__init__(service, 429, f"Retry after {retry_after}s")
```

### Celery Tasks — Retry with Backoff

```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_metadata(self, doi: str):
    try:
        return crossref_client.get_work(doi)
    except RateLimitError as exc:
        self.retry(exc=exc, countdown=exc.retry_after)
    except ExternalAPIError as exc:
        self.retry(exc=exc, countdown=2 ** self.request.retries * 30)
```

---

## Rules

1. **Never swallow exceptions silently** — always log with context
2. **Distinguish transient vs permanent** — only retry transient errors
3. **Degrade gracefully** — if LLM extraction fails, still save metadata-only version
4. **Track error rates** — alert if parsing/ingestion failure rate > 5%
