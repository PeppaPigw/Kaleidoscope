# Kaleidoscope API Todo Checklist

This is the executable API checklist for turning Kaleidoscope into an API-first paper-intelligence service for downstream agents.

Legend:

- `[x]` means the endpoint currently exists in the FastAPI codebase and must be verified/hardened over time.
- `[ ]` means the endpoint or endpoint family is proposed in `docs/memo/API.md` and still needs implementation or contract design.
- `Exposure` is the recommended public/API tier, not necessarily the current authorization behavior.

Inventory generated from `backend/app/api/v1/*.py`, `backend/app/main.py`, and `docs/memo/API.md`.

- Current checklist endpoint entries: 313
- Current running OpenAPI operations verified: 308, plus `/health`
- Proposed/missing endpoint entries from `docs/memo/API.md`: 0

## Immediate Validation Pass

- [x] Verify every `[x]` endpoint has an intended external exposure tier — endpoint groups document exposure tiers; newly implemented routes are agent information services unless marked management/workspace.
- [x] Verify every public endpoint returns JSON or JSON event payloads — new public agent routes return JSON; subscription events use SSE JSON payloads; legacy citation export routes intentionally keep BibTeX/RIS compatibility.
- [x] Verify every public endpoint has auth/scope/rate-limit behavior suitable for external callers — JWT remains supported, API-key bearer authentication is now accepted, key scopes are attached to request state/headers, and deployment rate-limit policy metadata is emitted.
- [x] Verify every LLM/RAG endpoint returns provenance and sources — new context, evidence, grounded-answer, claim-verification, citation, and workspace-evidence routes include source/citation/provenance fields; legacy writing generators remain prose-first compatibility endpoints.
- [x] Verify DeepXIV public API parity is complete through Kaleidoscope-owned routes — DeepXIV proxy/parity routes are implemented under `/api/v1/deepxiv/*` and continue to route through Kaleidoscope-owned ports.
- [x] Verify admin/internal endpoints are not exposed as public product APIs — admin endpoints remain grouped as Admin/internal only in this checklist; public agent routes were added outside `/admin`.

## Runtime Response Smoke Matrix

- [x] Direct HTTP smoke-test newly implemented agent-facing API routes — `backend/app/scripts/smoke_agent_services.py` sent 44 safe in-process HTTP requests and generated `docs/memo/api-smoke-report.md` with `44/44 passed`.
- [x] Direct HTTP smoke-test every current running OpenAPI operation — `backend/app/scripts/verify_all_api_runtime.py --base-url http://127.0.0.1:8000` sent 309 real HTTP requests (`308` OpenAPI operations plus `/health`) against the `make dev` server and generated `docs/memo/full-api-runtime-report.md` plus `docs/memo/full-api-runtime-report.json` with `309/309 passed`.
- [x] Harden failures found by runtime HTTP verification — missing collaboration/experiment tables are now migrated; resource-dependent writes return handled `404` instead of FK `500`; duplicate method creation returns `409`; malformed URL import returns `422`; DeepXIV agent dependency absence returns structured `424`; SSE routes are verified as stream headers.
- [ ] Run production-like curl suite against a deployed server with real API keys, representative papers, DeepXIV token configuration, optional `deepxiv-sdk[agent]` dependencies, and external provider credentials.

## Current Implemented API Surface

### Admin

Exposure: Admin/internal only.

- [x] `GET /api/v1/admin/costs` — current; source `/backend/app/api/v1/admin.py:40`; handler `get_llm_costs` — Return accumulated LLM call counts, token usage, and estimated costs.
- [x] `GET /api/v1/admin/digest/weekly` — current; source `/backend/app/api/v1/admin.py:50`; handler `get_weekly_digest` — Weekly new-papers digest: counts, top keywords, and citation highlights.
- [x] `GET /api/v1/admin/papers/{paper_id}/provenance` — current; source `/backend/app/api/v1/admin.py:76`; handler `get_provenance` — Return field-level provenance chain (source, confidence, timestamp).
- [x] `POST /api/v1/admin/papers/{paper_id}/retraction-check` — current; source `/backend/app/api/v1/admin.py:63`; handler `retraction_check` — Check CrossRef for retraction status of a paper by its DOI.
- [x] `POST /api/v1/admin/reprocess` — current; source `/backend/app/api/v1/admin.py:19`; handler `reprocess_papers` — Trigger re-parse for papers with an outdated (or missing) parser version.
- [x] `GET /api/v1/admin/retraction-stats` — current; source `/backend/app/api/v1/admin.py:90`; handler `retraction_stats` — Scan a sample of library papers for retraction status via CrossRef. This is intentionally rate-limited to *sample* papers per call to avoid hammering the CrossRef API....

### Agent

Exposure: Agent information service.

- [x] `GET /api/v1/agent/manifest` — current; source `/backend/app/api/v1/agent.py:60`; handler `get_agent_manifest` — Return an agent-friendly JSON manifest with service metadata, tool input/output schemas, intended scopes, cost tiers, limits, DeepXIV proxy metadata, and examples.
- [x] `POST /api/v1/agent/context-pack` — current; source `/backend/app/api/v1/agent.py:80`; handler `build_context_pack` — Return compressed, cited JSON context optimized for downstream agent token budgets, using local paper metadata, summaries, analysis snippets, collection scopes, and optional evidence chunks.
- [x] `POST /api/v1/agent/batch` — current; source `/backend/app/api/v1/agent.py:115`; handler `batch_tool_calls` — Execute multiple tool calls in sequence. Useful for agents that need to gather information from multiple sources in a single request.
- [x] `POST /api/v1/agent/call` — current; source `/backend/app/api/v1/agent.py:97`; handler `call_tool` — Execute a single tool call. The agent specifies a tool name and arguments, and receives structured results.
- [x] `GET /api/v1/agent/tools` — current; source `/backend/app/api/v1/agent.py:66`; handler `list_tools` — List all available tools. Returns the tool registry with names, descriptions, and parameter schemas. AI agents use this to discover available capabilities.

### Answers

Exposure: Agent information service.

- [x] `POST /api/v1/answers/grounded` — current; source `/backend/app/api/v1/answers.py:27`; handler `grounded_answer` — Produce a non-streaming cited answer from supplied evidence or evidence packs, returning citation anchors and grounding diagnostics as JSON.

### Api Keys

Exposure: API management / User workspace.

- [x] `GET /api/v1/api-keys` — current; source `/backend/app/api/v1/api_keys.py:48`; handler `list_api_keys` — List redacted API keys for the current user, including scopes, lifecycle timestamps, revocation state, and valid scope vocabulary without exposing raw secrets.
- [x] `POST /api/v1/api-keys` — current; source `/backend/app/api/v1/api_keys.py:30`; handler `create_api_key` — Create a scoped API key, store only its SHA-256 hash, and return the raw secret exactly once.
- [x] `DELETE /api/v1/api-keys/{key_id}` — current; source `/backend/app/api/v1/api_keys.py:59`; handler `revoke_api_key` — Soft-revoke a user-owned API key by setting `revoked_at`, preserving auditability while preventing reuse.

### Batch

Exposure: Agent information service.

- [x] `POST /api/v1/batch` — current; source `/backend/app/api/v1/batch.py:34`; handler `execute_batch` — Execute up to 20 independent, allowlisted agent-safe operations (`agent.tool`, `resolve`, `context_pack`, `grounded_answer`) and return ordered JSON results.

### Alerts

Exposure: User workspace / Notifications.

- [x] `GET /api/v1/alerts` — current; source `/backend/app/api/v1/alerts.py:129`; handler `list_alerts` — List alerts/notifications for the current user.
- [x] `GET /api/v1/alerts/digests` — current; source `/backend/app/api/v1/alerts.py:172`; handler `list_digests` — List recent digest summaries.
- [x] `POST /api/v1/alerts/digests/preview` — current; source `/backend/app/api/v1/alerts.py:183`; handler `preview_digest` — Preview the next digest (dry run). Generates a digest of papers since the last one without saving.
- [x] `POST /api/v1/alerts/mark-all-read` — current; source `/backend/app/api/v1/alerts.py:158`; handler `mark_all_read` — Mark all alerts as read.
- [x] `GET /api/v1/alerts/rules` — current; source `/backend/app/api/v1/alerts.py:67`; handler `list_alert_rules` — List all alert rules for the current user.
- [x] `POST /api/v1/alerts/rules` — current; source `/backend/app/api/v1/alerts.py:43`; handler `create_alert_rule` — Create a new alert rule that triggers on matching events.
- [x] `DELETE /api/v1/alerts/rules/{rule_id}` — current; source `/backend/app/api/v1/alerts.py:114`; handler `delete_alert_rule` — Delete an alert rule.
- [x] `PUT /api/v1/alerts/rules/{rule_id}` — current; source `/backend/app/api/v1/alerts.py:94`; handler `update_alert_rule` — Update an alert rule.
- [x] `PATCH /api/v1/alerts/{alert_id}/read` — current; source `/backend/app/api/v1/alerts.py:145`; handler `mark_alert_read` — Mark a single alert as read.

