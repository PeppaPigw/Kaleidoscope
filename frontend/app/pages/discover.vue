<script setup lang="ts">
/**
 * Discovery Explorer — powered by DeepXiv hybrid search.
 *
 * TopicsWall    — 4 curated category searches (live paper counts)
 * QueryComposer — semantic/keyword query → searchPapers()
 * FacetWall     — category, year, citation filters wired to search
 * RecommendationStream — DeepXiv results with TLDR briefs
 * VenueShelf    — local analytics categories (fallback)
 * GraphTeaser   — static concept graph teaser
 * SavedExplorations — in-session query history
 */
import type { TopicCover } from '~/components/discover/TopicsWall.vue'
import type { FacetGroup } from '~/components/discover/FacetWall.vue'
import type { RecommendedPaper } from '~/components/discover/RecommendationStream.vue'
import type { VenueItem } from '~/components/discover/VenueShelf.vue'
import type { GraphNode, GraphEdge } from '~/components/discover/GraphTeaser.vue'
import type { SavedExploration } from '~/components/discover/SavedExplorations.vue'
import type { DeepXivSearchResult, DeepXivBriefResponse } from '~/composables/useDeepXiv'

definePageMeta({ layout: 'default', title: 'Discovery Explorer' })

const route = useRoute()
const router = useRouter()

useHead({
  title: 'Discover — Kaleidoscope',
  meta: [
    { name: 'description', content: 'Explore curated research collections and discover papers with intelligent filtering.' },
  ],
})

// ── Tab state (from URL query) ────────────────────────────────
const activeTab = computed({
  get: () => (route.query.tab as string) || 'search',
  set: (val: string) => {
    router.push({ query: { ...route.query, tab: val } })
  },
})

// ── AI Assistant drawer state ──────────────────────────────────
const aiDrawerOpen = ref(false)

// Open drawer if ?agent=open in URL
watch(() => route.query.agent, (val) => {
  if (val === 'open') {
    aiDrawerOpen.value = true
    // Remove query param after opening
    router.replace({ query: { ...route.query, agent: undefined } })
  }
}, { immediate: true })

// ── Search state ──────────────────────────────────────────────
const queryText = ref('')
const searchResults = ref<DeepXivSearchResult[]>([])
const briefCache = ref<Record<string, DeepXivBriefResponse>>({})
const resultTotal = ref(0)
const offset = ref(0)
const PAGE_SIZE = 12
const isSearching = ref(false)
const isLoadingMore = ref(false)

// ── Topic covers ──────────────────────────────────────────────
const topicCovers = ref<TopicCover[]>([])
const topicsLoading = ref(true)

// ── Venue / sidebar ───────────────────────────────────────────
const venueItems = ref<VenueItem[]>([])
const venueShelfTitle = ref('Top Categories')

// ── Session history ───────────────────────────────────────────
const queryHistory = ref<SavedExploration[]>([])
let historyCounter = 0

// ── Bookmark target ───────────────────────────────────────────
const bookmarkTarget = ref<{ arxivId: string; title: string } | null>(null)

// ── Facets ────────────────────────────────────────────────────
const facetGroups = ref<FacetGroup[]>([
  {
    title: 'Year',
    options: [
      { label: '2026', count: 0, active: false },
      { label: '2025', count: 0, active: false },
      { label: '2024', count: 0, active: false },
    ],
  },
  {
    title: 'Domain',
    options: [
      { label: 'cs.AI', count: 0, active: false },
      { label: 'cs.CL', count: 0, active: false },
      { label: 'cs.CV', count: 0, active: false },
      { label: 'cs.LG', count: 0, active: false },
    ],
  },
  {
    title: 'Impact',
    options: [
      { label: 'High (50+ citations)', count: 0, active: false },
      { label: 'Any', count: 0, active: true },
    ],
  },
  {
    title: 'Search Mode',
    options: [
      { label: 'Hybrid', count: 0, active: true },
      { label: 'Semantic', count: 0, active: false },
      { label: 'Keyword', count: 0, active: false },
    ],
  },
])

