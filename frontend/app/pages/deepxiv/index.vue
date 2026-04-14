<script setup lang="ts">
/**
 * DeepXiv Search — arXiv paper search with hybrid/BM25/vector modes,
 * result grid, trending sidebar, and expandable filters.
 */
import { Search, Loader2 } from 'lucide-vue-next'
import type {
  DeepXivSearchResult,
  DeepXivSearchParams,
  DeepXivTrendingPaper,
} from '~/composables/useDeepXiv'

definePageMeta({ layout: 'default', title: 'DeepXiv' })
useHead({ title: 'DeepXiv -- arXiv Paper Search' })

const { t } = useTranslation()
const { searchPapers, getTrending } = useDeepXiv()

// ── Search state ────────────────────────────────────────
const query = ref('')
const searchMode = ref<'hybrid' | 'bm25' | 'vector'>('hybrid')
const results = ref<DeepXivSearchResult[]>([])
const totalResults = ref(0)
const isSearching = ref(false)
const searchError = ref<string | null>(null)
const hasSearched = ref(false)
const filtersExpanded = ref(false)
const filters = ref<DeepXivSearchParams>({})

// ── Trending state ──────────────────────────────────────
const trendingDays = ref(7)
const trendingPapers = ref<DeepXivTrendingPaper[]>([])
const trendingLoading = ref(false)

// ── Search modes ────────────────────────────────────────
const modes = [
  { key: 'hybrid' as const, label: 'Hybrid' },
  { key: 'bm25' as const, label: 'BM25' },
  { key: 'vector' as const, label: 'Vector' },
]

// ── Actions ─────────────────────────────────────────────
async function runSearch() {
  const trimmed = query.value.trim()
  if (!trimmed) return

  isSearching.value = true
  searchError.value = null
  hasSearched.value = true

  try {
    const params: DeepXivSearchParams = {
      ...filters.value,
      search_mode: searchMode.value,
    }
    const res = await searchPapers(trimmed, params)
    results.value = res.results
    totalResults.value = res.total
  }
  catch (err) {
    searchError.value = err instanceof Error ? err.message : 'Search failed'
    results.value = []
    totalResults.value = 0
  }
  finally {
    isSearching.value = false
  }
}

function handleResultClick(result: DeepXivSearchResult) {
  navigateTo(`/deepxiv/papers/${result.arxiv_id}`)
}

function handleTrendingClick(arxivId: string) {
  navigateTo(`/deepxiv/papers/${arxivId}`)
}

async function loadTrending() {
  trendingLoading.value = true
  try {
    const res = await getTrending(trendingDays.value, 5)
    trendingPapers.value = res.papers
  }
  catch {
    trendingPapers.value = []
  }
  finally {
    trendingLoading.value = false
  }
}

watch(trendingDays, () => {
  void loadTrending()
})

onMounted(() => {
  void loadTrending()
})
</script>