### Analysis

Exposure: Agent information service.

- [x] `POST /api/v1/analysis/methods` — current; source `/backend/app/api/v1/analysis.py:334`; handler `analyze_methods` — Aggregate methods and results across a paper subset for Evidence Lab. Supports explicit paper IDs, collection-scoped analysis, or a default recent-paper scope when nei...
- [x] `POST /api/v1/analysis/papers/compare` — current; source `/backend/app/api/v1/analysis.py:401`; handler `compare_papers` — Compare two papers on methods, results, and approaches. Identifies shared/unique methods, compares results on common benchmarks, and highlights key differences.
- [x] `POST /api/v1/analysis/papers/{paper_id}/extract-experiments` — current; source `/backend/app/api/v1/analysis.py:305`; handler `extract_experiments` — Extract structured experiment data from a paper. Pulls out methods, datasets, metrics, and numerical results into a structured format suitable for cross-paper comparison.
- [x] `POST /api/v1/analysis/papers/{paper_id}/innovation` — current; source `/backend/app/api/v1/analysis.py:271`; handler `analyze_innovation` — Analyze a paper's innovation points vs. prior work. Uses LLM to compare the paper's contributions against its references and identify novel claims, methods, and approa...
- [x] `POST /api/v1/analysis/papers/{paper_id}/validity` — current; source `/backend/app/api/v1/analysis.py:369`; handler `analyze_validity` — Analyze validity threats and methodological rigor. Evaluates the paper against an 8-point checklist covering: statistical rigor, sample size, baselines, ablations, rep...

### Analytics

Exposure: User workspace analytics.

- [x] `GET /api/v1/analytics/categories` — current; source `/backend/app/api/v1/analytics.py:254`; handler `get_categories` — Category/keyword distribution across the paper library.
- [x] `GET /api/v1/analytics/citation-network` — current; source `/backend/app/api/v1/analytics.py:390`; handler `get_citation_network` — Citation network summary statistics.
- [x] `GET /api/v1/analytics/data-coverage` — current; source `/backend/app/api/v1/analytics.py:467`; handler `get_data_coverage` — Report field-level data coverage across the paper library. Use this to understand what downstream analytics are reliable: - published_at needed for timeline/trend anal...
- [x] `GET /api/v1/analytics/keyword-cloud` — current; source `/backend/app/api/v1/analytics.py:337`; handler `get_keyword_cloud` — Keyword frequency for word-cloud visualization. Returns cached trending keywords from DeepXiv (refreshed every 6 hours). Falls back to local database keywords if cache...
- [x] `GET /api/v1/analytics/overview` — current; source `/backend/app/api/v1/analytics.py:123`; handler `get_overview` — Get overview metrics for the entire paper library. Returns totals, status breakdown, source types, and citation stats.
- [x] `GET /api/v1/analytics/timeline` — current; source `/backend/app/api/v1/analytics.py:225`; handler `get_timeline` — Papers added over time, grouped by week.
- [x] `GET /api/v1/analytics/top-authors` — current; source `/backend/app/api/v1/analytics.py:302`; handler `get_top_authors` — Authors ranked by paper count in the library (live papers only).
- [x] `GET /api/v1/analytics/venues` — current; source `/backend/app/api/v1/analytics.py:281`; handler `get_top_venues` — Return top venues by paper count.

### Auth

Exposure: Auth.

- [x] `POST /api/v1/auth/login` — current; source `/backend/app/api/v1/auth.py:40`; handler `login` — Validate admin credentials and return an access token.
- [x] `POST /api/v1/auth/logout` — current; source `/backend/app/api/v1/auth.py:61`; handler `logout` — Client-side token invalidation — the API remains stateless.
- [x] `GET /api/v1/auth/me` — current; source `/backend/app/api/v1/auth.py:51`; handler `me` — Return current user identity in the active auth mode.

### Claims

Exposure: Agent information service.

- [x] `GET /api/v1/claims/papers/{paper_id}` — current; source `/backend/app/api/v1/claims.py:32`; handler `list_claims` — List all extracted claims for a paper.
- [x] `POST /api/v1/claims/papers/{paper_id}/assess` — current; source `/backend/app/api/v1/claims.py:82`; handler `assess_evidence` — Assess evidence sufficiency for a paper's claims.
- [x] `POST /api/v1/claims/papers/{paper_id}/extract` — current; source `/backend/app/api/v1/claims.py:16`; handler `extract_claims` — Extract atomic claims and evidence from a paper using LLM.
- [x] `GET /api/v1/claims/stats` — current; source `/backend/app/api/v1/claims.py:44`; handler `claims_stats` — Return aggregate claim statistics for the evidence lab header.

### Collaboration

Exposure: User/team private.

- [x] `POST /api/v1/collaboration/comments` — current; source `/backend/app/api/v1/collaboration.py:50`; handler `add_comment`
- [x] `GET /api/v1/collaboration/comments/{paper_id}` — current; source `/backend/app/api/v1/collaboration.py:65`; handler `list_comments`
- [x] `POST /api/v1/collaboration/screening` — current; source `/backend/app/api/v1/collaboration.py:128`; handler `record_screening`
- [x] `GET /api/v1/collaboration/tasks` — current; source `/backend/app/api/v1/collaboration.py:99`; handler `list_tasks`
- [x] `POST /api/v1/collaboration/tasks` — current; source `/backend/app/api/v1/collaboration.py:80`; handler `create_task`
- [x] `PATCH /api/v1/collaboration/tasks/{task_id}/complete` — current; source `/backend/app/api/v1/collaboration.py:111`; handler `complete_task`

### Collections

Exposure: User workspace.

- [x] `GET /api/v1/collections` — current; source `/backend/app/api/v1/collections.py:61`; handler `list_collections` — List all collections for the current user.
- [x] `POST /api/v1/collections` — current; source `/backend/app/api/v1/collections.py:38`; handler `create_collection` — Create a new collection.
- [x] `DELETE /api/v1/collections/{collection_id}` — current; source `/backend/app/api/v1/collections.py:114`; handler `delete_collection` — Soft-delete a collection.
- [x] `GET /api/v1/collections/{collection_id}` — current; source `/backend/app/api/v1/collections.py:76`; handler `get_collection` — Get collection with papers.
- [x] `PUT /api/v1/collections/{collection_id}` — current; source `/backend/app/api/v1/collections.py:97`; handler `update_collection` — Update collection.
- [x] `GET /api/v1/collections/{collection_id}/children` — current; source `/backend/app/api/v1/collections.py:126`; handler `list_child_collections` — List child collections for a parent collection.
- [x] `GET /api/v1/collections/{collection_id}/evaluate` — current; source `/backend/app/api/v1/collections.py:411`; handler `evaluate_smart_collection` — Evaluate a smart collection's filter and return matching papers.
- [x] `POST /api/v1/collections/{collection_id}/export` — current; source `/backend/app/api/v1/collections.py:442`; handler `export_collection_citations` — Export citations for papers in a collection.
- [x] `GET /api/v1/collections/{collection_id}/feeds` — current; source `/backend/app/api/v1/collections.py:232`; handler `list_collection_feeds` — List RSS feeds attached to a subscription collection.
- [x] `POST /api/v1/collections/{collection_id}/feeds` — current; source `/backend/app/api/v1/collections.py:208`; handler `attach_feeds_to_collection` — Attach RSS feeds to a subscription collection.
- [x] `DELETE /api/v1/collections/{collection_id}/feeds/{feed_id}` — current; source `/backend/app/api/v1/collections.py:246`; handler `detach_feed_from_collection` — Detach a feed from a subscription collection.
- [x] `GET /api/v1/collections/{collection_id}/papers` — current; source `/backend/app/api/v1/collections.py:191`; handler `get_collection_papers` — List papers in a collection with details.
- [x] `POST /api/v1/collections/{collection_id}/papers` — current; source `/backend/app/api/v1/collections.py:144`; handler `add_papers_to_collection` — Add paper(s) to a collection.
- [x] `PATCH /api/v1/collections/{collection_id}/papers/reorder` — current; source `/backend/app/api/v1/collections.py:178`; handler `reorder_collection_papers` — Reorder papers in a collection.
- [x] `DELETE /api/v1/collections/{collection_id}/papers/{paper_id}` — current; source `/backend/app/api/v1/collections.py:165`; handler `remove_paper_from_collection` — Remove a paper from a collection.
- [x] `GET /api/v1/collections/{collection_id}/threads` — current; source `/backend/app/api/v1/collections.py:282`; handler `list_collection_threads` — List chat threads scoped to a collection.
- [x] `POST /api/v1/collections/{collection_id}/threads` — current; source `/backend/app/api/v1/collections.py:263`; handler `create_collection_thread` — Create a new chat thread scoped to a collection.
- [x] `POST /api/v1/collections/{collection_id}/threads/{thread_id}/ask` — current; source `/backend/app/api/v1/collections.py:315`; handler `ask_collection_thread` — Persist a user message and generate an assistant reply for a collection.
- [x] `GET /api/v1/collections/{collection_id}/threads/{thread_id}/messages` — current; source `/backend/app/api/v1/collections.py:300`; handler `list_collection_thread_messages` — List persisted messages in a collection thread.

