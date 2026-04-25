# Kaleidoscope External API Service Plan

Kaleidoscope should become an **API-first academic paper intelligence service**. The
frontend can remain a first-party client, but the backend should be treated as the
stable product surface for downstream agents that need paper search, retrieval,
analysis, evidence, citation context, and writing support.

This document is based on a codebase review of the FastAPI backend under
`backend/app/api/v1`, the service layer under `backend/app/services`, the data models
under `backend/app/models`, and the public DeepXIV API memo at
`docs/memo/deepaxiv_api.md`.

## API-First Direction

- **Primary customers:** downstream AI agents, research assistants, literature review
  systems, retrieval pipelines, and programmatic research workflows.
- **Primary value:** turn papers into structured, cited, machine-readable knowledge.
- **Default response format:** JSON. Markdown/full-text responses should still be
  wrapped in JSON objects instead of returned as raw text.
- **Streaming exception:** SSE or NDJSON is acceptable for long-running answer streams,
  but every event payload should be JSON.
- **External dependency policy:** DeepXIV, OpenAlex, Semantic Scholar, CrossRef,
  MinerU, RAGFlow, translation, LLM, and storage credentials must stay server-side.
  External callers should call Kaleidoscope endpoints only.
- **Versioning:** keep `/api/v1` as the public version prefix. Add non-breaking fields
  only; introduce `/api/v2` for contract-breaking schema changes.

## Current Backend Surface

The backend is already a substantial FastAPI API server:

- **Framework:** FastAPI with Pydantic, SQLAlchemy async sessions, Celery tasks, Redis,
  PostgreSQL, Meilisearch, Qdrant, Neo4j, MinIO/OSS, MinerU, RAGFlow, and DeepXIV SDK.
- **Registered API routes:** 247 route handlers were found under `backend/app/api/v1`.
- **Base path:** most endpoints are mounted under `/api/v1`.
- **Health:** `/health` and `/health/services` already exist outside `/api/v1`.
- **Auth mode:** `get_current_user_id()` supports JWT when `KALEIDOSCOPE_JWT_SECRET`
  is set, and otherwise falls back to a single-user default. Public API deployment
  should not rely on single-user fallback.
- **Error shape:** global exception handlers already return JSON with `code`,
  `message`, and optional `details`.

## Recommended Public API Tiers

| Tier                      | Audience                              | Examples                                                                                  | Auth                       | Notes                                                                  |
| ------------------------- | ------------------------------------- | ----------------------------------------------------------------------------------------- | -------------------------- | ---------------------------------------------------------------------- |
| Public discovery          | unauthenticated or low-scope API keys | health, DeepXIV free paper reads, public search previews, OpenAlex graph previews         | optional API key           | Rate-limit aggressively; never expose private library data by default. |
| Agent information service | downstream agents and apps            | paper resolution, search, content, evidence, summaries, QA, citation graph, analysis JSON | API key or JWT             | This should be the main commercial/stable API tier.                    |
| User workspace API        | logged-in users and first-party UI    | collections, reading status, annotations, writing docs, alerts                            | JWT/API key scoped to user | Keep user-owned state private.                                         |
| Admin/internal API        | operators                             | reprocess, cost stats, sync triggers, benchmark reset, retraction batch scans             | admin-only                 | Do not expose as public product endpoints.                             |

## Core JSON Contract

New public endpoints should use a consistent JSON envelope:

```json
{
  "data": {},
  "meta": {
    "request_id": "req_...",
    "generated_at": "2026-04-25T00:00:00Z",
    "sources": ["local", "deepxiv", "openalex"],
    "model": "optional-model-name",
    "cache": "hit|miss|stale"
  },
  "provenance": [
    {
      "field": "data.title",
      "source": "deepxiv.head",
      "confidence": 0.98,
      "retrieved_at": "2026-04-25T00:00:00Z"
    }
  ],
  "warnings": []
}
```

Existing endpoints can keep their current shapes for compatibility, but new agent-facing
endpoints should converge on this shape so downstream agents can reason about source,
freshness, confidence, and cache state.

## DeepXIV API Integration

The project must treat every API in `docs/memo/deepaxiv_api.md` as part of
Kaleidoscope, but callers should use **our own request port**. Do not require agents to
call `https://data.rag.ac.cn` directly or pass DeepXIV tokens themselves.

The current code already implements a DeepXIV proxy router at `/api/v1/deepxiv` in
`backend/app/api/v1/deepxiv.py` and a wrapper service in
`backend/app/services/deepxiv_service.py`.

