# Ingestion Pipeline

> How papers flow from external sources into Kaleidoscope.

---

## Pipeline Overview

```
                                    ┌─────────────────┐
                                    │  Trigger Types   │
                                    │                  │
                                    │ • Scheduled RSS  │ ✅ Celery beat
                                    │ • Manual Import  │ ✅ POST /api/v1/papers/import
                                    │ • API Webhook    │ 🔲 P1
                                    │ • Batch Upload   │ ✅ POST /api/v1/papers/batch-import
                                    └────────┬────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │     1. DISCOVERY        ✅   │
                              │  RSS → CrossRef → OpenAlex   │
                              │  → rss_poller.py             │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │     2. DEDUPLICATION    ✅   │
                              │  DOI → arXiv → Title (≥0.9)  │
                              │  → deduplicator.py           │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │     3. METADATA ENRICHMENT ✅│
                              │  CrossRef → OpenAlex → S2    │
                              │  → metadata_enricher.py      │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │     4. FULL-TEXT ACQUIRE ✅  │
                              │  arXiv → OA → Unpaywall →   │
                              │  S2 → TDM → metadata-only   │
                              │  → pdf_downloader.py         │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │     5. PARSING (GROBID) ✅   │
                              │  Title, abstract, sections   │
                              │  References, TEI XML → JSON  │
                              │  → grobid_client.py          │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │     6. LLM EXTRACTION  🔲   │
                              │  Summaries, claims, methods  │
                              │  → extraction/ (P1)          │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │     7. INDEXING        ✅   │
                              │  Meilisearch + Qdrant       │
                              │  → keyword_search.py        │
                              │  → vector_search.py         │
                              │  Neo4j sync 🔲 (P1)        │
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
# tasks/ingest_tasks.py — ACTUAL IMPLEMENTATION
#
# Tasks are chained via .delay() calls, not in a single function:
#
# poll_rss_feeds → [ingest_paper] → acquire_pdf → parse_pdf_task
#                                 → index_paper_task
#
# See: backend/app/tasks/ingest_tasks.py

@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def ingest_paper(self, identifier, id_type, title="", abstract=""):
    """1. Dedup → 2. Create record → 3. Enrich metadata → 4. Queue PDF + Index"""
    dedup_result = DeduplicatorService(db).check_duplicate(doi, arxiv_id, title)
    if dedup_result.is_duplicate:
        return {"status": "duplicate"}

    paper = Paper(doi=doi, title=title, ingestion_status="discovered")
    enricher = MetadataEnricherService(db, crossref, openalex, s2)
    await enricher.enrich(paper)  # CrossRef → OpenAlex → S2 cascade

    acquire_pdf.delay(paper_id)      # Async: PDF acquisition
    index_paper_task.delay(paper_id)  # Async: Meilisearch + Qdrant
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