// ── Graph teaser (static) ─────────────────────────────────────
const graphNodes: GraphNode[] = [
  { id: 'center', label: 'LLM Reasoning', cx: 132, cy: 76, r: 10, type: 'primary' },
  { id: 'rag', label: 'RAG', cx: 44, cy: 40, r: 6, type: 'bridge' },
  { id: 'agents', label: 'Agents', cx: 220, cy: 36, r: 6, type: 'bridge' },
  { id: 'eval', label: 'Evaluation', cx: 56, cy: 120, r: 7, type: 'primary' },
  { id: 'finetune', label: 'Fine-tuning', cx: 216, cy: 124, r: 6, type: 'bridge' },
]
const graphEdges: GraphEdge[] = [
  { from: 'center', to: 'rag' },
  { from: 'center', to: 'agents' },
  { from: 'center', to: 'eval' },
  { from: 'center', to: 'finetune' },
  { from: 'eval', to: 'rag' },
]

// ── Curated topic definitions ─────────────────────────────────
const TOPIC_DEFS = [
  {
    id: 'tc-ai',
    query: 'reasoning large language model chain of thought',
    category: 'cs.AI',
    label: 'Trending in AI',
    accent: 'teal' as const,
  },
  {
    id: 'tc-cv',
    query: 'multimodal vision language model image generation',
    category: 'cs.CV',
    label: 'Visual AI',
    accent: 'gold' as const,
  },
  {
    id: 'tc-bio',
    query: 'protein structure drug discovery generative model',
    category: 'q-bio.BM',
    label: 'Life Sciences',
    accent: 'teal' as const,
  },
  {
    id: 'tc-bench',
    query: 'benchmark evaluation leakage contamination',
    category: 'cs.LG',
    label: 'Methodology',
    accent: 'gold' as const,
  },
]

const TOPIC_SUBTITLES: Record<string, string> = {
  'tc-ai': 'Chain-of-thought, planning, and multi-step reasoning in LLMs',
  'tc-cv': 'Vision-language models, diffusion, and generative visual AI',
  'tc-bio': 'Protein folding, drug design, and biomedical AI',
  'tc-bench': 'Evaluation methodology, data contamination, and robustness',
}

// ── Derived search params from facets ─────────────────────────
const searchParams = computed(() => {
  const yearOpts = facetGroups.value.find(g => g.title === 'Year')?.options ?? []
  const activeYears = yearOpts.filter(o => o.active).map(o => o.label)
  let dateFrom: string | undefined
  let dateTo: string | undefined
  if (activeYears.length > 0) {
    const years = activeYears.map(Number).sort()
    dateFrom = `${years[0]!}-01-01`
    dateTo = `${years[years.length - 1]!}-12-31`
  }

  const domainOpts = facetGroups.value.find(g => g.title === 'Domain')?.options ?? []
  const categories = domainOpts.filter(o => o.active).map(o => o.label)

  const impactOpts = facetGroups.value.find(g => g.title === 'Impact')?.options ?? []
  const highImpact = impactOpts.find(o => o.label.startsWith('High') && o.active)
  const minCitation = highImpact ? 50 : undefined

  const modeOpts = facetGroups.value.find(g => g.title === 'Search Mode')?.options ?? []
  const activeMode = modeOpts.find(o => o.active)?.label.toLowerCase()
  const searchMode = activeMode === 'semantic' ? 'vector' : activeMode === 'keyword' ? 'bm25' : 'hybrid'

  return { dateFrom, dateTo, categories, minCitation, searchMode: searchMode as 'hybrid' | 'bm25' | 'vector' }
})

// ── Recommendation list for display ───────────────────────────
const recommendations = computed<RecommendedPaper[]>(() =>
  searchResults.value.map(r => ({
    id: r.arxiv_id,
    href: `/deepxiv/papers/${r.arxiv_id}`,
    eyebrow: r.categories[0] ?? 'arXiv',
    title: r.title,
    abstract: r.abstract ?? '',
    tldr: briefCache.value[r.arxiv_id]?.tldr ?? undefined,
    venue: r.authors.slice(0, 2).join(', '),
    score: r.score,
    tags: r.categories.slice(0, 2),
    strong: r.citations > 50,
  }))
)

