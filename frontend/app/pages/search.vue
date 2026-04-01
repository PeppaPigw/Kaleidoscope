<script setup lang="ts">
/**
 * Search Results Page
 *
 * Composes QueryRibbon, PrecisionFilters, ResultStack, ClaimSearch,
 * and CompareStrip into a unified search experience.
 *
 * Supports three search modes: keyword, semantic, and claim-first.
 */
import type { SearchMode } from '~/components/search/QueryRibbon.vue'
import type { FilterGroup } from '~/components/search/PrecisionFilters.vue'
import type { SearchResultItem } from '~/components/search/ResultStack.vue'
import type { ClaimResult } from '~/components/search/ClaimSearch.vue'
import type { CompareItem } from '~/components/search/CompareStrip.vue'
import type { SearchHit, SearchResponse } from '~/composables/useApi'

definePageMeta({
  layout: 'default',
})

const { t } = useTranslation()

useHead({
  title: 'Search — Kaleidoscope',
  meta: [
    { name: 'description', content: 'Search papers, claims, and authors with keyword, semantic, or claim-first modes.' },
  ],
})

// ─── Route query ─────────────────────────────────────────────
const route = useRoute()
const rawQ = route.query.q
const initialQuery = Array.isArray(rawQ) ? rawQ[0] ?? '' : rawQ ?? ''
const rawMode = route.query.mode
const parsedMode = Array.isArray(rawMode) ? rawMode[0] : rawMode
const validModes: SearchMode[] = ['keyword', 'semantic', 'claim']
const initialMode: SearchMode = validModes.includes(parsedMode as SearchMode)
  ? parsedMode as SearchMode
  : 'keyword'

// ─── Reactive state ──────────────────────────────────────────
const api = useApi()
const queryText = ref(initialQuery)
const searchMode = ref<SearchMode>(initialMode)
const isLoading = ref(false)
const searchResponse = ref<SearchResponse | null>(null)

// ─── Mock filter data ────────────────────────────────────────
const filterGroups = ref<FilterGroup[]>([
  {
    id: 'year',
    title: 'Year',
    options: [
      { id: 'y-2026', label: '2026', count: 14, active: false },
      { id: 'y-2025', label: '2025', count: 38, active: true },
      { id: 'y-2024', label: '2024', count: 56, active: false },
      { id: 'y-2023', label: '2023', count: 72, active: false },
    ],
  },
  {
    id: 'venue',
    title: 'Venue',
    options: [
      { id: 'v-acl', label: 'ACL', count: 22, active: false },
      { id: 'v-neurips', label: 'NeurIPS', count: 18, active: false },
      { id: 'v-emnlp', label: 'EMNLP', count: 15, active: false },
      { id: 'v-nature', label: 'Nature MI', count: 7, active: false },
    ],
  },
  {
    id: 'code',
    title: 'Code Availability',
    options: [
      { id: 'c-open', label: 'Open source', count: 45, active: false },
      { id: 'c-partial', label: 'Partial', count: 28, active: false },
      { id: 'c-none', label: 'None', count: 51, active: false },
    ],
  },
])

// ─── Search results ──────────────────────────────────────────
function createEmptySearchResponse(query = ''): SearchResponse {
  return {
    hits: [],
    total: 0,
    page: 1,
    per_page: 20,
    query,
    mode: 'hybrid',
    processing_time_ms: 0,
  }
}

function getPublishedYear(publishedAt?: string | null): number {
  if (!publishedAt) return 0
  const year = new Date(publishedAt).getFullYear()
  return Number.isNaN(year) ? 0 : year
}

function mapSearchHit(hit: SearchHit): SearchResultItem {
  return {
    id: hit.paper_id,
    title: hit.title,
    authors: hit.authors,
    venue: hit.venue ?? '',
    year: getPublishedYear(hit.published_at),
    abstract: hit.abstract ?? '',
    score: hit.score,
    tags: [],
    cited: hit.citation_count ?? 0,
    openAccess: false,
  }
}

