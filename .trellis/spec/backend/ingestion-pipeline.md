# Ingestion Pipeline

> How papers flow from external sources into Kaleidoscope.

---

## Pipeline Overview

```
                                    ┌─────────────────┐
                                    │  Trigger Types   │
                                    │                  │
                                    │ • Scheduled RSS  │
                                    │ • Manual Import  │
                                    │ • API Webhook    │
                                    │ • Batch Upload   │
                                    └────────┬────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │     1. DISCOVERY             │
                              │  RSS → CrossRef → OpenAlex   │
                              │  Extract: DOI, title, source │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │     2. DEDUPLICATION          │
                              │  DOI exact match              │
                              │  Title fuzzy match (>0.9)     │
                              │  → Skip / Merge / Create      │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │     3. METADATA ENRICHMENT    │
                              │  CrossRef → OpenAlex → S2     │
                              │  Fill: authors, venue, refs   │
                              │  Attach provenance per field  │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │     4. FULL-TEXT ACQUISITION  │
                              │  OA direct → Unpaywall → TDM │
                              │  Download PDF → MinIO         │
                              │  Or mark as metadata-only     │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │     5. PARSING (GROBID)       │
                              │  Title, abstract, sections    │
                              │  References, tables, figures  │
                              │  → Structured TEI XML → JSON  │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │     6. LLM EXTRACTION         │
                              │  Summaries (4 levels)         │
                              │  Claims, methods, results     │
                              │  Structured fields            │
                              │  → Store with confidence      │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │     7. INDEXING               │
                              │  Meilisearch (full-text)      │
                              │  Qdrant (embeddings)          │
                              │  Neo4j (citation graph)       │
                              └─────────────────────────────┘
```

---

## PDF Acquisition Strategy

Follow the priority cascade defined in `source.md`:

```python
async def acquire_pdf(paper: Paper) -> AcquisitionResult:
    """
    Priority:
    1. Direct OA download (arXiv, OA journals)
    2. Unpaywall API → best OA location
    3. Semantic Scholar → openAccessPdf
    4. Publisher TDM API (if authorized)
    5. Mark as metadata-only
    """
```

### Rate Limiting Rules

| Source | Limit | Strategy |
|--------|-------|---------|
| arXiv | 1 req / 3 sec | Token bucket |
| CrossRef | 50 req/s (polite pool) | Include `mailto:` header |
| OpenAlex | 100k/day | Count daily |
| Semantic Scholar | 100 req / 5 min (free) | Sliding window |
| Unpaywall | 100k/day | Count daily |
| Publisher sites | 1 req / 5 sec | Conservative |

---

## Celery Task Design

```python
# tasks/ingest_tasks.py

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def ingest_paper(self, identifier: str, id_type: str):
    """Full ingestion pipeline for a single paper."""
    try:
        paper = discover(identifier, id_type)
        paper = deduplicate(paper)
        paper = enrich_metadata(paper)
        pdf_result = acquire_pdf(paper)
        if pdf_result.success:
            parsed = parse_with_grobid(pdf_result.path)
            extract_with_llm(paper, parsed)  # Separate task chain
        index_paper(paper)  # Separate task
    except RateLimitError as exc:
        self.retry(exc=exc, countdown=exc.retry_after)
```

### Task Priorities

| Priority | Tasks |
|----------|-------|
| HIGH | User-initiated imports, search index updates |
| MEDIUM | Scheduled RSS polling, metadata enrichment |
| LOW | LLM extraction, batch reprocessing, graph rebuild |

---

## Error Handling

- **Transient errors** (network, rate limit): Retry with exponential backoff
- **Permanent errors** (404, invalid DOI): Log and mark paper with `ingestion_status = 'failed'`
- **Parsing errors**: Store raw PDF, mark for manual review, continue pipeline

---

## Monitoring

Track these metrics:
- Papers ingested per hour / day
- PDF acquisition success rate by source
- GROBID parsing success rate
- LLM extraction cost per paper
- Queue depth and processing latency