<template>
  <div class="ks-deepxiv">
    <!-- Header -->
    <header class="ks-deepxiv__header">
      <h1 class="ks-deepxiv__title">DeepXiv</h1>
      <p class="ks-deepxiv__subtitle">arXiv Paper Search</p>
    </header>

    <!-- Search bar -->
    <div class="ks-deepxiv__search">
      <div class="ks-deepxiv__search-box" :class="{ 'ks-deepxiv__search-box--loading': isSearching }">
        <Search :size="18" class="ks-deepxiv__search-icon" />
        <input
          v-model="query"
          type="text"
          class="ks-deepxiv__search-input"
          placeholder="Search papers, topics, authors..."
          :disabled="isSearching"
          @keydown.enter="runSearch"
        />
        <button
          class="ks-deepxiv__search-btn"
          :disabled="isSearching || !query.trim()"
          @click="runSearch"
        >
          <Loader2 v-if="isSearching" :size="14" class="ks-deepxiv__spinner" />
          <span v-else>Search</span>
        </button>
      </div>

      <!-- Mode toggle -->
      <div class="ks-deepxiv__modes">
        <button
          v-for="mode in modes"
          :key="mode.key"
          :class="['ks-deepxiv__mode', searchMode === mode.key && 'ks-deepxiv__mode--active']"
          @click="searchMode = mode.key"
        >
          {{ mode.label }}
        </button>
      </div>

      <!-- Expandable filters -->
      <button class="ks-deepxiv__filter-toggle" @click="filtersExpanded = !filtersExpanded">
        {{ filtersExpanded ? 'Hide Filters' : 'Show Filters' }}
      </button>
      <div v-if="filtersExpanded" class="ks-deepxiv__filters">
        <DeepxivSearchFilters v-model="filters" />
      </div>
    </div>

    <!-- Error -->
    <div v-if="searchError" class="ks-deepxiv__error">
      {{ searchError }}
    </div>

    <!-- Main content -->
    <div class="ks-deepxiv__body">
      <!-- Main column -->
      <main class="ks-deepxiv__main">
        <!-- Empty state: no search yet -->
        <div v-if="!hasSearched" class="ks-deepxiv__placeholder">
          <div class="ks-deepxiv__placeholder-icon">
            <Search :size="40" />
          </div>
          <p class="ks-deepxiv__placeholder-text">
            Start by searching for papers
          </p>
          <p class="ks-deepxiv__placeholder-hint">
            Use hybrid, BM25, or vector search to find arXiv papers
          </p>
        </div>

        <!-- Loading -->
        <div v-else-if="isSearching" class="ks-deepxiv__loading">
          <Loader2 :size="24" class="ks-deepxiv__spinner" />
          <span>Searching...</span>
        </div>

        <!-- Empty results -->
        <div v-else-if="results.length === 0" class="ks-deepxiv__placeholder">
          <p class="ks-deepxiv__placeholder-text">No results found</p>
          <p class="ks-deepxiv__placeholder-hint">
            Try adjusting your query or search mode
          </p>
        </div>

        <!-- Results -->
        <template v-else>
          <div class="ks-deepxiv__results-header">
            <span class="ks-deepxiv__results-count">{{ totalResults }} results</span>
          </div>
          <div class="ks-deepxiv__results-grid">
            <DeepxivSearchResultCard
              v-for="r in results"
              :key="r.arxiv_id"
              :result="r"
              @click="handleResultClick(r)"
            />
          </div>
        </template>
      </main>

      <!-- Right sidebar: Trending -->
      <aside class="ks-deepxiv__sidebar">
        <div class="ks-deepxiv__sidebar-header">
          <h3 class="ks-deepxiv__sidebar-title">Trending</h3>
          <DeepxivDayRangeSelector v-model="trendingDays" />
        </div>

        <div v-if="trendingLoading" class="ks-deepxiv__sidebar-loading">
          <Loader2 :size="16" class="ks-deepxiv__spinner" />
          <span>Loading...</span>
        </div>

        <div v-else-if="trendingPapers.length === 0" class="ks-deepxiv__sidebar-empty">
          No trending papers
        </div>

        <ul v-else class="ks-deepxiv__trending-list">
          <li
            v-for="paper in trendingPapers"
            :key="paper.arxiv_id"
            class="ks-deepxiv__trending-item"
            @click="handleTrendingClick(paper.arxiv_id)"
          >
            <span v-if="paper.rank" class="ks-deepxiv__trending-rank">#{{ paper.rank }}</span>
            <div class="ks-deepxiv__trending-body">
              <span class="ks-deepxiv__trending-id">{{ paper.arxiv_id }}</span>
              <span
                v-if="paper.stats?.total_views"
                class="ks-deepxiv__trending-views"
              >{{ paper.stats.total_views }} views</span>
            </div>
          </li>
        </ul>

        <NuxtLink to="/deepxiv/trending" class="ks-deepxiv__sidebar-more">
          View all trending
        </NuxtLink>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.ks-deepxiv {
  max-width: 1280px;
  margin: 0 auto;
  padding: 32px 24px 64px;
  min-height: 100vh;
}

/* ── Header ──────────────────────────────────────────── */
.ks-deepxiv__header {
  margin-bottom: 28px;
}

.ks-deepxiv__title {
  font: 700 2rem / 1.1 var(--font-display, serif);
  color: var(--color-primary);
  margin: 0;
}

.ks-deepxiv__subtitle {
  font: 400 0.8125rem / 1 var(--font-sans);
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--color-secondary);
  margin: 6px 0 0;
}

/* ── Search ──────────────────────────────────────────── */
.ks-deepxiv__search {
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ks-deepxiv__search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  transition: border-color var(--duration-fast) var(--ease-smooth),
              box-shadow var(--duration-fast) var(--ease-smooth);
}

.ks-deepxiv__search-box:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary) 12%, transparent);
}

.ks-deepxiv__search-box--loading {
  opacity: 0.7;
}

.ks-deepxiv__search-icon {
  flex-shrink: 0;
  color: var(--color-primary);
}

.ks-deepxiv__search-input {
  flex: 1;
  border: none;
  outline: none;
  background: none;
  font: 400 1rem / 1.4 var(--font-sans);
  color: var(--color-text);
}

.ks-deepxiv__search-input::placeholder {
  color: var(--color-secondary);
}

.ks-deepxiv__search-input:disabled {
  opacity: 0.5;
}

.ks-deepxiv__search-btn {
  flex-shrink: 0;
  padding: 8px 20px;
  background: var(--color-primary);
  color: var(--color-bg);
  border: none;
  border-radius: 6px;
  font: 600 0.8125rem / 1 var(--font-sans);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-smooth),
              opacity var(--duration-fast) var(--ease-smooth);
}

