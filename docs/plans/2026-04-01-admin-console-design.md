# Admin Console Design

**Date:** 2026-04-01

**Goal:** Add a dedicated `/admin` page that shows the full backend API surface, live system health, and operator actions so broken integrations and unavailable features are visible in one place.

## Scope

- Show the complete backend API inventory from the live OpenAPI schema instead of a hand-maintained list.
- Surface live health for the critical runtime dependencies and feature pipelines.
- Provide a safe operator panel for common actions such as reprocess and RAGFlow sync.
- Provide a generic manual endpoint runner so any API can be exercised from the admin page.

## Architecture

- The frontend admin page fetches `/api/openapi.json` and derives a normalized route catalog grouped by domain.
- Live probes reuse existing backend endpoints such as `/health`, `/health/services`, `/api/v1/search/health`, and `/api/v1/ragflow/sync/status`.
- A frontend-side endpoint runner issues arbitrary requests against the configured backend, records latency and status, and renders parsed responses or errors.
- Quick actions are curated presets over existing admin and RAGFlow endpoints so common operations remain one click away.

## UI Structure

1. Header and summary
   - Total route count
   - Number of domains
   - Probe status summary
2. Health deck
   - API server
   - Dependency services
   - Search stack
   - RAGFlow sync
   - Data coverage
3. Quick actions
   - Admin reprocess
   - RAGFlow sync trigger
   - Search a sample route again
4. API registry
   - Grouped by domain
   - Method, path, summary, tags, probeability
   - Filter by method, domain, text
5. Endpoint runner
   - Selected path and method
   - Path params, query params, JSON body
   - Response status, latency, payload

## Truthfulness Rules

- The page only marks a capability as `ok` when a real probe succeeds.
- Endpoints without a safe automatic probe are labeled as manual or unverified instead of implied healthy.
- Mutating routes are never auto-executed.

## Files Expected

- Add admin page and supporting components under `frontend/app/pages/admin.vue` and `frontend/app/components/admin/`
- Add admin composable and OpenAPI normalization helper under `frontend/app/composables/`
- Extend frontend tests to cover the admin page behavior