// ── Helpers ───────────────────────────────────────────────────
function pushHistory(q: string) {
  if (!q.trim()) return
  const id = `se-${++historyCounter}`
  const existing = queryHistory.value.find(h => h.title === q)
  if (existing) return
  queryHistory.value = [
    { id, title: q, date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' }), pinned: false },
    ...queryHistory.value,
  ].slice(0, 8)
}

async function fetchBriefs(ids: string[]) {
  const { getPaperBrief } = useDeepXiv()
  const uncached = ids.filter(id => !briefCache.value[id])
  if (!uncached.length) return
  const results = await Promise.allSettled(uncached.map(id => getPaperBrief(id)))
  results.forEach((r, i) => {
    if (r.status === 'fulfilled' && r.value) {
      briefCache.value[uncached[i]!] = r.value
    }
  })
}

// ── Core search ───────────────────────────────────────────────
async function doSearch(append = false) {
  const { searchPapers } = useDeepXiv()
  if (!append) {
    isSearching.value = true
    offset.value = 0
  }
  else {
    isLoadingMore.value = true
  }

  const params = searchParams.value
  try {
    const res = await searchPapers(queryText.value || 'large language model', {
      size: PAGE_SIZE,
      offset: offset.value,
      categories: params.categories.length ? params.categories : undefined,
      date_from: params.dateFrom,
      date_to: params.dateTo,
      min_citation: params.minCitation,
      search_mode: params.searchMode,
    })

    if (append) {
      searchResults.value = [...searchResults.value, ...(res.results ?? [])]
    }
    else {
      searchResults.value = res.results ?? []
    }
    resultTotal.value = res.total ?? 0

    // Fetch briefs for first page top 8
    const ids = searchResults.value.slice(0, 8).map(r => r.arxiv_id)
    await fetchBriefs(ids)
  }
  catch (e) {
    console.error('[Discover] search error', e)
    if (!append) searchResults.value = []
  }
  finally {
    isSearching.value = false
    isLoadingMore.value = false
  }
}

// ── Mount ─────────────────────────────────────────────────────
onMounted(async () => {
  const { searchPapers } = useDeepXiv()
  const { getAnalyticsCategories, getAnalyticsVenues } = useApi()

  // 1. Load topic covers in parallel
  const topicResults = await Promise.allSettled(
    TOPIC_DEFS.map(td =>
      searchPapers(td.query, { categories: [td.category], size: 1 }),
    ),
  )
  topicCovers.value = TOPIC_DEFS.map((td, i) => {
    const res = topicResults[i]
    const total = res?.status === 'fulfilled' ? (res.value.total ?? 0) : 0
    const topPaper = res?.status === 'fulfilled' ? res.value.results[0] : undefined
    return {
      id: td.id,
      label: td.label,
      title: topPaper?.title ?? td.query,
      subtitle: TOPIC_SUBTITLES[td.id] ?? '',
      count: total,
      accent: td.accent,
    }
  })
  topicsLoading.value = false

  // 2. Load default recommendation feed
  await doSearch()

  // 3. Sidebar: try local analytics, fallback to category labels
  try {
    const venues = await getAnalyticsVenues(10)
    venueShelfTitle.value = 'Top Venues'
    venueItems.value = (venues.venues ?? []).map((v: { name: string; count: number }, i: number) => ({
      id: `ven-${i}`,
      name: v.name,
      count: v.count,
    }))
  }
  catch {
    try {
      const cats = await getAnalyticsCategories(10)
      venueShelfTitle.value = 'Top Categories'
      venueItems.value = (cats.categories ?? []).map((c: { name: string; count: number }, i: number) => ({
        id: `cat-${i}`,
        name: c.name,
        count: c.count,
      }))
    }
    catch {
      venueShelfTitle.value = 'Browse Topics'
      venueItems.value = [
        { id: 'cs.AI', name: 'cs.AI — Artificial Intelligence', count: 0 },
        { id: 'cs.CL', name: 'cs.CL — Natural Language Processing', count: 0 },
        { id: 'cs.CV', name: 'cs.CV — Computer Vision', count: 0 },
        { id: 'cs.LG', name: 'cs.LG — Machine Learning', count: 0 },
        { id: 'stat.ML', name: 'stat.ML — Statistical ML', count: 0 },
      ]
    }
  }
})

onUnmounted(() => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
})

