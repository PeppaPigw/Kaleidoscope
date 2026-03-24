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
const queryText = ref(initialQuery)
const searchMode = ref<SearchMode>(initialMode)
const isLoading = ref(false)

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

// ─── Mock results ────────────────────────────────────────────
const searchResults: SearchResultItem[] = [
  {
    id: 'sr-1',
    title: 'ClaimMiner: Atomic Claim Extraction for Biomedical Papers with Evidence Alignment',
    authors: ['Liu, J.', 'Wang, X.', 'Chen, H.', 'Zhang, Y.'],
    venue: 'EMNLP 2025',
    year: 2025,
    abstract: 'A pipeline for decomposing biomedical papers into atomic, verifiable claims linked to supporting evidence sentences. We demonstrate that claim-level granularity improves downstream RAG and fact-checking accuracy.',
    score: 0.94,
    tags: ['Code', 'Human eval'],
    cited: 42,
    openAccess: true,
  },
  {
    id: 'sr-2',
    title: 'RAGBench-Sci: Failure Modes of Citation-Grounded Retrieval',
    authors: ['Park, S.', 'Kim, D.'],
    venue: 'ACL 2025',
    year: 2025,
    abstract: 'Systematic analysis of where citation-grounded RAG fails: hallucinated citations, partial quotes, and context window overflow. We propose a taxonomy of failure modes and a diagnostic benchmark.',
    score: 0.89,
    tags: ['Open data', 'Benchmark'],
    cited: 28,
    openAccess: true,
  },
  {
    id: 'sr-3',
    title: 'MedJudge-External: Reassessing Medical QA with Hospital-held Data',
    authors: ['Singh, R.', 'Patel, A.', 'Thompson, L.'],
    venue: 'Nature MI 2025',
    year: 2025,
    abstract: 'External validation study showing 60% of MedQA leaderboard gains disappear under hospital-held test sets, challenging the generalizability of current medical QA systems.',
    score: 0.86,
    tags: ['External eval', 'Clinical'],
    cited: 67,
    openAccess: false,
  },
  {
    id: 'sr-4',
    title: 'ToolChain Scholar: Agents under Long-Context Constraints',
    authors: ['Müller, T.', 'Garcia, C.'],
    venue: 'NeurIPS 2025',
    year: 2025,
    abstract: 'Evaluating tool-augmented scientific agents when context windows are constrained to 4K tokens. We show that strategic tool selection compensates for limited context in 78% of tasks.',
    score: 0.81,
    tags: ['Code', 'Agents'],
    cited: 19,
    openAccess: true,
  },
  {
    id: 'sr-5',
    title: 'When More Context Hurts: Failure Analysis for 128K Scientific QA',
    authors: ['Zhang, L.', 'Wu, F.', 'Li, Q.'],
    venue: 'EMNLP 2025 Findings',
    year: 2025,
    abstract: 'Documenting systematic performance drops when scaling context beyond 32K tokens in scientific QA benchmarks. Longer contexts introduce noise that degrades answer precision.',
    score: 0.76,
    tags: ['Negative result'],
    cited: 11,
    openAccess: true,
  },
]

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

function handleSearchSubmit(query: string) {
  navigateTo({ path: '/search', query: { q: query, mode: searchMode.value } })
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
      :result-count="searchMode === 'claim' ? claimResults.length : searchResults.length"
      :search-time-ms="142"
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