const searchResults = computed<SearchResultItem[]>(() =>
  searchResponse.value?.hits.map(mapSearchHit) ?? [],
)
const totalResults = computed(() =>
  searchMode.value === 'claim'
    ? claimResults.length
    : (searchResponse.value?.total ?? 0),
)
const searchTimingMs = computed(() =>
  searchMode.value === 'claim'
    ? 0
    : (searchResponse.value?.processing_time_ms ?? 0),
)

// ─── Mock claim results ──────────────────────────────────────
const claimResults: ClaimResult[] = [
  {
    id: 'cl-1',
    claim: 'Citation-grounded RAG systems hallucinate citations in 18-32% of generated outputs when processing papers longer than 16K tokens.',
    confidence: 0.91,
    category: 'Empirical Finding',
    evidence: [
      {
        paperId: 'sr-2',
        paperTitle: 'RAGBench-Sci (2025)',
        stance: 'supports',
        snippet: 'Our analysis reveals a hallucination rate of 23.7% for citations in papers exceeding 16K tokens...',
      },
      {
        paperId: 'sr-5',
        paperTitle: 'When More Context Hurts (2025)',
        stance: 'supports',
        snippet: 'We observe citation accuracy degrading from 92% to 68% as context length scales from 8K to 128K tokens...',
      },
    ],
  },
  {
    id: 'cl-2',
    claim: 'Medical QA benchmark leaderboard improvements do not generalize to hospital-held clinical datasets.',
    confidence: 0.87,
    category: 'Validity Concern',
    evidence: [
      {
        paperId: 'sr-3',
        paperTitle: 'MedJudge-External (2025)',
        stance: 'supports',
        snippet: '60% of leaderboard gains on MedQA disappear when evaluated on hospital-held test sets from three institutions...',
      },
      {
        paperId: 'sr-1',
        paperTitle: 'ClaimMiner (2025)',
        stance: 'neutral',
        snippet: 'While our extraction pipeline works across domains, clinical text requires additional entity normalization...',
      },
    ],
  },
  {
    id: 'cl-3',
    claim: 'Tool-augmented agents can compensate for limited context windows in scientific question answering.',
    confidence: 0.78,
    category: 'Method Claim',
    evidence: [
      {
        paperId: 'sr-4',
        paperTitle: 'ToolChain Scholar (2025)',
        stance: 'supports',
        snippet: 'Strategic tool selection compensates for limited context in 78% of scientific QA tasks...',
      },
      {
        paperId: 'sr-5',
        paperTitle: 'When More Context Hurts (2025)',
        stance: 'contradicts',
        snippet: 'Our results suggest that even tool-augmented approaches fail when the required evidence spans multiple distant document sections...',
      },
    ],
  },
]

// ─── Compare tray ────────────────────────────────────────────
const compareItems = ref<CompareItem[]>([])
let searchRequestId = 0
let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null

async function runSearch(query: string) {
  const normalizedQuery = query.trim()
  searchRequestId += 1
  const requestId = searchRequestId

  if (!normalizedQuery || searchMode.value === 'claim') {
    searchResponse.value = createEmptySearchResponse(normalizedQuery)
    isLoading.value = false
    return
  }

  isLoading.value = true
  try {
    // Map UI mode names to backend values
    const backendMode = searchMode.value === 'keyword'
      ? 'keyword'
      : searchMode.value === 'semantic'
        ? 'semantic'
        : 'hybrid'
    const response = await api.searchPapers(normalizedQuery, {
      mode: backendMode,
      page: 1,
      per_page: 20,
    })
    if (requestId === searchRequestId) {
      searchResponse.value = response
    }
  }
  catch {
    if (requestId === searchRequestId) {
      searchResponse.value = createEmptySearchResponse(normalizedQuery)
    }
  }
  finally {
    if (requestId === searchRequestId) {
      isLoading.value = false
    }
  }
}

watch(queryText, (value) => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    void runSearch(value)
  }, 300)
}, {
  immediate: Boolean(queryText.value.trim()),
})

watch(searchMode, (mode, previousMode) => {
  if (mode === 'claim') {
    searchRequestId += 1
    isLoading.value = false
    searchResponse.value = createEmptySearchResponse(queryText.value.trim())
    return
  }
  if (previousMode === 'claim' && queryText.value.trim()) {
    void runSearch(queryText.value)
  }
})