// ── Unified watch — re-search when query or filters change ────
// Debounced to prevent double-firing when both query & facets change together
let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null

function scheduleSearch() {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    offset.value = 0
    doSearch()
  }, 60)
}

watch(
  () => facetGroups.value.flatMap(g => g.options.map(o => `${g.title}:${o.label}:${o.active}`)).join(','),
  scheduleSearch,
)

// ── Handlers ──────────────────────────────────────────────────
function handleTopicClick(topic: TopicCover) {
  const def = TOPIC_DEFS.find(td => td.id === topic.id)
  if (def) {
    queryText.value = def.query
    const domainGroup = facetGroups.value.find(g => g.title === 'Domain')
    if (domainGroup) {
      // Changing facets will trigger the watcher → scheduleSearch()
      domainGroup.options.forEach(o => { o.active = o.label === def.category })
      return
    }
  }
  else {
    queryText.value = topic.title
  }
  // If no facet changed, kick off search directly
  scheduleSearch()
}

function handleFacetToggle(group: string, option: string, active: boolean) {
  const g = facetGroups.value.find(fg => fg.title === group)
  if (!g) return
  if (group === 'Search Mode') {
    // Radio: only one active at a time
    g.options.forEach(o => { o.active = o.label === option ? active : false })
    if (!g.options.some(o => o.active)) g.options[0]!.active = true
  }
  else if (group === 'Impact') {
    g.options.forEach(o => { o.active = o.label === option ? active : false })
    if (!g.options.some(o => o.active)) g.options.find(o => o.label === 'Any')!.active = true
  }
  else {
    const opt = g.options.find(o => o.label === option)
    if (opt) opt.active = active
  }
}

function handlePaperClick(paper: RecommendedPaper) {
  navigateTo(paper.href ?? `/deepxiv/papers/${paper.id}`)
}

function handlePaperSave(paper: RecommendedPaper) {
  bookmarkTarget.value = { arxivId: paper.id, title: paper.title }
}

function handleQuerySubmit(q: string) {
  queryText.value = q
  pushHistory(q)
  scheduleSearch()
}

function handleLoadMore() {
  offset.value += PAGE_SIZE
  doSearch(true)
}

function handleVenueClick(venue: VenueItem) {
  const catMatch = venue.name.match(/^([\w.]+)\s*—/)
  if (catMatch) {
    const domainGroup = facetGroups.value.find(g => g.title === 'Domain')
    if (domainGroup) {
      const opt = domainGroup.options.find(o => o.label === catMatch[1])
      if (opt) {
        opt.active = true
        return
      }
    }
  }
  if (venueShelfTitle.value.includes('Venue')) {
    navigateTo(`/search?venue=${encodeURIComponent(venue.name)}`)
  }
  else {
    queryText.value = venue.name
    doSearch()
  }
}

function handleGraphExplore() {
  navigateTo('/insights/landscape')
}

function handleExplorationReopen(exploration: SavedExploration) {
  queryText.value = exploration.title
  offset.value = 0
  doSearch()
}

const selectedCount = ref(0)
const queryPlaceholder = 'e.g. citation-grounded agents with human evaluation, biomedical evidence extraction, benchmark leakage detection…'
const querySuggestions = [
  'LLM reasoning chain of thought',
  'Multimodal clinical VLM',
  'Efficient long-context attention',
  'Diffusion model image generation',
]

const hasMore = computed(() => offset.value + PAGE_SIZE < resultTotal.value)
</script>