.ks-deepxiv__search-btn:hover:not(:disabled) {
  opacity: 0.85;
}

.ks-deepxiv__search-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ── Mode toggle ─────────────────────────────────────── */
.ks-deepxiv__modes {
  display: flex;
  gap: 4px;
}

.ks-deepxiv__mode {
  padding: 6px 16px;
  border: 1px solid var(--color-border);
  background: none;
  font: 500 0.75rem / 1 var(--font-sans);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-secondary);
  cursor: pointer;
  border-radius: 4px;
  transition: border-color var(--duration-fast) var(--ease-smooth),
              color var(--duration-fast) var(--ease-smooth),
              background var(--duration-fast) var(--ease-smooth);
}

.ks-deepxiv__mode:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.ks-deepxiv__mode--active {
  border-color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
  color: var(--color-primary);
  font-weight: 600;
}

/* ── Filter toggle ───────────────────────────────────── */
.ks-deepxiv__filter-toggle {
  align-self: flex-start;
  padding: 0;
  border: none;
  background: none;
  font: 500 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  transition: color var(--duration-fast) var(--ease-smooth);
}

.ks-deepxiv__filter-toggle:hover {
  color: var(--color-primary);
}

.ks-deepxiv__filters {
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-surface);
}

/* ── Error ────────────────────────────────────────────── */
.ks-deepxiv__error {
  padding: 10px 14px;
  margin-bottom: 16px;
  border-left: 3px solid #ba1a1a;
  background: rgba(186, 26, 26, 0.06);
  font: 400 0.8125rem / 1.4 var(--font-sans);
  color: #ba1a1a;
}

/* ── Body layout ─────────────────────────────────────── */
.ks-deepxiv__body {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 28px;
  align-items: start;
}

/* ── Main column ─────────────────────────────────────── */
.ks-deepxiv__main {
  min-width: 0;
}

.ks-deepxiv__results-header {
  margin-bottom: 12px;
}

.ks-deepxiv__results-count {
  font: 500 0.6875rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-secondary);
}

.ks-deepxiv__results-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ── Placeholder / Loading ───────────────────────────── */
.ks-deepxiv__placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.ks-deepxiv__placeholder-icon {
  color: var(--color-border);
  margin-bottom: 16px;
}

.ks-deepxiv__placeholder-text {
  font: 500 1rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
  margin: 0 0 6px;
}

.ks-deepxiv__placeholder-hint {
  font: 400 0.8125rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
  opacity: 0.7;
  margin: 0;
}

.ks-deepxiv__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 60px 20px;
  font: 400 0.875rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-deepxiv__spinner {
  animation: ks-dx-spin 0.8s linear infinite;
}

@keyframes ks-dx-spin {
  to { transform: rotate(360deg); }
}

/* ── Sidebar ─────────────────────────────────────────── */
.ks-deepxiv__sidebar {
  position: sticky;
  top: 80px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
}

.ks-deepxiv__sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.ks-deepxiv__sidebar-title {
  font: 600 0.875rem / 1 var(--font-sans);
  color: var(--color-text);
  margin: 0;
}

.ks-deepxiv__sidebar-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 0;
  font: 400 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-deepxiv__sidebar-empty {
  padding: 16px 0;
  font: 400 0.8125rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
  text-align: center;
}

/* ── Trending list ───────────────────────────────────── */
.ks-deepxiv__trending-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ks-deepxiv__trending-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-smooth);
}

.ks-deepxiv__trending-item:hover {
  background: color-mix(in srgb, var(--color-primary) 6%, transparent);
}

.ks-deepxiv__trending-rank {
  flex-shrink: 0;
  font: 700 0.6875rem / 1 var(--font-mono);
  color: var(--color-primary);
  min-width: 20px;
}

.ks-deepxiv__trending-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.ks-deepxiv__trending-id {
  font: 500 0.75rem / 1.3 var(--font-mono);
  color: var(--color-text);
  word-break: break-all;
}

.ks-deepxiv__trending-views {
  font: 400 0.625rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-deepxiv__sidebar-more {
  display: block;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--color-border);
  font: 500 0.75rem / 1 var(--font-sans);
  color: var(--color-primary);
  text-decoration: none;
  text-align: center;
  transition: opacity var(--duration-fast) var(--ease-smooth);
}

.ks-deepxiv__sidebar-more:hover {
  opacity: 0.7;
}

/* ── Responsive ──────────────────────────────────────── */
@media (max-width: 860px) {
  .ks-deepxiv__body {
    grid-template-columns: 1fr;
  }

  .ks-deepxiv__sidebar {
    position: static;
  }
}
</style>