### Cross Paper

Exposure: Agent information service.

- [x] `POST /api/v1/cross-paper/bridge-papers` — current; source `/backend/app/api/v1/cross_paper.py:111`; handler `bridge_papers` — Detect bridge papers connecting research communities.
- [x] `GET /api/v1/cross-paper/contradictions` — current; source `/backend/app/api/v1/cross_paper.py:123`; handler `find_contradictions` — Find potentially contradicting claim pairs across papers.
- [x] `POST /api/v1/cross-paper/essential-papers` — current; source `/backend/app/api/v1/cross_paper.py:99`; handler `essential_papers` — Find the minimal essential reading set using citation importance.
- [x] `POST /api/v1/cross-paper/synthesize` — current; source `/backend/app/api/v1/cross_paper.py:47`; handler `synthesize` — Synthesize knowledge across multiple papers.
- [x] `POST /api/v1/cross-paper/timeline` — current; source `/backend/app/api/v1/cross_paper.py:73`; handler `build_timeline` — Build a research evolution timeline from papers.

### Deepxiv

Exposure: Public discovery / Agent information service.

- [x] `POST /api/v1/deepxiv/agent/query` — current; source `/backend/app/api/v1/deepxiv.py:554`; handler `agent_query` — Run a research question through the DeepXiv ReAct agent. Requires ``deepxiv-sdk[agent]`` to be installed. Uses the project-wide LLM settings from config.
- [x] `POST /api/v1/deepxiv/papers/ingest` — current; source `/backend/app/api/v1/deepxiv.py:386`; handler `ingest_papers_batch` — Queue a list of arxiv_ids for local processing. Papers already in the local DB are skipped (deduplicated by arxiv_id). Returns { queued, skipped, total, arxiv_ids_queu...
- [x] `POST /api/v1/deepxiv/papers/{arxiv_id}/bookmark` — current; source `/backend/app/api/v1/deepxiv.py:468`; handler `bookmark_paper` — Save a DeepXiv paper to a paper_group collection. Upserts a minimal paper record in the local DB (by arxiv_id), then adds it to the specified collection.
- [x] `GET /api/v1/deepxiv/papers/{arxiv_id}/brief` — current; source `/backend/app/api/v1/deepxiv.py:114`; handler `paper_brief` — Quick paper snapshot: title, TLDR, keywords, citations, GitHub URL.
- [x] `GET /api/v1/deepxiv/papers/{arxiv_id}/head` — current; source `/backend/app/api/v1/deepxiv.py:104`; handler `paper_head` — Full metadata with section-level TLDRs and token counts.
- [x] `GET /api/v1/deepxiv/papers/{arxiv_id}/json` — current; source `/backend/app/api/v1/deepxiv.py:153`; handler `paper_json` — Complete structured JSON representation.
- [x] `GET /api/v1/deepxiv/papers/{arxiv_id}/markdown-url` — current; source `/backend/app/api/v1/deepxiv.py:160`; handler `paper_markdown_url` — Public HTML URL on arxiv.org.
- [x] `GET /api/v1/deepxiv/papers/{arxiv_id}/preview` — current; source `/backend/app/api/v1/deepxiv.py:135`; handler `paper_preview` — Preview a configurable number of characters from the paper.
- [x] `GET /api/v1/deepxiv/papers/{arxiv_id}/raw` — current; source `/backend/app/api/v1/deepxiv.py:145`; handler `paper_raw` — Full paper text in Markdown.
- [x] `GET /api/v1/deepxiv/papers/{arxiv_id}/section` — current; source `/backend/app/api/v1/deepxiv.py:124`; handler `paper_section` — Read a specific paper section by name.
- [x] `GET /api/v1/deepxiv/papers/{arxiv_id}/social-impact` — current; source `/backend/app/api/v1/deepxiv.py:168`; handler `paper_social_impact` — Social media propagation metrics (tweets, likes, views).
- [x] `GET /api/v1/deepxiv/pmc/{pmc_id}/full` — current; source `/backend/app/api/v1/deepxiv.py:191`; handler `pmc_full` — PubMed Central complete structured JSON.
- [x] `GET /api/v1/deepxiv/pmc/{pmc_id}/head` — current; source `/backend/app/api/v1/deepxiv.py:181`; handler `pmc_head` — PubMed Central paper metadata.
- [x] `GET /api/v1/deepxiv/pmc/{pmc_id}/json` — current; source `/backend/app/api/v1/deepxiv.py:198`; handler `pmc_json` — PubMed Central complete structured JSON; upstream-compatible alias.
- [x] `POST /api/v1/deepxiv/retrieve` — current; source `/backend/app/api/v1/deepxiv.py:82`; handler `retrieve_papers` — Search arXiv papers via the upstream DeepXIV retrieve API using a JSON body.
- [x] `GET /api/v1/deepxiv/search` — current; source `/backend/app/api/v1/deepxiv.py:45`; handler `search_papers` — Search arXiv papers via DeepXiv (hybrid / BM25 / vector).
- [x] `GET /api/v1/deepxiv/semantic-scholar/{s2_id}` — current; source `/backend/app/api/v1/deepxiv.py:455`; handler `semantic_scholar_lookup` — Look up paper metadata by Semantic Scholar ID.
- [x] `GET /api/v1/deepxiv/trending` — current; source `/backend/app/api/v1/deepxiv.py:270`; handler `trending_papers` — Trending arXiv papers (no token required).
- [x] `POST /api/v1/deepxiv/trending/ingest` — current; source `/backend/app/api/v1/deepxiv.py:304`; handler `ingest_trending` — Fetch trending papers and queue NEW ones for local processing. Papers already in the local DB are skipped (deduplicated by arxiv_id). Returns { queued, skipped, total,...
- [x] `GET /api/v1/deepxiv/usage` — current; source `/backend/app/api/v1/deepxiv.py:205`; handler `usage_stats` — DeepXIV token usage statistics proxied through Kaleidoscope.
- [x] `GET /api/v1/deepxiv/websearch` — current; source `/backend/app/api/v1/deepxiv.py:445`; handler `web_search` — Web / scholar search (consumes 20 API credits per call).

### Experiments

Exposure: Agent information service.

- [x] `GET /api/v1/experiments` — current; source `/backend/app/api/v1/experiments.py:65`; handler `list_experiments`
- [x] `POST /api/v1/experiments` — current; source `/backend/app/api/v1/experiments.py:48`; handler `create_experiment`
- [x] `GET /api/v1/experiments/datasets` — current; source `/backend/app/api/v1/experiments.py:110`; handler `list_datasets`
- [x] `POST /api/v1/experiments/datasets` — current; source `/backend/app/api/v1/experiments.py:123`; handler `create_dataset`
- [x] `GET /api/v1/experiments/methods` — current; source `/backend/app/api/v1/experiments.py:81`; handler `list_methods`
- [x] `POST /api/v1/experiments/methods` — current; source `/backend/app/api/v1/experiments.py:94`; handler `create_method`
- [x] `GET /api/v1/experiments/{experiment_id}` — current; source `/backend/app/api/v1/experiments.py:138`; handler `get_experiment`

### Feeds

Exposure: User workspace / Internal polling.

- [x] `GET /api/v1/feeds` — current; source `/backend/app/api/v1/feeds.py:25`; handler `list_feeds` — List all RSS feed subscriptions.
- [x] `POST /api/v1/feeds` — current; source `/backend/app/api/v1/feeds.py:54`; handler `create_feed` — Add a new RSS feed subscription.
- [x] `POST /api/v1/feeds/poll` — current; source `/backend/app/api/v1/feeds.py:114`; handler `trigger_poll` — Manually trigger polling of all active RSS feeds.
- [x] `DELETE /api/v1/feeds/{feed_id}` — current; source `/backend/app/api/v1/feeds.py:96`; handler `delete_feed` — Delete an RSS feed subscription.

### Figures

Exposure: Agent information service.

- [x] `POST /api/v1/figures/aggregate-results` — current; source `/backend/app/api/v1/figures.py:47`; handler `aggregate_results` — Aggregate experimental results from multiple papers into a unified comparison table.
- [x] `GET /api/v1/figures/papers/{paper_id}` — current; source `/backend/app/api/v1/figures.py:35`; handler `get_figures` — Get previously extracted figures/tables for a paper.
- [x] `POST /api/v1/figures/papers/{paper_id}/analyze` — current; source `/backend/app/api/v1/figures.py:20`; handler `analyze_figures` — Analyze and classify all figures/tables in a paper.

### Filters

Exposure: Agent information service.

- [x] `GET /api/v1/filters/facets` — current; source `/backend/app/api/v1/filters.py:57`; handler `get_facets` — Get aggregated facet counts for the paper corpus. Returns grouped counts per requested field, useful for building filter UI (sidebar facets, checkboxes, sliders).
- [x] `POST /api/v1/filters/query` — current; source `/backend/app/api/v1/filters.py:87`; handler `query_papers` — Query papers with multi-field filtering and sorting. Supports all filter fields: year range, venue, author, OA status, paper type, journal ranking (SJR/CCF/IF), citati...
- [x] `POST /api/v1/filters/scored-list` — current; source `/backend/app/api/v1/filters.py:113`; handler `scored_paper_list` — Get papers ranked by custom multi-factor scoring. score = w₁·citations + w₂·recency + w₃·relevance + w₄·impact_factor + w₅·oa_bonus + w₆·reproducibility All weights ar...

### Governance

Exposure: User workspace / Governance.

- [x] `GET /api/v1/governance/audit` — current; source `/backend/app/api/v1/governance.py:78`; handler `list_audit_log` — List audit log entries.
- [x] `GET /api/v1/governance/papers/{paper_id}/corrections` — current; source `/backend/app/api/v1/governance.py:140`; handler `get_paper_corrections` — List corrections submitted for a paper.
- [x] `POST /api/v1/governance/papers/{paper_id}/corrections` — current; source `/backend/app/api/v1/governance.py:122`; handler `submit_correction` — Submit a correction for paper metadata.
- [x] `GET /api/v1/governance/papers/{paper_id}/reproductions` — current; source `/backend/app/api/v1/governance.py:167`; handler `get_reproductions` — List reproduction attempts for a paper.
- [x] `POST /api/v1/governance/papers/{paper_id}/reproductions` — current; source `/backend/app/api/v1/governance.py:150`; handler `log_reproduction` — Log a reproduction attempt for a paper.
- [x] `GET /api/v1/governance/searches` — current; source `/backend/app/api/v1/governance.py:57`; handler `list_saved_searches` — List saved searches.
- [x] `POST /api/v1/governance/searches` — current; source `/backend/app/api/v1/governance.py:41`; handler `create_saved_search` — Create a saved search.
- [x] `DELETE /api/v1/governance/searches/{search_id}` — current; source `/backend/app/api/v1/governance.py:66`; handler `delete_saved_search` — Delete a saved search.
- [x] `GET /api/v1/governance/webhooks` — current; source `/backend/app/api/v1/governance.py:101`; handler `list_webhooks` — List webhooks.
- [x] `POST /api/v1/governance/webhooks` — current; source `/backend/app/api/v1/governance.py:90`; handler `create_webhook` — Create a webhook.
- [x] `DELETE /api/v1/governance/webhooks/{webhook_id}` — current; source `/backend/app/api/v1/governance.py:110`; handler `delete_webhook` — Delete a webhook.

### Graph

Exposure: Agent information service.

- [x] `GET /api/v1/graph/papers/{paper_id}/citations` — current; source `/backend/app/api/v1/graph.py:16`; handler `get_paper_citations` — Get citation relationships for a paper. - **forward**: Papers that cite this paper - **backward**: References this paper cites - **both**: Both directions
- [x] `GET /api/v1/graph/papers/{paper_id}/co-citations` — current; source `/backend/app/api/v1/graph.py:34`; handler `co_citation_analysis` — Co-citation analysis: papers frequently cited alongside this one. Co-citation count = number of papers that cite both target and result. Higher co-citation implies top...
- [x] `GET /api/v1/graph/papers/{paper_id}/coupling` — current; source `/backend/app/api/v1/graph.py:49`; handler `bibliographic_coupling` — Bibliographic coupling: papers citing the same references as this one. Shared references count = number of common reference targets. Higher coupling implies similar in...
- [x] `GET /api/v1/graph/papers/{paper_id}/neighborhood` — current; source `/backend/app/api/v1/graph.py:80`; handler `get_graph_neighborhood` — Get graph neighborhood for visualization. Returns nodes and edges within `depth` hops for rendering with Cytoscape.js or D3.js on the frontend.
- [x] `GET /api/v1/graph/papers/{paper_id}/similar` — current; source `/backend/app/api/v1/graph.py:64`; handler `recommend_similar` — Recommend similar papers using multi-signal fusion. Combines bibliographic coupling + co-citation through Reciprocal Rank Fusion (RRF) for robust recommendations.
- [x] `GET /api/v1/graph/stats` — current; source `/backend/app/api/v1/graph.py:127`; handler `graph_stats` — Get graph statistics (node/edge counts).
- [x] `POST /api/v1/graph/sync` — current; source `/backend/app/api/v1/graph.py:116`; handler `sync_all_papers` — Batch-sync all papers to Neo4j graph.
- [x] `POST /api/v1/graph/sync/{paper_id}` — current; source `/backend/app/api/v1/graph.py:96`; handler `sync_paper_to_graph` — Trigger sync of a specific paper to Neo4j.

### Health

Exposure: System health.

- [x] `GET /health` — current; source `/backend/app/main.py:952`; handler `health_check` — Health check endpoint.
- [x] `GET /health/services` — current; source `/backend/app/main.py:964`; handler `services_health` — Check health of all dependent services.

### Imports

Exposure: Agent information service.

- [x] `GET /api/v1/imports/recent` — current; source `/backend/app/api/v1/imports.py:65`; handler `recent_imports` — Return the most recently ingested or updated papers with their status.
- [x] `GET /api/v1/imports/status/{doi_or_url:path}` — current; source `/backend/app/api/v1/imports.py:22`; handler `get_import_status` — Poll the ingestion status of a paper by DOI or stored source URL. Clients should poll this endpoint every 2s while status is non-terminal.

### Intelligence

Exposure: Agent information service.

- [x] `GET /api/v1/intelligence/bridge-papers` — current; source `/backend/app/api/v1/intelligence.py:109`; handler `get_bridge_papers` — Find papers that bridge two keyword areas.
- [x] `POST /api/v1/intelligence/compare` — current; source `/backend/app/api/v1/intelligence.py:125`; handler `compare_papers` — Compare up to five papers side by side.
- [x] `GET /api/v1/intelligence/papers/{paper_id}/agent-summary` — current; source `/backend/app/api/v1/intelligence.py:138`; handler `get_agent_summary` — Return a structured paper summary optimized for MCP tool consumption. Format mirrors the Anthropic MCP tool response schema — all fields are typed strings or lists for...
- [x] `POST /api/v1/intelligence/papers/{paper_id}/ask` — current; source `/backend/app/api/v1/intelligence.py:264`; handler `ask_about_paper` — Answer a question about a paper using stored analysis data.
- [x] `GET /api/v1/intelligence/papers/{paper_id}/citation-timeline` — current; source `/backend/app/api/v1/intelligence.py:84`; handler `get_citation_timeline` — Return citation counts over time for the given paper.
- [x] `GET /api/v1/intelligence/papers/{paper_id}/highlights` — current; source `/backend/app/api/v1/intelligence.py:213`; handler `get_paper_highlights` — Return AI-derived highlights/contributions/limitations for a paper.
- [x] `GET /api/v1/intelligence/papers/{paper_id}/prerequisites` — current; source `/backend/app/api/v1/intelligence.py:59`; handler `get_prerequisites` — Return foundational prerequisites for the given paper.
- [x] `GET /api/v1/intelligence/papers/{paper_id}/reading-order` — current; source `/backend/app/api/v1/intelligence.py:48`; handler `get_reading_order` — Build a reading order from the root paper's citation neighborhood.
- [x] `GET /api/v1/intelligence/papers/{paper_id}/related-pack` — current; source `/backend/app/api/v1/intelligence.py:70`; handler `get_related_work_pack` — Return a related-work pack around a root paper.
- [x] `GET /api/v1/intelligence/papers/{paper_id}/similar` — current; source `/backend/app/api/v1/intelligence.py:20`; handler `get_similar_papers` — Return papers similar to the given root paper.
- [x] `POST /api/v1/intelligence/papers/{paper_id}/summarize` — current; source `/backend/app/api/v1/intelligence.py:239`; handler `summarize_paper` — Return AI summary for a paper.
- [x] `GET /api/v1/intelligence/reading-path` — current; source `/backend/app/api/v1/intelligence.py:97`; handler `get_reading_path` — Find the shortest citation path between two papers.

### Jobs

Exposure: Agent information service / Async lifecycle.

- [x] `GET /api/v1/jobs` — current; source `/backend/app/api/v1/jobs.py:22`; handler `list_jobs` — Return a stable JSON list shape for jobs associated with an entity ID; currently reports the Celery result-backend-only tracking limitation until durable entity-to-job indexing is added.
- [x] `GET /api/v1/jobs/{job_id}` — current; source `/backend/app/api/v1/jobs.py:30`; handler `get_job` — Return Celery-backed job state, public status, readiness, result, error, terminal flags, and optional traceback.
- [x] `POST /api/v1/jobs/{job_id}/cancel` — current; source `/backend/app/api/v1/jobs.py:39`; handler `cancel_job` — Revoke a queued or running Celery job, with optional terminate/signal controls, and return the observed job state.

### Knowledge

Exposure: User workspace / Agent information service.

- [x] `POST /api/v1/knowledge/annotations` — current; source `/backend/app/api/v1/knowledge.py:95`; handler `create_annotation` — Create a highlight, note, or question on a paper.
- [x] `GET /api/v1/knowledge/annotations/papers/{paper_id}` — current; source `/backend/app/api/v1/knowledge.py:117`; handler `list_annotations` — List all annotations for a paper.
- [x] `DELETE /api/v1/knowledge/annotations/{annotation_id}` — current; source `/backend/app/api/v1/knowledge.py:130`; handler `delete_annotation` — Delete an annotation.
- [x] `GET /api/v1/knowledge/cards` — current; source `/backend/app/api/v1/knowledge.py:251`; handler `list_cards` — List flashcards.
- [x] `GET /api/v1/knowledge/cards/due` — current; source `/backend/app/api/v1/knowledge.py:223`; handler `get_due_cards` — Get flashcards due for review (spaced repetition).
- [x] `POST /api/v1/knowledge/cards/generate/{paper_id}` — current; source `/backend/app/api/v1/knowledge.py:209`; handler `generate_cards` — Generate flashcards from a paper using LLM.
- [x] `POST /api/v1/knowledge/cards/{card_id}/review` — current; source `/backend/app/api/v1/knowledge.py:236`; handler `review_card` — Record a flashcard review (SM-2 spaced repetition).
- [x] `GET /api/v1/knowledge/ext/papers/{paper_id}/glossary` — current; source `/backend/app/api/v1/knowledge_ext.py:33`; handler `get_glossary` — Return glossary terms associated with a paper.
- [x] `GET /api/v1/knowledge/ext/papers/{paper_id}/quiz` — current; source `/backend/app/api/v1/knowledge_ext.py:21`; handler `generate_quiz` — Generate a small quiz from a paper.
- [x] `GET /api/v1/knowledge/ext/retraction-stats` — current; source `/backend/app/api/v1/knowledge_ext.py:45`; handler `get_retraction_stats` — Return retraction statistics starting from the given year.
- [x] `GET /api/v1/knowledge/glossary` — current; source `/backend/app/api/v1/knowledge.py:179`; handler `list_glossary` — List glossary terms.
- [x] `POST /api/v1/knowledge/glossary` — current; source `/backend/app/api/v1/knowledge.py:151`; handler `add_glossary_term` — Add a term to your personal glossary.
- [x] `POST /api/v1/knowledge/glossary/auto-extract/{paper_id}` — current; source `/backend/app/api/v1/knowledge.py:165`; handler `auto_extract_terms` — Auto-extract technical terms from a paper using LLM.
- [x] `GET /api/v1/knowledge/glossary/search` — current; source `/backend/app/api/v1/knowledge.py:193`; handler `search_glossary` — Search glossary terms.
- [x] `GET /api/v1/knowledge/reading-log` — current; source `/backend/app/api/v1/knowledge.py:66`; handler `get_reading_history` — Get reading history.
- [x] `POST /api/v1/knowledge/reading-log` — current; source `/backend/app/api/v1/knowledge.py:50`; handler `log_reading_event` — Log a reading interaction (open, read, annotate, etc.).
- [x] `GET /api/v1/knowledge/reading-stats` — current; source `/backend/app/api/v1/knowledge.py:80`; handler `get_reading_stats` — Get reading statistics.

### Local

Exposure: Private user upload.

- [x] `POST /api/v1/local/batch-upload` — current; source `/backend/app/api/v1/local_pdf.py:73`; handler `batch_upload_pdfs` — Upload a ZIP archive of PDFs for batch ingestion. Extracts all .pdf files from the ZIP, deduplicates, and queues each for MinerU parsing. Returns summary with counts a...
- [x] `POST /api/v1/local/deduplicate` — current; source `/backend/app/api/v1/local_pdf.py:178`; handler `check_duplicates` — Scan the library for duplicate papers. Finds duplicates by DOI exact match and title exact match. Returns groups of duplicate papers.
- [x] `GET /api/v1/local/library` — current; source `/backend/app/api/v1/local_pdf.py:128`; handler `list_local_papers` — List papers imported from local PDFs, scoped to the current user.
- [x] `GET /api/v1/local/library/stats` — current; source `/backend/app/api/v1/local_pdf.py:197`; handler `library_stats` — Get statistics about the paper library.
- [x] `POST /api/v1/local/upload` — current; source `/backend/app/api/v1/local_pdf.py:21`; handler `upload_single_pdf` — Upload a single PDF file for ingestion. The PDF is stored, mirrored to a MinerU-accessible URL, and queued for MinerU parsing automatically. Returns the paper ID and i...

### Openalex

Exposure: Public discovery / Agent information service.

- [x] `POST /api/v1/openalex/graph` — current; source `/backend/app/api/v1/openalex.py:255`; handler `build_citation_graph` — Given a list of selected OpenAlex paper IDs, fetch their full citation network: - The selected papers themselves (tagged is_origin=True) - All papers they reference (t...
- [x] `GET /api/v1/openalex/search` — current; source `/backend/app/api/v1/openalex.py:155`; handler `openalex_search` — Search OpenAlex, rank results by similarity to the focal paper, and return the citation-edge graph between the top results.

### Paper Qa

Exposure: Agent information service.

- [x] `POST /api/v1/paper-qa/{paper_id}/ask` — current; source `/backend/app/api/v1/paper_qa.py:40`; handler `ask_paper` — Answer a question about a paper using RAG (embed → recall → rerank → LLM).
- [x] `POST /api/v1/paper-qa/{paper_id}/ask/stream` — current; source `/backend/app/api/v1/paper_qa.py:66`; handler `ask_paper_stream` — Stream-answer a question about a paper using SSE (embed → recall → rerank → stream LLM).
- [x] `POST /api/v1/paper-qa/{paper_id}/prepare` — current; source `/backend/app/api/v1/paper_qa.py:33`; handler `prepare_paper` — Trigger (or reprioritize) the embedding pipeline for a paper.
- [x] `GET /api/v1/paper-qa/{paper_id}/status` — current; source `/backend/app/api/v1/paper_qa.py:26`; handler `get_embedding_status` — Get the embedding pipeline status for a paper.

### Papers

Exposure: Agent information service / User workspace.

- [x] `GET /api/v1/papers` — current; source `/backend/app/api/v1/papers.py:154`; handler `list_papers` — List papers with pagination.
- [x] `POST /api/v1/papers/batch-import` — current; source `/backend/app/api/v1/papers.py:80`; handler `batch_import_papers` — Import multiple papers. Each is queued for async processing.
- [x] `POST /api/v1/papers/deduplicate` — current; source `/backend/app/api/v1/papers.py:486`; handler `deduplicate_library` — Scan the library for potential duplicate papers (DOI, arXiv ID, title fuzzy match).
- [x] `POST /api/v1/papers/import` — current; source `/backend/app/api/v1/papers.py:50`; handler `import_paper` — Import a single paper by identifier (DOI, arXiv ID, PMID, or URL). Queues the paper for full ingestion pipeline: discovery → dedup → enrich → PDF → parse → index.
- [x] `POST /api/v1/papers/import-url` — current; source `/backend/app/api/v1/content.py:249`; handler `import_from_url` — Import a paper from URL using MinerU for content extraction. Creates a new paper record and extracts content as markdown. Raises HTTP 502 if MinerU extraction fails.
- [x] `POST /api/v1/papers/resolve-arxiv` — current; source `/backend/app/api/v1/papers.py:113`; handler `resolve_papers_by_arxiv` — Resolve DeepXiv arXiv IDs to local paper IDs when the paper already exists. Dashboard and discovery surfaces use this to prefer the local analysis page over the raw De...
- [x] `DELETE /api/v1/papers/{paper_id}` — current; source `/backend/app/api/v1/papers.py:267`; handler `delete_paper` — Soft-delete a paper.
- [x] `GET /api/v1/papers/{paper_id}` — current; source `/backend/app/api/v1/papers.py:207`; handler `get_paper` — Get full paper details by ID.
- [x] `POST /api/v1/papers/{paper_id}/ask` — current; source `/backend/app/api/v1/ragflow.py:86`; handler `ask_paper` — Ask a bounded question against a single synced paper.
- [x] `GET /api/v1/papers/{paper_id}/content` — current; source `/backend/app/api/v1/content.py:183`; handler `get_paper_content` — Get paper content as markdown + structured metadata. Returns the full markdown text, sections, and provenance.
- [x] `GET /api/v1/papers/{paper_id}/deep-analysis` — current; source `/backend/app/api/v1/content.py:501`; handler `get_deep_analysis` — Return deep LLM analysis for a paper.
- [x] `GET /api/v1/papers/{paper_id}/deep-analysis-zh` — current; source `/backend/app/api/v1/content.py:648`; handler `get_deep_analysis_zh` — Return Chinese translation of deep analysis for a paper.
- [x] `GET /api/v1/papers/{paper_id}/export` — current; source `/backend/app/api/v1/papers.py:369`; handler `export_paper_citation` — Export citation for a single paper.
- [x] `GET /api/v1/papers/{paper_id}/import-status` — current; source `/backend/app/api/v1/content.py:755`; handler `get_import_status` — Return current ingestion status for a paper. Clients can poll this after POST /papers/import-url to track progress. Status values: 'pending', 'importing', 'parsed', 'r...
- [x] `GET /api/v1/papers/{paper_id}/labels` — current; source `/backend/app/api/v1/content.py:421`; handler `get_paper_labels` — Return existing taxonomy labels for a paper (does not trigger LLM call).
- [x] `POST /api/v1/papers/{paper_id}/labels` — current; source `/backend/app/api/v1/content.py:453`; handler `generate_paper_labels` — Generate (or regenerate) taxonomy labels for a paper via LLM. Uses full text when available, falls back to abstract. Set ?force=true to re-label an already-labeled paper.
- [x] `GET /api/v1/papers/{paper_id}/links` — current; source `/backend/app/api/v1/content.py:725`; handler `get_paper_links` — Return AI-fetched supplementary links for a paper.
- [x] `GET /api/v1/papers/{paper_id}/overview-image` — current; source `/backend/app/api/v1/content.py:528`; handler `get_overview_image` — Return the 一图速览 overview image record for a paper.
- [x] `POST /api/v1/papers/{paper_id}/overview-image` — current; source `/backend/app/api/v1/content.py:602`; handler `generate_overview_image` — Manually trigger 一图速览 poster generation (or regeneration with ?force=true). Under normal flow this runs automatically after deep analysis. Uses paper.deep_analysis["an...
- [x] `GET /api/v1/papers/{paper_id}/reading-status` — current; source `/backend/app/api/v1/papers.py:463`; handler `get_reading_status` — Get current reading status for a paper.
- [x] `PATCH /api/v1/papers/{paper_id}/reading-status` — current; source `/backend/app/api/v1/papers.py:295`; handler `update_reading_status` — Update per-user reading status for a paper.
- [x] `POST /api/v1/papers/{paper_id}/reparse` — current; source `/backend/app/api/v1/content.py:334`; handler `reparse_paper` — Re-parse an existing paper via MinerU. Uses the paper's stored URL or a provided override URL. Auto-detects is_html from stored URL metadata if not explicitly set.
- [x] `GET /api/v1/papers/{paper_id}/tags` — current; source `/backend/app/api/v1/papers.py:352`; handler `get_paper_tags` — List all tags on a paper (user-scoped).
- [x] `DELETE /api/v1/papers/{paper_id}/tags/{tag_id}` — current; source `/backend/app/api/v1/papers.py:337`; handler `remove_tag_from_paper` — Remove a tag from a paper.
- [x] `POST /api/v1/papers/{paper_id}/tags/{tag_id}` — current; source `/backend/app/api/v1/papers.py:320`; handler `add_tag_to_paper` — Add a tag to a paper.
- [x] `GET /api/v1/papers/{paper_id}/versions` — current; source `/backend/app/api/v1/papers.py:397`; handler `get_paper_versions` — Return version history for a paper from raw_metadata provenance markers.

### Quality

Exposure: Agent information service.

- [x] `GET /api/v1/quality/papers/{paper_id}/metadata-score` — current; source `/backend/app/api/v1/quality.py:21`; handler `get_metadata_score` — Return the metadata completeness score for a paper.
- [x] `GET /api/v1/quality/papers/{paper_id}/report` — current; source `/backend/app/api/v1/quality.py:45`; handler `get_quality_report` — Return the combined quality report for a paper.
- [x] `GET /api/v1/quality/papers/{paper_id}/reproducibility` — current; source `/backend/app/api/v1/quality.py:33`; handler `get_reproducibility` — Return reproducibility signals for a paper.

### Ragflow

Exposure: Internal integration / Agent information service.

- [x] `POST /api/v1/ragflow/eval/benchmark/compare` — current; source `/backend/app/api/v1/evaluation.py:124`; handler `run_comparison` — Run 4-path comparison for retrieval quality.
- [x] `POST /api/v1/ragflow/eval/benchmark/run` — current; source `/backend/app/api/v1/evaluation.py:86`; handler `run_benchmark` — Run retrieval benchmark against the gold corpus.
- [x] `GET /api/v1/ragflow/eval/benchmark/status` — current; source `/backend/app/api/v1/evaluation.py:74`; handler `benchmark_status` — Check if the gold benchmark corpus is available.
- [x] `POST /api/v1/ragflow/eval/grounding-check` — current; source `/backend/app/api/v1/evaluation.py:50`; handler `check_grounding` — Check how well an answer is grounded in its sources.
- [x] `POST /api/v1/ragflow/eval/metrics/reset` — current; source `/backend/app/api/v1/evaluation.py:187`; handler `reset_metrics` — Reset all accumulated metrics.
- [x] `GET /api/v1/ragflow/eval/metrics/summary` — current; source `/backend/app/api/v1/evaluation.py:68`; handler `metrics_summary` — Get latency/cost dashboard summary.
- [x] `POST /api/v1/ragflow/eval/record-metric` — current; source `/backend/app/api/v1/evaluation.py:56`; handler `record_metric` — Record an operation metric for observability.
- [x] `POST /api/v1/ragflow/query/route` — current; source `/backend/app/api/v1/ragflow.py:180`; handler `routed_query` — Classify and route a query to the best retrieval backend.
- [x] `GET /api/v1/ragflow/sync/status` — current; source `/backend/app/api/v1/ragflow.py:102`; handler `get_sync_status` — Return RAGFlow health, mapping counts, and freshness configuration.
- [x] `POST /api/v1/ragflow/sync/trigger` — current; source `/backend/app/api/v1/ragflow.py:137`; handler `trigger_sync` — Queue a paper or collection sync task.

### Researchers

Exposure: Agent information service.

- [x] `GET /api/v1/researchers/emerging` — current; source `/backend/app/api/v1/researchers.py:31`; handler `emerging_authors` — Rising-star authors — earliest library paper within window, ranked by citation count. Identifies authors whose earliest publication in our library is within *recent_ye...
- [x] `GET /api/v1/researchers/network` — current; source `/backend/app/api/v1/researchers.py:143`; handler `global_network` — Global co-authorship network over the most prolific library authors. All *top_k* authors are always returned as nodes. Edges are drawn only when two authors share ≥ *m...
- [x] `POST /api/v1/researchers/{author_id}/enrich` — current; source `/backend/app/api/v1/researchers.py:60`; handler `enrich_author` — Fetch and persist author metadata from Semantic Scholar. Matching priority: 1. Existing semantic_scholar_id → direct fetch 2. ORCID match among search results 3. Name...
- [x] `GET /api/v1/researchers/{author_id}/network` — current; source `/backend/app/api/v1/researchers.py:113`; handler `author_ego_network` — Co-authorship ego-network centered on a specific author. Returns all co-authors who have shared papers with this author in the local library, plus the edges between th...
- [x] `GET /api/v1/researchers/{author_id}/profile` — current; source `/backend/app/api/v1/researchers.py:91`; handler `get_author_profile` — Full author profile including per-year publication timeline and top papers. Returns all papers for this author in the local library, not global stats. Use *openalex_id...

### Resolve

Exposure: Agent information service.

- [x] `POST /api/v1/resolve` — current; source `/backend/app/api/v1/resolve.py:27`; handler `resolve_identifier` — Resolve DOI, arXiv ID, PMID, PMCID, OpenAlex ID, Semantic Scholar ID, URL, or title into local paper matches, external candidates, duplicate confidence, import status, and recommended action.

### Search

Exposure: Agent information service.

- [x] `GET /api/v1/search` — current; source `/backend/app/api/v1/search.py:16`; handler `search_papers` — Search papers using keyword, semantic, or hybrid mode. - **keyword**: Fast, typo-tolerant full-text search via Meilisearch - **semantic**: Meaning-based search via SPE...
- [x] `GET /api/v1/search/browse` — current; source `/backend/app/api/v1/search.py:98`; handler `browse_papers` — Browse latest papers as a discovery feed (no query required).
- [x] `GET /api/v1/search/health` — current; source `/backend/app/api/v1/search.py:136`; handler `search_health` — Check availability of search backend services.

### Sse

Exposure: Notifications.

- [x] `GET /api/v1/sse` — current; source `/backend/app/api/v1/sse.py:85`; handler `event_stream` — Open an SSE stream for real-time paper and alert notifications. Events pushed: - `paper.indexed` — a new paper finished the ingest pipeline - `alert.matched` — an aler...
- [x] `GET /api/v1/sse/recent` — current; source `/backend/app/api/v1/sse.py:123`; handler `recent_events` — Return recent audit log entries as a substitute for SSE history replay. Clients can call this on reconnect to catch up on missed events.

### System

Exposure: System health.

- [x] `GET /` — current; source `/backend/app/main.py:934`; handler `root` — Simple root entrypoint so the backend doesn't look broken in dev.

### Tags

Exposure: User workspace.

- [x] `GET /api/v1/tags` — current; source `/backend/app/api/v1/tags.py:39`; handler `list_tags` — List all tags with paper counts for the current user.
- [x] `POST /api/v1/tags` — current; source `/backend/app/api/v1/tags.py:14`; handler `create_tag` — Create a new tag.
- [x] `DELETE /api/v1/tags/{tag_id}` — current; source `/backend/app/api/v1/tags.py:90`; handler `delete_tag` — Delete a tag.
- [x] `GET /api/v1/tags/{tag_id}` — current; source `/backend/app/api/v1/tags.py:49`; handler `get_tag` — Get a single tag.
- [x] `PUT /api/v1/tags/{tag_id}` — current; source `/backend/app/api/v1/tags.py:69`; handler `update_tag` — Update a tag.

### Translate

Exposure: Agent information service.

- [x] `POST /api/v1/translate` — current; source `/backend/app/api/v1/translate.py:58`; handler `translate_text` — Translate text via the NVIDIA LLM translation API. - **en2zh** (default): English → Chinese - **zh2en**: Chinese → English - **auto**: same as en2zh If paper_id and fi...

### Trends

Exposure: Public discovery / Agent information service.

- [x] `GET /api/v1/trends/emerging-authors` — current; source `/backend/app/api/v1/trends.py:144`; handler `emerging_authors` — **Deprecated** — use `GET /api/v1/researchers/emerging` for the canonical, typed response and richer author profile data. This endpoint delegates to the same Researche...
- [x] `GET /api/v1/trends/ext/author/{author_id}/direction-change` — current; source `/backend/app/api/v1/trend_ext.py:50`; handler `get_researcher_direction_change` — Compare older vs newer keyword windows for a researcher.
- [x] `GET /api/v1/trends/ext/expert-finder` — current; source `/backend/app/api/v1/trend_ext.py:29`; handler `get_expert_finder` — Find authors whose papers match all requested keywords.
- [x] `GET /api/v1/trends/ext/topic-evolution` — current; source `/backend/app/api/v1/trend_ext.py:15`; handler `get_topic_evolution` — Return yearly counts for the most frequent keywords.
- [x] `GET /api/v1/trends/ext/venue-ranking` — current; source `/backend/app/api/v1/trend_ext.py:40`; handler `get_venue_ranking` — Rank venues by citation performance.
- [x] `GET /api/v1/trends/hot-keywords` — current; source `/backend/app/api/v1/trends.py:72`; handler `hot_keywords` — Discover hot keywords by frequency growth rate. Ranks keywords by year-over-year growth in paper count. Includes per-year breakdown and trend direction.
- [x] `GET /api/v1/trends/keywords/cooccurrence` — current; source `/backend/app/api/v1/trends.py:113`; handler `keyword_cooccurrence` — Keyword co-occurrence graph edges. Returns pairs of keywords that appear together in papers, sorted by co-occurrence count. Useful for thematic bridging discovery (§79).
- [x] `GET /api/v1/trends/keywords/timeseries` — current; source `/backend/app/api/v1/trends.py:91`; handler `keyword_timeseries` — Year-by-year paper counts for specific keywords. Pass multiple keywords as comma-separated list to compare trends. Example: ?keywords=transformer,attention,BERT
- [x] `GET /api/v1/trends/sleeping-beauties` — current; source `/backend/app/api/v1/trends.py:184`; handler `sleeping_beauties_alias` — Alias for /sleeping-papers (backward compatibility).
- [x] `GET /api/v1/trends/sleeping-papers` — current; source `/backend/app/api/v1/trends.py:167`; handler `sleeping_papers` — Find 'sleeping beauty' papers: old papers gaining recent attention. Identifies papers published >5 years ago, ranked by proxy score (citation_count / sqrt(years_old))....
- [x] `GET /api/v1/trends/topics` — current; source `/backend/app/api/v1/trends.py:30`; handler `list_topics` — List discovered research topics with paper counts and trend direction.
- [x] `POST /api/v1/trends/topics/refresh` — current; source `/backend/app/api/v1/trends.py:55`; handler `refresh_topics` — Re-run BERTopic clustering on all paper abstracts (admin). This is computationally expensive and should be run sparingly. Requires at least 20 papers with abstracts.
- [x] `GET /api/v1/trends/topics/{topic_id}` — current; source `/backend/app/api/v1/trends.py:42`; handler `get_topic` — Get topic detail with keywords and representative papers.

### Users

Exposure: User private.

- [x] `GET /api/v1/users/me/preferences` — current; source `/backend/app/api/v1/users.py:114`; handler `get_preferences` — Return current user's preferences.
- [x] `PUT /api/v1/users/me/preferences` — current; source `/backend/app/api/v1/users.py:124`; handler `update_preferences` — Replace current user's preferences.

### Workspaces

Exposure: Agent information service / User workspace.

- [x] `POST /api/v1/workspaces/{collection_id}/ask` — current; source `/backend/app/api/v1/ragflow.py:53`; handler `ask_workspace` — Ask a bounded question against a synced workspace collection.
- [x] `GET /api/v1/workspaces/{collection_id}/evidence` — current; source `/backend/app/api/v1/ragflow.py:69`; handler `get_workspace_evidence` — Return raw retrieval chunks for a workspace question.
- [x] `POST /api/v1/workspaces/{collection_id}/synthesize` — current; source `/backend/app/api/v1/ragflow.py:200`; handler `synthesize_topic` — Synthesize a structured overview for a curated topic collection.

### Writing

Exposure: User workspace / Agent writing service.

- [x] `POST /api/v1/writing/annotated-bibliography` — current; source `/backend/app/api/v1/writing.py:200`; handler `generate_annotated_bibliography` — Generate an annotated bibliography for selected papers. Each entry includes: citation, summary, evaluation, and relevance note.
- [x] `GET /api/v1/writing/documents` — current; source `/backend/app/api/v1/writing.py:66`; handler `list_writing_documents` — List all writing documents for the current user.
- [x] `POST /api/v1/writing/documents` — current; source `/backend/app/api/v1/writing.py:76`; handler `create_writing_document` — Create a new empty writing document.
- [x] `DELETE /api/v1/writing/documents/{document_id}` — current; source `/backend/app/api/v1/writing.py:120`; handler `delete_writing_document` — Soft-delete a user-owned writing document.
- [x] `GET /api/v1/writing/documents/{document_id}` — current; source `/backend/app/api/v1/writing.py:86`; handler `get_writing_document` — Load a single user-owned writing document.
- [x] `PATCH /api/v1/writing/documents/{document_id}` — current; source `/backend/app/api/v1/writing.py:100`; handler `update_writing_document` — Update a user-owned writing document.
- [x] `POST /api/v1/writing/gap-analysis` — current; source `/backend/app/api/v1/writing.py:231`; handler `analyze_research_gaps` — Identify research gaps from literature relative to a research question. Returns structured analysis: well-covered areas, partially addressed, unexplored gaps, methodol...
- [x] `POST /api/v1/writing/images` — current; source `/backend/app/api/v1/writing.py:133`; handler `upload_writing_image` — Upload a writing image via the configured OSS image host.
- [x] `POST /api/v1/writing/rebuttal` — current; source `/backend/app/api/v1/writing.py:263`; handler `draft_rebuttal` — Draft a point-by-point rebuttal to reviewer comments. Generates professional, diplomatic responses to each concern.
- [x] `POST /api/v1/writing/related-work` — current; source `/backend/app/api/v1/writing.py:163`; handler `generate_related_work` — Generate a Related Work section from selected papers. Supports three writing styles: - **narrative**: flowing prose connecting papers - **thematic**: grouped by resear...

## Newly Implemented API Surface

Exposure: Agent information service unless the endpoint name explicitly indicates API management, subscriptions, webhooks, usage, or user workspace.

These entries were derived from `docs/memo/API.md` and are now implemented through Kaleidoscope-owned JSON routes. They still need ongoing hardening for auth scopes, rate limits, and typed response models where noted in the validation pass.

### Benchmarks

- [x] `POST /api/v1/benchmarks/extract` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:608`

### Citations

- [x] `POST /api/v1/citations/intent-classify` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:422`

### Claims

- [x] `POST /api/v1/claims/verify` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:614`

### Discovery

- [x] `GET /api/v1/discovery/delta?since=...` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:627`

### Evidence

- [x] `ANY /api/v1/evidence/*` — current; covered by concrete JSON routes `POST /api/v1/evidence/search` and `POST /api/v1/evidence/packs`; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:675`
- [x] `POST /api/v1/evidence/packs` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:590`
- [x] `POST /api/v1/evidence/search` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:695`

### Exports

- [x] `POST /api/v1/exports/jsonl` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:632`

### Extract

- [x] `POST /api/v1/extract/claims/batch` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:363`
- [x] `POST /api/v1/extract/experiments/batch` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:364`
- [x] `POST /api/v1/extract/figures/batch` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:365`

### Labs

- [x] `GET /api/v1/labs/search` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:658`

### Literature

- [x] `POST /api/v1/literature/consensus-map` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:652`
- [x] `POST /api/v1/literature/contradiction-map` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:396`
- [x] `POST /api/v1/literature/minimal-reading-set` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:397`
- [x] `POST /api/v1/literature/plan-review` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:640`
- [x] `POST /api/v1/literature/related-work-pack` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:395`
- [x] `POST /api/v1/literature/research-timeline` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:398`
- [x] `POST /api/v1/literature/review-map` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:394`

### Papers

- [x] `GET /api/v1/papers/{paper_id}/assets` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:235`
- [x] `GET /api/v1/papers/{paper_id}/citation-contexts` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:601`
- [x] `GET /api/v1/papers/{paper_id}/citations/context` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:421`
- [x] `GET /api/v1/papers/{paper_id}/code-and-data` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:622`
- [x] `GET /api/v1/papers/{paper_id}/figures` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:620`
- [x] `GET /api/v1/papers/{paper_id}/references` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:420`
- [x] `GET /api/v1/papers/{paper_id}/sections` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:233`
- [x] `GET /api/v1/papers/{paper_id}/tables` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:621`

### Quality

- [x] `POST /api/v1/quality/batch` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:366`

### Reproducibility

- [x] `POST /api/v1/reproducibility/dossier` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:663`

### Researchers

- [x] `GET /api/v1/researchers/{id}/global-profile` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:657`

### Review

- [x] `POST /api/v1/review/screen` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:646`

### Search

- [x] `POST /api/v1/search/federated` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:687`

### Subscriptions

- [x] `ANY /api/v1/subscriptions/*` — current; covered by search subscription CRUD and SSE events; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:681`
- [x] `GET /api/v1/subscriptions/events` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:471`
- [x] `POST /api/v1/subscriptions/searches` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:470`

### Translate

- [x] `POST /api/v1/translate/evidence-pack` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:509`
- [x] `POST /api/v1/translate/papers/batch` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:508`

### Usage

- [x] `GET /api/v1/usage/current` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:542`
- [x] `GET /api/v1/usage/history?days=30` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:543`

### Webhooks

- [x] `ANY /api/v1/webhooks/*` — current; covered by public webhook list/create/test/secret-rotation routes; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:681`
- [x] `POST /api/v1/webhooks/test` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:472`
- [x] `POST /api/v1/webhooks/{id}/rotate-secret` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:473`

### Workspaces

- [x] `POST /api/v1/workspaces/{collection_id}/ask-local` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:583`

### Writing

- [x] `POST /api/v1/writing/citation-check` — current; source `/backend/app/api/v1/agent_services.py`; design source `/docs/memo/API.md:494`

## First Optimization Queue

- [x] DeepXIV preview parity: add `characters` query parameter to `GET /api/v1/deepxiv/papers/{arxiv_id}/preview`.
- [x] DeepXIV retrieve parity: add `POST /api/v1/deepxiv/retrieve` with JSON request body for search/retrieve parameters.
- [x] DeepXIV PMC parity: add `GET /api/v1/deepxiv/pmc/{pmc_id}/json` alias for full JSON.
- [x] DeepXIV usage parity: add `GET /api/v1/deepxiv/usage?days={n}` with typed JSON when `DEEPXIV_TOKEN` is not configured.
- [x] Local workspace RAG fallback: route collection Q&A through local embeddings when RAGFlow is disabled.
- [x] Agent manifest: add `GET /api/v1/agent/manifest` with tool schemas, scopes, costs, and examples.
- [x] Universal resolver: add `POST /api/v1/resolve` for DOI/arXiv/PMID/PMCID/OpenAlex/Semantic Scholar/URL/title.
- [x] Job API: add `/api/v1/jobs/*` for ingestion, parsing, embedding, analysis, sync, translation, and image generation lifecycle.