### DeepXIV Mapping

| Upstream API from memo                                  | Kaleidoscope endpoint                                       | Current status        | Recommendation                                                                                                                           |
| ------------------------------------------------------- | ----------------------------------------------------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /arxiv/?type=head&arxiv_id={id}`                   | `GET /api/v1/deepxiv/papers/{arxiv_id}/head`                | implemented           | Keep; return normalized sections and citations.                                                                                          |
| `GET /arxiv/?type=brief&arxiv_id={id}`                  | `GET /api/v1/deepxiv/papers/{arxiv_id}/brief`               | implemented           | Keep; use as cheap discovery card.                                                                                                       |
| `GET /arxiv/?type=preview&arxiv_id={id}`                | `GET /api/v1/deepxiv/papers/{arxiv_id}/preview`             | implemented           | Add `characters` query support to match upstream documented range.                                                                       |
| `GET /arxiv/?type=raw&arxiv_id={id}`                    | `GET /api/v1/deepxiv/papers/{arxiv_id}/raw`                 | implemented           | Keep JSON wrapper: `{ arxiv_id, content }`.                                                                                              |
| `GET /arxiv/?type=section&arxiv_id={id}&section={name}` | `GET /api/v1/deepxiv/papers/{arxiv_id}/section?name={name}` | implemented           | Keep; consider accepting `section` alias for upstream compatibility.                                                                     |
| `GET /arxiv/?type=json&arxiv_id={id}`                   | `GET /api/v1/deepxiv/papers/{arxiv_id}/json`                | implemented           | Keep as complete structured source payload.                                                                                              |
| `GET /arxiv/?type=markdown&arxiv_id={id}`               | `GET /api/v1/deepxiv/papers/{arxiv_id}/markdown-url`        | partially implemented | Current endpoint returns a URL. Add a JSON proxy endpoint that returns fetched/renderable content metadata if direct parity is required. |
| `POST /arxiv/?type=retrieve&query={query}`              | `GET /api/v1/deepxiv/search?q={query}`                      | implemented with GET  | Add `POST /api/v1/deepxiv/retrieve` for full upstream parity and cleaner agent payloads.                                                 |
| `GET /arxiv/trending_signal?arxiv_id={id}`              | `GET /api/v1/deepxiv/papers/{arxiv_id}/social-impact`       | implemented           | Keep; normalize missing impact as `{ message }` or 404 consistently.                                                                     |
| `GET /pmc/?type=head&pmc_id={id}`                       | `GET /api/v1/deepxiv/pmc/{pmc_id}/head`                     | implemented           | Keep.                                                                                                                                    |
| `GET /pmc/?type=json&pmc_id={id}`                       | `GET /api/v1/deepxiv/pmc/{pmc_id}/full`                     | implemented           | Keep; consider alias `/json`.                                                                                                            |
| `GET /stats/usage?days={n}`                             | not implemented                                             | missing               | Add `GET /api/v1/deepxiv/usage?days={n}` so API users can inspect proxied quota usage.                                                   |

### DeepXIV Additions Already Present

| Kaleidoscope endpoint                             | Service value                                                             |
| ------------------------------------------------- | ------------------------------------------------------------------------- |
| `GET /api/v1/deepxiv/trending?days=7&limit=30`    | Trending arXiv feed with a local-library fallback when upstream is empty. |
| `POST /api/v1/deepxiv/trending/ingest`            | Queues new trending papers for local Kaleidoscope ingestion.              |
| `POST /api/v1/deepxiv/papers/ingest`              | Batch queue arXiv IDs for local processing.                               |
| `GET /api/v1/deepxiv/websearch?q=...`             | Web/scholar search through DeepXIV.                                       |
| `GET /api/v1/deepxiv/semantic-scholar/{s2_id}`    | Semantic Scholar paper lookup through DeepXIV SDK.                        |
| `POST /api/v1/deepxiv/papers/{arxiv_id}/bookmark` | Saves a DeepXIV paper into a local `paper_group` collection.              |
| `POST /api/v1/deepxiv/agent/query`                | Runs the DeepXIV SDK ReAct agent through project LLM settings.            |

### DeepXIV Implementation Requirements

- Keep `DEEPXIV_TOKEN` and upstream base URL in server configuration only.
- Cache read-only DeepXIV responses by endpoint, paper ID, and query parameters.
- Normalize upstream variations such as `citation` vs `citations` and `preview` vs
  `content`; the current service already does part of this.
- Add strict timeout/retry metadata in `meta` so downstream agents know whether a
  response is live, cached, or stale.
- Add an upstream-parity test matrix for every endpoint listed in
  `docs/memo/deepaxiv_api.md`.

## Existing APIs That Should Be Externalized

These API groups already exist and are valuable as JSON services for downstream agents.

### 1. Agent Tool API

Current endpoints:

- `GET /api/v1/agent/tools`
- `POST /api/v1/agent/call`
- `POST /api/v1/agent/batch`

Current tools include:

- `search_papers`
- `get_paper`
- `get_citations`
- `find_similar`
- `summarize_paper`
- `extract_info`
- `ask_paper`
- `ask_papers`
- `import_paper`
- `list_collections`
- `add_to_collection`
- `export_citations`
- `get_recent_papers`

Externalization recommendation:

- This is the most important downstream-agent surface and should become the canonical
  programmatic interface.
- Add stable tool IDs, semantic versions, JSON Schema input/output declarations, auth
  scopes, rate-limit cost, and examples.
- Add DeepXIV, OpenAlex, evidence search, paper QA, claim extraction, quality reports,
  and researcher lookup to the tool registry.
- Add `GET /api/v1/agent/manifest` for an agent-friendly manifest with tool schemas,
  auth requirements, service limits, and examples.

### 2. Paper Ingestion and Resolution

Current endpoints:

- `POST /api/v1/papers/import`
- `POST /api/v1/papers/batch-import`
- `POST /api/v1/papers/import-url`
- `POST /api/v1/deepxiv/papers/ingest`
- `POST /api/v1/deepxiv/trending/ingest`
- `POST /api/v1/local/upload`
- `POST /api/v1/local/batch-upload`
- `GET /api/v1/imports/status/{doi_or_url}`
- `GET /api/v1/papers/{paper_id}/import-status`
- `GET /api/v1/imports/recent`
- `POST /api/v1/papers/resolve-arxiv`

Externalization recommendation:

- Expose a stable async ingestion API. Every import should return a `job_id`,
  `paper_id` when known, and polling URL.
- Keep local upload endpoints private/user-scoped by default because uploaded PDFs may
  contain proprietary or unpublished content.
- Add a universal resolver:

```http
POST /api/v1/resolve
```

```json
{
  "identifiers": ["2409.05591", "10.48550/arXiv.2409.05591"],
  "sources": ["local", "deepxiv", "openalex", "semantic_scholar", "crossref"],
  "create_if_missing": false
}
```

This should return canonical IDs, local availability, external matches, duplicate
groups, and recommended next actions.

### 3. Paper Metadata and Content

Current endpoints:

- `GET /api/v1/papers`
- `GET /api/v1/papers/{paper_id}`
- `GET /api/v1/papers/{paper_id}/content`
- `GET /api/v1/papers/{paper_id}/versions`
- `GET /api/v1/papers/{paper_id}/export?format=bibtex|ris|csl-json`
- `GET /api/v1/papers/{paper_id}/links`
- `GET /api/v1/papers/{paper_id}/labels`
- `POST /api/v1/papers/{paper_id}/labels`
- `GET /api/v1/papers/{paper_id}/deep-analysis`
- `GET /api/v1/papers/{paper_id}/deep-analysis-zh`
- `GET /api/v1/papers/{paper_id}/overview-image`
- `POST /api/v1/papers/{paper_id}/overview-image`

Externalization recommendation:

- Expose this as the main local paper object API.
- Return content in structured sections as well as raw markdown.
- Add lightweight fields for `has_full_text`, `has_embeddings`, `has_deep_analysis`,
  `has_claims`, `has_figures`, and `quality_score` so agents can route workflows.
- Add `GET /api/v1/papers/{paper_id}/sections` for section-level JSON without requiring
  callers to parse the whole content payload.
- Add `GET /api/v1/papers/{paper_id}/assets` for figures, tables, extracted images,
  supplementary links, code URLs, and dataset URLs.

### 4. Search, Filtering, and Discovery

Current endpoints:

- `GET /api/v1/search?q=...&mode=keyword|semantic|hybrid`
- `GET /api/v1/search/browse`
- `GET /api/v1/search/health`
- `GET /api/v1/filters/facets`
- `POST /api/v1/filters/query`
- `POST /api/v1/filters/scored-list`
- `GET /api/v1/deepxiv/search`
- `GET /api/v1/openalex/search`
- `GET /api/v1/deepxiv/trending`
- `GET /api/v1/trends/hot-keywords`
- `GET /api/v1/trends/keywords/timeseries`
- `GET /api/v1/trends/keywords/cooccurrence`
- `GET /api/v1/trends/topics`
- `GET /api/v1/trends/topics/{topic_id}`
- `GET /api/v1/trends/sleeping-papers`

Externalization recommendation:

- Offer a single agent-facing search endpoint that can federate local library,
  DeepXIV, OpenAlex, and optionally Semantic Scholar:

```http
POST /api/v1/search/federated
```

```json
{
  "query": "retrieval augmented generation evaluation",
  "sources": ["local", "deepxiv", "openalex"],
  "mode": "hybrid",
  "filters": { "year_from": 2022, "categories": ["cs.CL"] },
  "rerank": true,
  "limit": 20
}
```

- Return per-result provenance, score explanation, source availability, and local import
  action hints.
- Keep raw `/search` for UI compatibility but make `/search/federated` the external API.

### 5. Paper QA, RAG, and Evidence Retrieval

Current endpoints:

- `GET /api/v1/paper-qa/{paper_id}/status`
- `POST /api/v1/paper-qa/{paper_id}/prepare`
- `POST /api/v1/paper-qa/{paper_id}/ask`
- `POST /api/v1/paper-qa/{paper_id}/ask/stream`
- `POST /api/v1/papers/{paper_id}/ask`
- `POST /api/v1/workspaces/{collection_id}/ask`
- `GET /api/v1/workspaces/{collection_id}/evidence?q=...`
- `POST /api/v1/workspaces/{collection_id}/synthesize`
- `GET /api/v1/ragflow/sync/status`
- `POST /api/v1/ragflow/sync/trigger`
- `POST /api/v1/ragflow/query/route`
- `POST /api/v1/ragflow/eval/grounding-check`

Important gap:

- The repository contains `LocalRAGService` and `VectorSearchService`, but the workspace
  API currently routes through RAGFlow and returns disabled responses when RAGFlow sync
  is off. The project documentation also notes that local embeddings and RAGFlow are not
  fully unified yet.

Externalization recommendation:

- Add a generic evidence API independent of RAGFlow:

```http
POST /api/v1/evidence/search
```

```json
{
  "query": "What datasets are used for evaluation?",
  "paper_ids": ["paper-uuid-1", "paper-uuid-2"],
  "collection_id": null,
  "top_k": 12,
  "include_full_snippets": true
}
```

- Return chunks, section titles, similarity, citation anchors, paper metadata, and
  whether each source is from local embeddings, RAGFlow, or DeepXIV.
- Add `POST /api/v1/answers/grounded` that takes an evidence pack and produces a cited
  answer with grounding diagnostics.
- Keep SSE only for streaming answer generation; provide a non-streaming JSON version
  for every streaming endpoint.

### 6. Paper Analysis and Structured Extraction

Current endpoints:

- `POST /api/v1/analysis/papers/{paper_id}/innovation`
- `POST /api/v1/analysis/papers/{paper_id}/extract-experiments`
- `POST /api/v1/analysis/methods`
- `POST /api/v1/analysis/papers/{paper_id}/validity`
- `POST /api/v1/analysis/papers/compare`
- `POST /api/v1/claims/papers/{paper_id}/extract`
- `GET /api/v1/claims/papers/{paper_id}`
- `POST /api/v1/claims/papers/{paper_id}/assess`
- `GET /api/v1/claims/stats`
- `POST /api/v1/figures/papers/{paper_id}/analyze`
- `GET /api/v1/figures/papers/{paper_id}`
- `POST /api/v1/figures/aggregate-results`
- `GET /api/v1/quality/papers/{paper_id}/report`
- `GET /api/v1/quality/papers/{paper_id}/metadata-score`
- `GET /api/v1/quality/papers/{paper_id}/reproducibility`
- `POST /api/v1/experiments`
- `GET /api/v1/experiments`
- `GET /api/v1/experiments/methods`
- `GET /api/v1/experiments/datasets`

Externalization recommendation:

- These are high-value JSON services and should be exposed to agents as structured
  extraction endpoints.
- Add explicit response models for every LLM-generated payload.
- Store and return provenance for extracted claims, methods, datasets, metrics,
  limitations, ablations, baselines, and threats to validity.
- Add batch variants:
  - `POST /api/v1/extract/claims/batch`
  - `POST /api/v1/extract/experiments/batch`
  - `POST /api/v1/extract/figures/batch`
  - `POST /api/v1/quality/batch`

### 7. Cross-Paper Intelligence

Current endpoints:

- `GET /api/v1/intelligence/papers/{paper_id}/similar`
- `GET /api/v1/intelligence/papers/{paper_id}/reading-order`
- `GET /api/v1/intelligence/papers/{paper_id}/prerequisites`
- `GET /api/v1/intelligence/papers/{paper_id}/related-pack`
- `GET /api/v1/intelligence/papers/{paper_id}/citation-timeline`
- `GET /api/v1/intelligence/reading-path`
- `GET /api/v1/intelligence/bridge-papers`
- `POST /api/v1/intelligence/compare`
- `GET /api/v1/intelligence/papers/{paper_id}/agent-summary`
- `GET /api/v1/intelligence/papers/{paper_id}/highlights`
- `POST /api/v1/intelligence/papers/{paper_id}/summarize`
- `POST /api/v1/intelligence/papers/{paper_id}/ask`
- `POST /api/v1/cross-paper/synthesize`
- `POST /api/v1/cross-paper/timeline`
- `POST /api/v1/cross-paper/essential-papers`
- `POST /api/v1/cross-paper/bridge-papers`
- `GET /api/v1/cross-paper/contradictions`

Externalization recommendation:

- This is the second-most important agent surface after search/evidence.
- Convert it into task-oriented APIs for literature review agents:
  - `POST /api/v1/literature/review-map`
  - `POST /api/v1/literature/related-work-pack`
  - `POST /api/v1/literature/contradiction-map`
  - `POST /api/v1/literature/minimal-reading-set`
  - `POST /api/v1/literature/research-timeline`
- Return graph nodes/edges, claims, source snippets, and confidence values rather than
  only prose summaries.

### 8. Citation and Knowledge Graph

Current endpoints:

- `GET /api/v1/graph/papers/{paper_id}/citations`
- `GET /api/v1/graph/papers/{paper_id}/co-citations`
- `GET /api/v1/graph/papers/{paper_id}/coupling`
- `GET /api/v1/graph/papers/{paper_id}/similar`
- `GET /api/v1/graph/papers/{paper_id}/neighborhood`
- `POST /api/v1/graph/sync/{paper_id}`
- `POST /api/v1/graph/sync`
- `GET /api/v1/graph/stats`
- `POST /api/v1/openalex/graph`

Externalization recommendation:

- Expose read-only graph APIs to agents; keep sync writes admin-only.
- Add citation-context APIs:
  - `GET /api/v1/papers/{paper_id}/references`
  - `GET /api/v1/papers/{paper_id}/citations/context`
  - `POST /api/v1/citations/intent-classify`
- Citation context is especially valuable for agents because it tells whether a paper is
  cited as background, method, comparison, extension, criticism, or evidence.

### 9. Researcher, Venue, and Trend Intelligence

Current endpoints:

- `GET /api/v1/researchers/emerging`
- `POST /api/v1/researchers/{author_id}/enrich`
- `GET /api/v1/researchers/{author_id}/profile`
- `GET /api/v1/researchers/{author_id}/network`
- `GET /api/v1/researchers/network`
- `GET /api/v1/trends/ext/topic-evolution`
- `GET /api/v1/trends/ext/expert-finder`
- `GET /api/v1/trends/ext/venue-ranking`
- `GET /api/v1/trends/ext/author/{author_id}/direction-change`
- `GET /api/v1/analytics/overview`
- `GET /api/v1/analytics/timeline`
- `GET /api/v1/analytics/categories`
- `GET /api/v1/analytics/venues`
- `GET /api/v1/analytics/top-authors`
- `GET /api/v1/analytics/keyword-cloud`
- `GET /api/v1/analytics/citation-network`
- `GET /api/v1/analytics/data-coverage`

Externalization recommendation:

- Expose read-only researcher and trend endpoints as JSON intelligence services.
- Clearly distinguish local-library analytics from global statistics.
- Add global enrichment endpoints that merge OpenAlex, Semantic Scholar, and local data.

### 10. Collections, Workspaces, Feeds, Alerts, and Webhooks

Current endpoints:

- Collections: `POST/GET/PUT/DELETE /api/v1/collections`, collection papers, child
  collections, feed attachments, chat threads, smart collection evaluation, export.
- Feeds: `GET/POST/DELETE /api/v1/feeds`, `POST /api/v1/feeds/poll`.
- Alerts: alert rules, alerts, read state, digest listing, digest preview.
- Governance: saved searches, audit log, webhooks, corrections, reproduction attempts.
- SSE: `GET /api/v1/sse`, `GET /api/v1/sse/recent`.

Externalization recommendation:

- Keep stateful workspace APIs authenticated and user-scoped.
- Expose read-only collection summaries to agents only when the owning user grants scope.
- Turn saved searches, alert rules, and webhooks into a proper agent notification API:
  - `POST /api/v1/subscriptions/searches`
  - `GET /api/v1/subscriptions/events`
  - `POST /api/v1/webhooks/test`
  - `POST /api/v1/webhooks/{id}/rotate-secret`
- Webhook payloads should be signed with HMAC and include event type, entity IDs,
  dedupe key, and links to JSON resources.

### 11. Writing and Research Output APIs

Current endpoints:

- `GET/POST/PATCH/DELETE /api/v1/writing/documents`
- `POST /api/v1/writing/images`
- `POST /api/v1/writing/related-work`
- `POST /api/v1/writing/annotated-bibliography`
- `POST /api/v1/writing/gap-analysis`
- `POST /api/v1/writing/rebuttal`

Externalization recommendation:

- The generation endpoints are useful external services for literature-review agents.
- Keep document CRUD private to user workspaces.
- Return structured outlines, cited paragraphs, bibliography entries, and source mapping
  instead of only prose.
- Add `POST /api/v1/writing/citation-check` to verify that each generated claim has a
  source paper and source snippet.

### 12. Translation and Bilingual Analysis

Current endpoints:

- `POST /api/v1/translate`
- `GET /api/v1/papers/{paper_id}/deep-analysis-zh`
- Paper model fields include `title_zh`, `abstract_zh`, and `deep_analysis_zh`.

Externalization recommendation:

- Keep translation as a JSON service, but add paper-aware batch translation:
  - `POST /api/v1/translate/papers/batch`
  - `POST /api/v1/translate/evidence-pack`
- Return language detection, source field, translated field, model, and cache status.

## APIs That Should Not Be Public by Default

| Endpoint group                                          | Reason                                                                                                    |
| ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `/api/v1/admin/*`                                       | Reprocessing, cost inspection, weekly digest generation, and retraction batch scans are operator actions. |
| `/api/v1/ragflow/eval/metrics/reset`                    | Destructive observability reset.                                                                          |
| `/api/v1/graph/sync*`                                   | Expensive sync jobs; keep admin/internal.                                                                 |
| `/api/v1/feeds/poll`                                    | Can trigger external polling load; keep authenticated/admin or quota-gated.                               |
| `/api/v1/local/upload` and `/api/v1/local/batch-upload` | User-private files and storage cost; expose only under authenticated user scopes.                         |
| `/api/v1/users/*`                                       | Personal preferences.                                                                                     |
| `/api/v1/collaboration/*`                               | User/team-private comments, tasks, and screening records.                                                 |
| `/api/v1/auth/login` with default credentials           | Must be hardened before any public deployment.                                                            |

## Important Missing Services

The project already has many pieces, but the following services would make it much
stronger as a downstream-agent information platform.

### P0: Required Before Public API Launch

1. **API key management and scopes**

   - `POST /api/v1/api-keys`
   - `GET /api/v1/api-keys`
   - `DELETE /api/v1/api-keys/{key_id}`
   - Scopes: `search:read`, `papers:read`, `papers:write`, `analysis:run`,
     `rag:ask`, `workspace:read`, `admin:run`.

2. **Quota and usage API**

   - `GET /api/v1/usage/current`
   - `GET /api/v1/usage/history?days=30`
   - Include DeepXIV usage, LLM usage, token counts, cache hits, and per-endpoint cost.

3. **Universal paper resolver**

   - `POST /api/v1/resolve`
   - Resolve DOI, arXiv ID, PMID, PMCID, OpenAlex ID, Semantic Scholar ID, URL, or title.
   - Return local paper ID, external candidates, duplicate confidence, import status, and
     recommended action.

4. **Async job API**

   - `GET /api/v1/jobs/{job_id}`
   - `GET /api/v1/jobs?entity_id={paper_id}`
   - `POST /api/v1/jobs/{job_id}/cancel`
   - Standardize ingestion, parsing, embedding, analysis, sync, translation, and image
     generation status.

5. **DeepXIV parity completion**

   - Add missing `/api/v1/deepxiv/usage`.
   - Add POST retrieve parity.
   - Add `characters` support for preview.
   - Add aliases for upstream parameter names where safe.

6. **Agent manifest and tool schemas**

   - `GET /api/v1/agent/manifest`
   - Include JSON Schema, examples, auth scopes, cost hints, latency class, idempotency,
     and whether the tool is read-only.

7. **Standard batch API**

   - `POST /api/v1/batch`
   - Accept up to N independent API calls and return ordered JSON results.
   - This reduces agent round trips for search + resolve + summarize workflows.

8. **Local RAG workspace fallback**
   - Add a workspace endpoint backed by `LocalRAGService` so collection QA works even
     when RAGFlow sync is disabled.
   - Example: `POST /api/v1/workspaces/{collection_id}/ask-local` or route via
     `/api/v1/ragflow/query/route` automatically.

### P1: High-Value Agent Information Services

1. **Evidence pack builder**

   - `POST /api/v1/evidence/packs`
   - Build token-budgeted evidence packs from local papers, DeepXIV raw content, and
     OpenAlex metadata.

2. **Prompt context builder**

   - `POST /api/v1/agent/context-pack`
   - Return compressed, cited JSON context optimized for an agent's token budget.

3. **Citation context and intent**

   - `GET /api/v1/papers/{paper_id}/citation-contexts`
   - `POST /api/v1/citations/intent-classify`
   - Classify citation usage as background, method, comparison, criticism, extension,
     dataset, benchmark, or evidence.

4. **Structured benchmark extraction**

   - `POST /api/v1/benchmarks/extract`
   - Extract datasets, metrics, baselines, ablations, hardware, sample size, and result
     values into normalized JSON tables.

5. **Research claim verification**

   - `POST /api/v1/claims/verify`
   - Given a claim and paper set, retrieve evidence, label support/refute/insufficient,
     and return cited snippets.

6. **Paper asset service**

   - `GET /api/v1/papers/{paper_id}/figures`
   - `GET /api/v1/papers/{paper_id}/tables`
   - `GET /api/v1/papers/{paper_id}/code-and-data`
   - Normalize figures, tables, code URLs, dataset links, and supplementary materials.

7. **Federated discovery delta feed**

   - `GET /api/v1/discovery/delta?since=...`
   - Return newly discovered papers, trending changes, alert matches, and importable
     candidates for autonomous agents.

8. **Schema-first exports**
   - `POST /api/v1/exports/jsonl`
   - Export paper metadata, chunks, embeddings metadata, claims, experiments, and
     citations as JSONL for downstream training/RAG pipelines.

### P2: Advanced Research-Agent Services

1. **Literature review planner**

   - `POST /api/v1/literature/plan-review`
   - Given a topic, return search strategy, seed papers, inclusion/exclusion criteria,
     expected subtopics, and missing evidence.

2. **Systematic review screening API**

   - `POST /api/v1/review/screen`
   - Use title/abstract/full text plus criteria to label include/exclude/uncertain with
     rationales.

3. **Contradiction and consensus map**

   - `POST /api/v1/literature/consensus-map`
   - Cluster claims by research question and label agreement, disagreement, or open gap.

4. **Author and lab intelligence**

   - `GET /api/v1/researchers/{id}/global-profile`
   - `GET /api/v1/labs/search`
   - Merge local library, OpenAlex, Semantic Scholar, affiliations, collaborations, and
     topic shifts.

5. **Experiment reproducibility dossier**
   - `POST /api/v1/reproducibility/dossier`
   - Return code/data availability, protocol completeness, hardware, random seeds,
     statistical tests, baselines, ablations, and known reproduction attempts.

## Suggested Public API Product Shape

### Stable Resource APIs

| Resource      | Endpoint family                                                                    | Purpose                                                |
| ------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------ |
| Papers        | `/api/v1/papers`, `/api/v1/resolve`, `/api/v1/deepxiv/papers`                      | Local and upstream paper metadata/content.             |
| Search        | `/api/v1/search`, `/api/v1/search/federated`, `/api/v1/filters`                    | Discovery across local and external sources.           |
| Evidence      | `/api/v1/evidence/*`, `/api/v1/paper-qa/*`, `/api/v1/workspaces/*`                 | Retrieval, QA, context packs, grounded answers.        |
| Analysis      | `/api/v1/analysis/*`, `/api/v1/claims/*`, `/api/v1/figures/*`, `/api/v1/quality/*` | Structured paper understanding.                        |
| Graph         | `/api/v1/graph/*`, `/api/v1/openalex/*`                                            | Citation, co-citation, coupling, and literature graph. |
| Trends        | `/api/v1/trends/*`, `/api/v1/researchers/*`, `/api/v1/analytics/*`                 | Topic, author, venue, and library-level intelligence.  |
| Agents        | `/api/v1/agent/*`, `/api/v1/batch`                                                 | Tool discovery and tool execution.                     |
| Jobs          | `/api/v1/jobs/*`                                                                   | Long-running task lifecycle.                           |
| Subscriptions | `/api/v1/subscriptions/*`, `/api/v1/webhooks/*`, `/api/v1/sse`                     | Monitoring, alerts, and event delivery.                |

### Agent Workflow Examples

#### Discover and import relevant papers

1. `POST /api/v1/search/federated`
2. `POST /api/v1/resolve`
3. `POST /api/v1/papers/batch-import`
4. `GET /api/v1/jobs/{job_id}`
5. `POST /api/v1/evidence/packs`

#### Answer a question over a paper set

1. `POST /api/v1/evidence/search`
2. `POST /api/v1/answers/grounded`
3. `POST /api/v1/ragflow/eval/grounding-check`

#### Build a related work section

1. `POST /api/v1/literature/related-work-pack`
2. `POST /api/v1/writing/related-work`
3. `POST /api/v1/writing/citation-check`

#### Monitor a topic continuously

1. `POST /api/v1/subscriptions/searches`
2. `POST /api/v1/alerts/rules`
3. `GET /api/v1/discovery/delta?since=...`
4. Webhook or SSE event delivery.

## Schema and Reliability Requirements

- **Every public response must be typed.** Add Pydantic response models where endpoints
  currently return untyped dictionaries.
- **Every long-running write should be idempotent.** Accept `Idempotency-Key` for import,
  parsing, embedding, analysis, translation, and sync requests.
- **Every generated answer must include sources.** Downstream agents need snippets,
  paper IDs, section titles, and confidence/score metadata.
- **Every external-source response must include provenance.** Include source name,
  source endpoint, retrieved timestamp, cache state, and normalized fields.
- **Every public endpoint needs rate-limit metadata.** Return remaining quota and reset
  time via headers and/or `meta.rate_limit`.
- **Every private endpoint needs ownership checks.** Single-user fallback is useful for
  local development but should be disabled in public deployments.
- **Prefer read-only external APIs first.** Public writes create cost, data retention,
  abuse, and privacy obligations.

## Deployment Readiness Checklist

- Replace default admin credentials and require JWT/API keys in production.
- Add scoped API keys and per-key quotas.
- Add request IDs and structured access logs for all public endpoints.
- Add response caching for DeepXIV, OpenAlex, Semantic Scholar, CrossRef, search, and
  trend endpoints.
- Add OpenAPI examples for high-value agent endpoints.
- Add contract tests for the DeepXIV mapping table.
- Add smoke tests for agent workflows: search, resolve, import, job poll, content,
  evidence, grounded answer, citation export.
- Add clear data-retention policy for uploaded PDFs and generated embeddings.
- Add webhook signing and replay protection before exposing webhook delivery.

## Recommended Implementation Order

1. Complete DeepXIV proxy parity and caching.
2. Harden auth with scoped API keys and remove public reliance on single-user mode.
3. Add universal resolver and job status API.
4. Add agent manifest and expand tool registry.
5. Expose local evidence search and grounded answer APIs.
6. Add federated search across local, DeepXIV, and OpenAlex.
7. Normalize analysis response models and batch extraction APIs.
8. Add subscription delta feed and signed webhooks.
9. Add dataset/export APIs for downstream RAG and training workflows.

## Bottom Line

Kaleidoscope already contains most of the backend capabilities needed for an external
paper-intelligence API: ingestion, paper content, DeepXIV access, hybrid search,
local/RAGFlow QA, claim and experiment extraction, citation graph analysis, trend
analytics, researcher intelligence, writing support, and an initial agent tool API.

The main work is not inventing the service from scratch. The main work is to **stabilize
contracts, complete DeepXIV proxy parity, add API-key scopes, standardize JSON envelopes,
unify local/RAGFlow evidence retrieval, and expose agent-native workflows instead of
frontend-shaped endpoints only**.