<template>
  <div class="ks-discover">
    <!-- ═══ Row 1: Topics Wall + Query Composer ═══ -->
    <div class="ks-discover__row ks-discover__row--top">
      <DiscoverTopicsWall
        :topics="topicsLoading ? [] : topicCovers"
        @topic-click="handleTopicClick"
      />
      <DiscoverQueryComposer
        v-model="queryText"
        :placeholder="queryPlaceholder"
        :suggestions="querySuggestions"
        @submit="handleQuerySubmit"
      />
    </div>

    <!-- ═══ Tab Navigation ═══ -->
    <div class="ks-discover__tabs">
      <button
        type="button"
        :class="['ks-discover__tab', activeTab === 'search' && 'ks-discover__tab--active']"
        @click="activeTab = 'search'"
      >
        Search Results
      </button>
      <button
        type="button"
        :class="['ks-discover__tab', activeTab === 'trending' && 'ks-discover__tab--active']"
        @click="activeTab = 'trending'"
      >
        Trending Papers
      </button>
    </div>

    <!-- ═══ Row 2+: Facets + Stream + Sidebar ═══ -->
    <div v-if="activeTab === 'search'" class="ks-discover__row ks-discover__row--main">
      <DiscoverFacetWall
        :groups="facetGroups"
        @facet-toggle="handleFacetToggle"
      />

      <div class="ks-discover__stream-col">
        <!-- Results header -->
        <div v-if="!isSearching && searchResults.length > 0" class="ks-discover__results-header">
          <span class="ks-discover__results-count">
            {{ resultTotal.toLocaleString() }} results
            <span v-if="queryText"> for "<strong>{{ queryText }}</strong>"</span>
          </span>
        </div>

        <!-- Loading skeleton -->
        <div v-if="isSearching" class="ks-discover__skeleton-grid">
          <div v-for="n in 4" :key="n" class="ks-discover__skeleton-card">
            <div class="ks-discover__skeleton-eyebrow" />
            <div class="ks-discover__skeleton-title" />
            <div class="ks-discover__skeleton-text" />
            <div class="ks-discover__skeleton-text ks-discover__skeleton-text--short" />
          </div>
        </div>

        <DiscoverRecommendationStream
          v-else
          :papers="recommendations"
          @paper-click="handlePaperClick"
          @save="handlePaperSave"
          @compare="handlePaperClick"
        />

        <!-- Load more -->
        <div v-if="hasMore && !isSearching" class="ks-discover__load-more">
          <button
            type="button"
            class="ks-discover__load-more-btn"
            :disabled="isLoadingMore"
            @click="handleLoadMore"
          >
            {{ isLoadingMore ? 'Loading…' : `Load more (${resultTotal - searchResults.length} remaining)` }}
          </button>
        </div>

        <!-- Empty state -->
        <div v-if="!isSearching && searchResults.length === 0" class="ks-discover__empty">
          <p class="ks-discover__empty-title">No results found</p>
          <p class="ks-discover__empty-desc">Try a different query or clear some filters.</p>
        </div>
      </div>

      <!-- Right sidebar stack -->
      <div class="ks-discover__sidebar-right">
        <DiscoverVenueShelf
          :title="venueShelfTitle"
          :venues="venueItems"
          @venue-click="handleVenueClick"
        />
        <DiscoverGraphTeaser
          :nodes="graphNodes"
          :edges="graphEdges"
          @explore="handleGraphExplore"
        />
        <DiscoverSavedExplorations
          :explorations="queryHistory"
          @reopen="handleExplorationReopen"
        />
      </div>
    </div>

    <!-- ═══ Trending Tab Content ═══ -->
    <div v-else-if="activeTab === 'trending'" class="ks-discover__trending-container">
      <DiscoverTrendingTab />
    </div>

    <!-- ═══ Next Actions Bar (fixed bottom) ═══ -->
    <DiscoverNextActionsBar :selected-count="selectedCount" />

    <!-- Bookmark modal -->
    <CollectionsGroupPickerModal
      v-if="bookmarkTarget"
      :arxiv-id="bookmarkTarget.arxivId"
      :title="bookmarkTarget.title"
      @close="bookmarkTarget = null"
      @saved="bookmarkTarget = null"
    />

    <!-- AI Assistant Drawer -->
    <DiscoverAiAssistantDrawer
      :open="aiDrawerOpen"
      @close="aiDrawerOpen = false"
    />

    <!-- Floating AI Button -->
    <DiscoverFloatingAiButton @click="aiDrawerOpen = true" />
  </div>
