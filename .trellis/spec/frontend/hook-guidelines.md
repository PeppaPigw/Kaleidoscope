# Hook Guidelines (Composables)

> Data fetching and composable patterns for Kaleidoscope frontend (Nuxt 3).

---

## Data Fetching — Nuxt Built-in

All server data fetching uses **Nuxt's `useFetch` / `useAsyncData`** (replaces TanStack Query). Backend is FastAPI at `NUXT_PUBLIC_API_URL`.

```typescript
// composables/usePapers.ts

// Fetch paper by ID
export function usePaper(paperId: MaybeRef<string>) {
  return useFetch(() => `/api/v1/papers/${toValue(paperId)}`, {
    key: `paper-${toValue(paperId)}`,
  })
}

// Search papers
export function useSearchPapers(query: Ref<SearchQuery>) {
  return useFetch('/api/v1/search', {
    method: 'POST',
    body: query,
    key: computed(() => `search-${JSON.stringify(toValue(query))}`),
    watch: [query],
  })
}

// Import paper (mutation)
export function useImportPaper() {
  const importing = ref(false)
  const error = ref<Error | null>(null)

  async function importPaper(req: PaperImportRequest) {
    importing.value = true
    error.value = null
    try {
      const result = await $fetch<Paper>('/api/v1/papers/import', {
        method: 'POST',
        body: req,
      })
      // Invalidate related caches
      refreshNuxtData('papers')
      return result
    } catch (e) {
      error.value = e as Error
      throw e
    } finally {
      importing.value = false
    }
  }

  return { importPaper, importing, error }
}
```

---

## Key Pattern: `useFetch` vs `$fetch`

| Use Case | Tool | When |
|----------|------|------|
| Page data loading | `useFetch` / `useAsyncData` | SSR-compatible, cached, reactive |
| User-triggered mutations | `$fetch` | Imports, saves, deletes — imperative actions |
| Background polling | `useFetch` with `watch` | Monitoring, job status |

```typescript
// ✅ Good — SSR data fetching with useFetch
const { data: papers } = await useFetch('/api/v1/papers')

// ✅ Good — mutation with $fetch
async function savePaper(paper: Paper) {
  await $fetch(`/api/v1/papers/${paper.id}`, { method: 'PATCH', body: paper })
  refreshNuxtData(`paper-${paper.id}`)
}

// ❌ Bad — manual fetch in onMounted
onMounted(async () => {
  const res = await fetch('/api/v1/papers')
  papers.value = await res.json()
})
```

---

## Feature Composables

### Search with Debounce + Claim Mode

```typescript
// composables/useSearch.ts
export function useSearch() {
  const query = ref('')
  const mode = ref<'hybrid' | 'semantic' | 'keyword' | 'claim'>('hybrid')
  const filters = ref<SearchFilters>({})

  const debouncedQuery = refDebounced(query, 300)

  const searchBody = computed<SearchQuery>(() => ({
    q: debouncedQuery.value,
    mode: mode.value,
    filters: filters.value,
    page: 1,
    per_page: 20,
  }))

  const { data: results, status } = useFetch('/api/v1/search', {
    method: 'POST',
    body: searchBody,
    watch: [searchBody],
    immediate: false,
  })

  return { query, mode, filters, results, status }
}
```

### Reader State

```typescript
// composables/useReader.ts
export function useReader(paperId: MaybeRef<string>) {
  const { data: paper } = usePaper(paperId)

  const readingMode = ref<'focus' | 'evidence' | 'methods' | 'skim'>('focus')
  const highlightLayers = ref<SemanticLayer[]>(['claims', 'results'])
  const annotations = ref<Annotation[]>([])
  const readingProgress = ref(0)

  // Quote-to-Draft bridge
  function sendQuoteToDraft(selection: TextSelection) {
    const evidence: EvidenceCard = {
      text: selection.text,
      source: toValue(paperId),
      page: selection.page,
      section: selection.section,
      timestamp: new Date().toISOString(),
    }
    // Navigate to writing with evidence in query
    navigateTo({
      path: '/writing',
      query: { evidence: JSON.stringify(evidence) },
    })
  }

  return {
    paper, readingMode, highlightLayers,
    annotations, readingProgress, sendQuoteToDraft,
  }
}
```

### Workspace Management

```typescript
// composables/useWorkspace.ts
export function useWorkspace(workspaceId: MaybeRef<string>) {
  const { data: workspace } = useFetch(
    () => `/api/v1/workspaces/${toValue(workspaceId)}`
  )

  const { data: corpus } = useFetch(
    () => `/api/v1/workspaces/${toValue(workspaceId)}/corpus`
  )

  async function addToCorpus(paperIds: string[], shelf: CorpusShelf) {
    await $fetch(`/api/v1/workspaces/${toValue(workspaceId)}/corpus`, {
      method: 'POST',
      body: { paper_ids: paperIds, shelf },
    })
    refreshNuxtData(`workspace-corpus-${toValue(workspaceId)}`)
  }

  return { workspace, corpus, addToCorpus }
}
```

---

## Provenance Composable

```typescript
// composables/useProvenance.ts
export function useProvenance() {
  const isOpen = ref(false)
  const currentField = ref<ProvenanceTarget | null>(null)

  function showProvenance(target: ProvenanceTarget) {
    currentField.value = target
    isOpen.value = true
  }

  const { data: provenance } = useFetch(
    () => currentField.value
      ? `/api/v1/provenance/${currentField.value.entityType}/${currentField.value.entityId}/${currentField.value.field}`
      : null,
    { watch: [currentField] }
  )

  return { isOpen, currentField, provenance, showProvenance }
}
```

---

## Rules

1. **One composable per feature domain** — `usePapers.ts`, `useReader.ts`, `useWorkspace.ts`
2. **`useFetch` for reads, `$fetch` for writes** — never mix
3. **Debounce user input** — 300ms for search, 500ms for expensive operations
4. **Typed returns** — always type the return of composables
5. **`refreshNuxtData()` after mutations** — invalidate relevant cache keys
6. **`MaybeRef` for reactive params** — composables should accept both `ref` and raw values
7. **No `watch` + `fetch` manually** — use `useFetch` with `watch` option instead