watch(() => route.query.q, (nextQuery) => {
  const nextValue = Array.isArray(nextQuery) ? nextQuery[0] ?? '' : nextQuery ?? ''
  if (nextValue !== queryText.value) queryText.value = nextValue
})

watch(() => route.query.mode, (nextMode) => {
  const parsed = Array.isArray(nextMode) ? nextMode[0] : nextMode
  const value = validModes.includes(parsed as SearchMode) ? parsed as SearchMode : 'keyword'
  if (value !== searchMode.value) searchMode.value = value
})

onBeforeUnmount(() => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
})

// ─── Handlers ────────────────────────────────────────────────
function handleFilterToggle(groupId: string, optionId: string, active: boolean) {
  const group = filterGroups.value.find(g => g.id === groupId)
  if (group) {
    const opt = group.options.find(o => o.id === optionId)
    if (opt) opt.active = active
  }
}

function handleClearFilters() {
  for (const group of filterGroups.value) {
    for (const opt of group.options) {
      opt.active = false
    }
  }
}

async function handleSearchSubmit(query: string) {
  const normalizedQuery = query.trim()
  queryText.value = normalizedQuery
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  await runSearch(normalizedQuery)
  await navigateTo({ path: '/search', query: { q: normalizedQuery, mode: searchMode.value } })
}

function handlePaperClick(_paper: SearchResultItem) {
  // NuxtLink in ResultStack handles navigation; reserved for analytics
}

function handlePaperRead(paper: SearchResultItem) {
  navigateTo(`/reader/${paper.id}`)
}

function handlePaperSave(_paper: SearchResultItem) {
  // Will wire to workspace API
}

function handlePaperCompare(paper: SearchResultItem) {
  if (compareItems.value.length >= 4) return
  if (compareItems.value.some(c => c.id === paper.id)) return
  compareItems.value.push({
    id: paper.id,
    title: paper.title,
    venue: paper.venue,
    year: paper.year,
  })
}

function handleCompareRemove(item: CompareItem) {
  compareItems.value = compareItems.value.filter(c => c.id !== item.id)
}

function handleCompareClear() {
  compareItems.value = []
}

function handleCompareGo() {
  const ids = compareItems.value.map(c => c.id).join(',')
  navigateTo(`/synthesis?compare=${ids}`)
}

function handleClaimPaperClick(paperId: string) {
  navigateTo(`/papers/${paperId}`)
}
</script>

<template>
  <div class="ks-search">
    <KsPageHeader :title="t('search')" :subtitle="t('searchResults')" />

    <!-- Query Ribbon -->
    <SearchQueryRibbon
      v-model="queryText"
      :mode="searchMode"
      :result-count="totalResults"
      :search-time-ms="searchTimingMs"
      @update:mode="searchMode = $event"
      @submit="handleSearchSubmit"
    />

    <!-- Filters -->
    <SearchPrecisionFilters
      :filters="filterGroups"
      @filter-toggle="handleFilterToggle"
      @clear-all="handleClearFilters"
    />

    <!-- Results area -->
    <div class="ks-search__content">
      <!-- Keyword / Semantic mode -->
      <SearchResultStack
        v-if="searchMode !== 'claim'"
        :results="searchResults"
        :loading="isLoading"
        @paper-click="handlePaperClick"
        @save="handlePaperSave"
        @compare="handlePaperCompare"
        @read="handlePaperRead"
      />

      <!-- Claim-first mode -->
      <SearchClaimSearch
        v-else
        :claims="claimResults"
        :loading="isLoading"
        @paper-click="handleClaimPaperClick"
      />
    </div>

    <!-- Compare tray -->
    <SearchCompareStrip
      :items="compareItems"
      @remove="handleCompareRemove"
      @compare="handleCompareGo"
      @clear="handleCompareClear"
    />
  </div>
</template>

<style scoped>
.ks-search {
  min-height: 100vh;
  padding-bottom: 100px;
}

.ks-search__content {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px;
}
</style>