</template>

<style scoped>
.ks-discover {
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding-bottom: 96px;
}

/* ─── Grid rows ───────────────────────────────────────────── */
.ks-discover__row--top {
  display: grid;
  grid-template-columns: 5fr 2fr;
  gap: 24px;
  align-items: stretch;
}

.ks-discover__row--main {
  display: grid;
  grid-template-columns: 260px 1fr 280px;
  gap: 24px;
  align-items: start;
}

/* ─── Stream column ───────────────────────────────────────── */
.ks-discover__stream-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.ks-discover__results-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ks-discover__results-count {
  font: 400 0.8125rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-discover__results-count strong {
  color: var(--color-text);
  font-weight: 600;
}

/* ─── Skeleton loaders ────────────────────────────────────── */
@keyframes ks-discover-shimmer {
  0% { background-position: -200% center; }
  100% { background-position: 200% center; }
}

.ks-discover__skeleton-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.ks-discover__skeleton-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

.ks-discover__skeleton-eyebrow,
.ks-discover__skeleton-title,
.ks-discover__skeleton-text {
  border-radius: 4px;
  background: linear-gradient(90deg, var(--color-border) 25%, rgba(255,255,255,0.06) 50%, var(--color-border) 75%);
  background-size: 200% 100%;
  animation: ks-discover-shimmer 1.5s infinite;
}

.ks-discover__skeleton-eyebrow { height: 10px; width: 60px; }
.ks-discover__skeleton-title { height: 20px; width: 90%; }
.ks-discover__skeleton-text { height: 14px; width: 100%; }
.ks-discover__skeleton-text--short { width: 70%; }

/* ─── Load more ───────────────────────────────────────────── */
.ks-discover__load-more {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}

.ks-discover__load-more-btn {
  padding: 10px 28px;
  background: var(--color-surface);
  border: 1.5px solid var(--color-border);
  border-radius: 6px;
  font: 500 0.875rem / 1 var(--font-sans);
  color: var(--color-text);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.ks-discover__load-more-btn:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.ks-discover__load-more-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ─── Empty ───────────────────────────────────────────────── */
.ks-discover__empty {
  padding: 60px 40px;
  text-align: center;
  background: var(--color-surface);
  border: 1px dashed var(--color-border);
  border-radius: 8px;
}

.ks-discover__empty-title {
  font: 600 1.125rem / 1 var(--font-display);
  color: var(--color-text);
  margin: 0 0 8px;
}

.ks-discover__empty-desc {
  font: 400 0.875rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
}

/* ─── Right sidebar stack ─────────────────────────────────── */
.ks-discover__sidebar-right {
  display: flex;
  flex-direction: column;
  gap: 20px;
  position: sticky;
  top: 104px;
  max-height: calc(100dvh - 128px);
  overflow-y: auto;
  scrollbar-width: thin;
}

/* ─── Tab Navigation ──────────────────────────────────────── */
.ks-discover__tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 24px;
}

.ks-discover__tab {
  padding: 12px 24px;
  border: none;
  background: none;
  font: 500 0.875rem / 1 var(--font-sans);
  color: var(--color-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
  position: relative;
  bottom: -1px;
}

.ks-discover__tab:hover {
  color: var(--color-text);
}

.ks-discover__tab--active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

/* ─── Trending Container ──────────────────────────────────── */
.ks-discover__trending-container {
  width: 100%;
}

/* ─── Responsive ──────────────────────────────────────────── */
@media (max-width: 1280px) {
  .ks-discover__row--main {
    grid-template-columns: 240px 1fr 240px;
    gap: 16px;
  }
  .ks-discover__skeleton-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .ks-discover__row--top {
    grid-template-columns: 1fr;
  }
  .ks-discover__row--main {
    grid-template-columns: 1fr;
  }
  .ks-discover__sidebar-right {
    position: static;
    max-height: none;
  }
  .ks-discover__skeleton-grid {
    grid-template-columns: 1fr;
  }
}
</style>
