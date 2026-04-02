# Admin Console Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a real admin console that exposes the full backend API inventory, live system probes, and manual operator controls.

**Architecture:** The frontend will derive the route catalog from the backend OpenAPI schema, then layer curated health probes and operator actions on top. The page stays frontend-driven so the API inventory always reflects the running backend, while existing backend health endpoints remain the source of truth for runtime status.

**Tech Stack:** Nuxt 3, Vue 3, TypeScript, ofetch via `$fetch`, existing Ks UI components, Vitest, Playwright

---

### Task 1: Create the admin data model

**Files:**
- Create: `frontend/app/composables/useAdminConsole.ts`

1. Define normalized OpenAPI types and route grouping helpers.
2. Add catalog loading from `/api/openapi.json`.
3. Add live probes for `/health`, `/health/services`, `/api/v1/search/health`, `/api/v1/ragflow/sync/status`, `/api/v1/analytics/data-coverage`.
4. Add generic endpoint runner with status, latency, and parsed response state.

### Task 2: Build admin UI components

**Files:**
- Create: `frontend/app/components/admin/AdminHealthDeck.vue`
- Create: `frontend/app/components/admin/AdminQuickActions.vue`
- Create: `frontend/app/components/admin/AdminApiRegistry.vue`
- Create: `frontend/app/components/admin/AdminEndpointRunner.vue`

1. Build reusable presentational components around the normalized admin data.
2. Match the editorial UI system already used elsewhere in the app.
3. Keep mutating operations opt-in through explicit buttons.

### Task 3: Add the `/admin` page

**Files:**
- Create: `frontend/app/pages/admin.vue`
- Modify: `frontend/app/components/layout/AppSidebar.vue`
- Modify: `frontend/app/composables/useTranslation.ts`

1. Add the page shell and wire it to the new composable.
2. Expose summary counts, filters, and endpoint selection.
3. Rename the sidebar destination from a settings placeholder to an actual admin label.

### Task 4: Add focused tests

**Files:**
- Create: `frontend/app/composables/useAdminConsole.test.ts`
- Modify: `frontend/tests/smoke.spec.ts`

1. Unit test the OpenAPI normalization and grouping logic.
2. Extend smoke coverage to assert the admin page renders core console sections.

### Task 5: Verify

**Files:**
- No code changes

1. Run `pnpm test` in `frontend`
2. Run `pnpm lint` in `frontend`
3. Run any targeted checks needed for touched files
