<script setup lang="ts">
/**
 * Search — OpenAlex discovery + citation graph builder.
 *
 * Phase 1 "spotlight"  — centered search bar (macOS Spotlight style)
 * Phase 2 "results"    — left list with checkboxes, select papers to graph
 * Phase 3 "graph"      — left node list, center force graph, right detail
 *
 * Topbar is hidden; the page manages its own slim nav strip in phases 2 & 3.
 */
import type { OpenAlexPaper, OpenAlexGraphNode, OpenAlexEdge, Collection } from '~/composables/useApi'
import type { GraphNode } from '~/components/search/RelationGraph.vue'

definePageMeta({ layout: 'default', hideTopbar: true, flushContent: true })
useHead({ title: 'Relation Network — Kaleidoscope' })

const { translate, isPending } = useTranslation()

// ── State ─────────────────────────────────────────────────────

type Phase = 'spotlight' | 'results' | 'graph'
const phase = ref<Phase>('spotlight')
const api = useApi()

// Search
const queryText = ref('')
const spotlightInput = ref<HTMLInputElement>()
const isSearching = ref(false)
const searchError = ref<string | null>(null)
const searchResults = ref<OpenAlexPaper[]>([])

// Selection (phase 2)
const selectedIds = ref<Set<string>>(new Set())
const resultsFocusedId = ref<string | null>(null)
const resultsFocusedPaper = computed<OpenAlexPaper | null>(() =>
  searchResults.value.find(p => p.openalex_id === resultsFocusedId.value) ?? null,
)

// Graph (phase 3)
const isBuilding = ref(false)
const buildError = ref<string | null>(null)
const graphNodes = ref<OpenAlexGraphNode[]>([])
const graphEdges = ref<OpenAlexEdge[]>([])
const graphSelectedId = ref<string | null>(null)

type LayoutMode = 'split' | 'list' | 'map'
const layoutMode = ref<LayoutMode>('split')

// ── Resizable panels ──────────────────────────────────────────

const LEFT_MIN = 220
const CENTER_MIN = 300
const RIGHT_MIN = 260
const leftWidth = ref(292)
const rightWidth = ref(360)

function startDragLeft(e: MouseEvent) {
  e.preventDefault()
  const startX = e.clientX
  const startW = leftWidth.value
  const onMove = (me: MouseEvent) => {
    leftWidth.value = Math.max(LEFT_MIN, startW + (me.clientX - startX))
  }
  const onUp = () => {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
    document.body.style.cssText = ''
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function startDragRight(e: MouseEvent) {
  e.preventDefault()
  const startX = e.clientX
  const startW = rightWidth.value
  const onMove = (me: MouseEvent) => {
    rightWidth.value = Math.max(RIGHT_MIN, startW - (me.clientX - startX))
  }
  const onUp = () => {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
    document.body.style.cssText = ''
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

const leftStyle = computed(() =>
  layoutMode.value === 'list'
    ? { flex: '1', minWidth: LEFT_MIN + 'px' }
    : { width: leftWidth.value + 'px', minWidth: LEFT_MIN + 'px' },
)

const rightStyle = computed(() => ({
  width: rightWidth.value + 'px',
  minWidth: RIGHT_MIN + 'px',
}))

// ── Spotlight → search ────────────────────────────────────────

async function runSearch(q: string) {
  const trimmed = q.trim()
  if (!trimmed) return
  isSearching.value = true
  searchError.value = null
  try {
    const res = await api.searchOpenAlex(trimmed, { limit: 50 })
    searchResults.value = res.papers
    selectedIds.value = new Set()
    resultsFocusedId.value = null
    phase.value = 'results'
  }
  catch (err) {
    searchError.value = err instanceof Error ? err.message : 'Search failed'
  }
  finally {
    isSearching.value = false
  }
}

function handleSpotlightSubmit() {
  void runSearch(queryText.value)
}

function handleSearchSubmit() {
  void runSearch(queryText.value)
}

// ── Paper selection (phase 2) ─────────────────────────────────

function toggleSelect(id: string) {
  const s = new Set(selectedIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selectedIds.value = s
}

function selectAll() {
  selectedIds.value = new Set(searchResults.value.map(p => p.openalex_id))
}

function clearSelection() {
  selectedIds.value = new Set()
}

// ── Build graph (phase 2 → 3) ─────────────────────────────────

async function buildGraph() {
  if (!selectedIds.value.size) return
  isBuilding.value = true
  buildError.value = null
  try {
    const res = await api.buildOpenAlexGraph([...selectedIds.value])
    graphNodes.value = res.nodes
    graphEdges.value = res.edges
    graphSelectedId.value = null

    // Notify user if some papers were filtered out due to no connections
    if (res.isolated_count > 0) {
      console.warn(`${res.isolated_count} paper(s) were excluded from the graph due to no citation connections`)
    }

    phase.value = 'graph'
  }
  catch (err) {
    buildError.value = err instanceof Error ? err.message : 'Graph build failed'
  }
  finally {
    isBuilding.value = false
  }
}

// ── Graph interaction (phase 3) ───────────────────────────────

function handleGraphSelect(id: string) {
  graphSelectedId.value = graphSelectedId.value === id ? null : id
}

function handleGraphDeselect() {
  graphSelectedId.value = null
}

const graphSelectedNode = computed<OpenAlexGraphNode | null>(() =>
  graphNodes.value.find(n => n.openalex_id === graphSelectedId.value) ?? null,
)

// Unified detail paper — covers both phases
type DetailPaper = OpenAlexPaper & { is_origin?: boolean }
const detailPaper = computed<DetailPaper | null>(() => {
  if (phase.value === 'graph') return graphSelectedNode.value ?? null
  return resultsFocusedPaper.value
})

// ── Helpers ───────────────────────────────────────────────────

function firstAuthorLastName(p: { authors?: string[] }) {
  const name = p.authors?.[0] ?? ''
  const parts = name.trim().split(/\s+/)
  const last = parts[parts.length - 1] ?? ''
  const rest = parts.length > 1 ? ` et al.` : ''
  return last + rest
}

function firstAuthorFullName(p: { authors?: string[] }) {
  return p.authors?.[0] ?? '—'
}

function formatCitations(n?: number | null) {
  if (!n) return '0'
  return n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n)
}

// ── Abstract translation ──────────────────────────────────────

const translatedAbstract = ref<string | null>(null)
const showTranslated = ref(false)

async function toggleTranslate(text: string) {
  if (showTranslated.value) {
    showTranslated.value = false
    return
  }
  if (!translatedAbstract.value) {
    translatedAbstract.value = await translate(text)
  }
  showTranslated.value = true
}

watch(detailPaper, () => {
  translatedAbstract.value = null
  showTranslated.value = false
})

// ── Add to Collection ─────────────────────────────────────────

const collections = ref<Collection[]>([])
const showCollectionDropdown = ref(false)
const isAddingToCollection = ref(false)
const addToCollectionError = ref<string | null>(null)
const addToCollectionSuccess = ref<string | null>(null)

async function addToCollection(collectionId: string, collectionName: string) {
  if (!detailPaper.value) return

  isAddingToCollection.value = true
  addToCollectionError.value = null
  addToCollectionSuccess.value = null
  showCollectionDropdown.value = false

  try {
    // Step 1: Import paper to local DB using DOI or OpenAlex URL
    const identifier = detailPaper.value.doi
      || `https://openalex.org/${detailPaper.value.openalex_id}`
    const identifierType = detailPaper.value.doi ? 'doi' : 'url'

    const importResult = await api.importPaper({
      identifier,
      identifier_type: identifierType,
    })

    // Step 2: Check if we got a paper_id (immediate import) or if it's queued
    if (importResult.status === 'queued') {
      // Paper is being imported asynchronously
      addToCollectionSuccess.value = `Importing paper... Check collection "${collectionName}" later`
      setTimeout(() => {
        addToCollectionSuccess.value = null
      }, 5000)
      return
    }

    if (!importResult.paper_id) {
      throw new Error('Import succeeded but no paper_id returned')
    }

    // Step 3: Add to collection using the paper UUID
    await api.addPapersToCollection(collectionId, [importResult.paper_id])

    addToCollectionSuccess.value = `Added to "${collectionName}"`
    setTimeout(() => {
      addToCollectionSuccess.value = null
    }, 3000)
  }
  catch (err) {
    addToCollectionError.value = err instanceof Error ? err.message : 'Failed to add to collection'
    setTimeout(() => {
      addToCollectionError.value = null
    }, 5000)
  }
  finally {
    isAddingToCollection.value = false
  }
}

// ── Venue display (arxiv category inference) ──────────────────

const ARXIV_CAT_MAP: Array<[RegExp, string]> = [
  [/natural language|computational linguistics|\bnlp\b/i, 'cs.CL'],
  [/computer vision|image recognition|object detect/i, 'cs.CV'],
  [/machine learning|\bdeep learning\b|\bneural network/i, 'cs.LG'],
  [/artificial intelligence/i, 'cs.AI'],
  [/information retrieval|recommender/i, 'cs.IR'],
  [/robotics/i, 'cs.RO'],
  [/software engineering/i, 'cs.SE'],
  [/computer network|distributed system/i, 'cs.NI'],
  [/algorithm|data structure|complexity/i, 'cs.DS'],
  [/bioinformatics|genomics|proteomics/i, 'q-bio'],
  [/quantum/i, 'quant-ph'],
  [/high energy|particle physics/i, 'hep-ph'],
  [/astrophysics/i, 'astro-ph'],
  [/condensed matter/i, 'cond-mat'],
  [/statistics|statistical/i, 'stat.ML'],
  [/economics\b|econometrics/i, 'econ'],
  [/mathematics|algebra|topology/i, 'math'],
]

function venueDisplay(paper: { venue?: string | null; doi?: string | null; primary_topic?: string | null; topics?: Array<{ display_name: string }> }): string {
  const isArxiv = paper.venue === 'arXiv'
    || paper.doi?.toLowerCase().includes('10.48550/arxiv')
  if (!isArxiv) return paper.venue || '—'

  const topicStr = [
    paper.primary_topic,
    ...(paper.topics?.map(t => t.display_name) ?? []),
  ].filter(Boolean).join(' ')

  for (const [pattern, cat] of ARXIV_CAT_MAP) {
    if (pattern.test(topicStr)) return `arXiv [${cat}]`
  }
  return 'arXiv'
}

// ── Mount lifecycle ───────────────────────────────────────────

onMounted(async () => {
  nextTick(() => spotlightInput.value?.focus())
  try {
    collections.value = await api.listCollections()
  }
  catch (err) {
    console.error('Failed to load collections:', err)
  }
})

const graphDisplayNodes = computed<GraphNode[]>(() =>
  graphNodes.value.map(n => ({
    openalex_id: n.openalex_id,
    title: n.title,
    year: n.year,
    authors: n.authors,
    cited_by_count: n.cited_by_count,
    is_origin: n.is_origin,
    abstract: n.abstract,
    venue: n.venue,
  })),
)
</script>

<template>
  <div class="kss-page">

    <!-- ══════════════════════════════════════════════════════════
         PHASE 1 — SPOTLIGHT
    ══════════════════════════════════════════════════════════ -->
    <Transition name="kss-fade">
      <div v-if="phase === 'spotlight'" class="kss-spotlight">
        <div class="kss-spotlight__inner">
          <img src="/brand/kaleidoscope-icon-mark.png" alt="" class="kss-spotlight__logo" />
          <h1 class="kss-spotlight__brand">Kaleidoscope</h1>
          <p class="kss-spotlight__sub">Relation Network Explorer</p>

          <div class="kss-spotlight__box" :class="{ 'kss-spotlight__box--loading': isSearching }">
            <svg class="kss-spotlight__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
            </svg>
            <input
              ref="spotlightInput"
              v-model="queryText"
              type="text"
              class="kss-spotlight__input"
              placeholder="Search papers, topics, authors…"
              :disabled="isSearching"
              @keydown.enter="handleSpotlightSubmit"
            />
            <span v-if="isSearching" class="kss-spotlight__spinner" />
            <kbd v-else class="kss-spotlight__kbd">↵</kbd>
          </div>

          <p v-if="searchError" class="kss-spotlight__error">{{ searchError }}</p>
          <p v-else class="kss-spotlight__hint">Press Enter to search</p>
        </div>
      </div>
    </Transition>

    <!-- ══════════════════════════════════════════════════════════
         PHASES 2 & 3 — THREE-COLUMN LAYOUT
    ══════════════════════════════════════════════════════════ -->
    <Transition name="kss-slide">
      <div v-if="phase !== 'spotlight'" class="kss-layout">

        <!-- ── Slim nav ── -->
        <nav class="kss-nav">
          <div v-if="phase === 'graph'" class="kss-nav__modes">
            <button
              v-for="m in (['split', 'list', 'map'] as const)"
              :key="m"
              :class="['kss-nav__mode', layoutMode === m && 'kss-nav__mode--active']"
              @click="layoutMode = m"
            >{{ m }}</button>
          </div>
          <!-- Back to results when in graph -->
          <button v-if="phase === 'graph'" class="kss-nav__back" @click="phase = 'results'">
            ← Results
          </button>
        </nav>

        <!-- ── Body ── -->
        <div class="kss-body">

          <!-- LEFT PANEL -->
          <aside
            v-show="phase === 'results' || layoutMode !== 'map'"
            class="kss-left"
            :style="phase === 'graph' ? leftStyle : {}"
          >
            <!-- Search bar -->
            <div class="kss-left__search">
              <div class="kss-search-field">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0;color:#6e7979">
                  <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
                </svg>
                <input
                  v-model="queryText"
                  type="text"
                  class="kss-search-input"
                  placeholder="New search…"
                  @keydown.enter="handleSearchSubmit"
                />
              </div>
            </div>

            <!-- PHASE 2: Results with checkboxes -->
            <template v-if="phase === 'results'">
              <div class="kss-left__header">
                <span class="kss-label">
                  {{ isSearching ? 'Searching…' : `Results (${searchResults.length})` }}
                </span>
                <div class="kss-left__header-actions">
                  <button class="kss-link-btn" @click="selectAll">All</button>
                  <button class="kss-link-btn" @click="clearSelection">None</button>
                </div>
              </div>

              <ul class="kss-list">
                <li
                  v-for="p in searchResults"
                  :key="p.openalex_id"
                  :class="['kss-card', selectedIds.has(p.openalex_id) && 'kss-card--checked', resultsFocusedId === p.openalex_id && 'kss-card--focused']"
                  @click="resultsFocusedId = p.openalex_id"
                >
                  <div
                    class="kss-card__check"
                    @click.stop="toggleSelect(p.openalex_id)"
                  >
                    <div :class="['kss-checkbox', selectedIds.has(p.openalex_id) && 'kss-checkbox--on']">
                      <svg v-if="selectedIds.has(p.openalex_id)" width="10" height="10" viewBox="0 0 10 10" fill="none">
                        <path d="M1.5 5l2.5 2.5 4.5-4.5" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                      </svg>
                    </div>
                  </div>
                  <div class="kss-card__body">
                    <p class="kss-card__year">{{ p.year ?? '—' }}</p>
                    <h4 class="kss-card__title">{{ p.title }}</h4>
                    <p class="kss-card__author">{{ firstAuthorLastName(p) }}</p>
                    <p class="kss-card__venue">{{ venueDisplay(p) }}</p>
                  </div>
                </li>
              </ul>

              <!-- Build button (sticky footer) -->
              <div v-if="selectedIds.size > 0" class="kss-build-footer">
                <button
                  class="kss-build-btn"
                  :disabled="isBuilding"
                  @click="buildGraph"
                >
                  <span v-if="isBuilding">Building…</span>
                  <span v-else>Build Graph ({{ selectedIds.size }})</span>
                </button>
                <p v-if="buildError" class="kss-build-error">{{ buildError }}</p>
              </div>
            </template>

            <!-- PHASE 3: Graph node list -->
            <template v-else-if="phase === 'graph'">
              <!-- Origin papers: compact pinned section -->
              <div class="kss-origin-section">
                <div class="kss-origin-section__header">
                  <span class="kss-label">Selected · {{ graphNodes.filter(n => n.is_origin).length }}</span>
                </div>
                <ul class="kss-origin-list">
                  <li
                    v-for="n in graphNodes.filter(n => n.is_origin)"
                    :key="n.openalex_id"
                    :class="['kss-origin-item', graphSelectedId === n.openalex_id && 'kss-origin-item--selected']"
                    @click="handleGraphSelect(n.openalex_id)"
                  >
                    <span class="kss-origin-dot" />
                    <span class="kss-origin-item__title">{{ n.title }}</span>
                  </li>
                </ul>
              </div>

              <!-- References header -->
              <div class="kss-left__header">
                <span class="kss-label">References · {{ graphNodes.filter(n => !n.is_origin).length }}</span>
              </div>

              <!-- List mode: rich cards for reference papers -->
              <ul v-if="layoutMode === 'list'" class="kss-list">
                <li
                  v-for="n in graphNodes.filter(n => !n.is_origin)"
                  :key="n.openalex_id"
                  :class="['kss-card-list', graphSelectedId === n.openalex_id && 'kss-card-list--selected']"
                  @click="handleGraphSelect(n.openalex_id)"
                >
                  <div class="kss-card-list__header">
                    <span class="kss-card-list__author">{{ firstAuthorFullName(n) }}</span>
                    <span class="kss-card-list__year">{{ n.year ?? '—' }}</span>
                  </div>
                  <h4 class="kss-card-list__title">{{ n.title }}</h4>
                  <p class="kss-card-list__venue">{{ venueDisplay(n) }}</p>
                  <hr class="kss-card-list__divider" />
                  <p class="kss-card-list__abstract">{{ n.abstract ?? 'No abstract available.' }}</p>
                </li>
              </ul>

              <!-- Split/map mode: compact cards for reference papers -->
              <ul v-else class="kss-list">
                <li
                  v-for="n in graphNodes.filter(n => !n.is_origin)"
                  :key="n.openalex_id"
                  :class="['kss-card kss-card--node', graphSelectedId === n.openalex_id && 'kss-card--selected']"
                  @click="handleGraphSelect(n.openalex_id)"
                >
                  <div class="kss-card__check">
                    <div class="kss-dot kss-dot--ref" />
                  </div>
                  <div class="kss-card__body">
                    <p class="kss-card__year">{{ n.year ?? '—' }}</p>
                    <h4 class="kss-card__title">{{ n.title }}</h4>
                    <p class="kss-card__author">{{ firstAuthorLastName(n) }}</p>
                    <p class="kss-card__venue">{{ venueDisplay(n) }}</p>
                  </div>
                </li>
              </ul>
            </template>
          </aside>

          <!-- Resize handle: Left-Center (split mode only) -->
          <div
            v-if="phase === 'graph' && layoutMode === 'split'"
            class="kss-handle"
            @mousedown="startDragLeft"
          />

          <!-- CENTER PANEL — Graph (phase 3) -->
          <section
            v-if="phase === 'graph'"
            v-show="layoutMode !== 'list'"
            class="kss-center"
            :style="{ minWidth: CENTER_MIN + 'px' }"
          >
            <header class="kss-center__header">
              <div>
                <h2 class="kss-center__title">Relation Network</h2>
                <p class="kss-center__sub">
                  {{ graphNodes.filter(n => n.is_origin).length }} origin ·
                  {{ graphNodes.filter(n => !n.is_origin).length }} references ·
                  {{ graphEdges.length }} edges
                </p>
              </div>
              <div class="kss-center__legend">
                <span class="kss-legend-item">
                  <svg width="18" height="18" viewBox="0 0 18 18">
                    <circle cx="9" cy="9" r="7" fill="none" stroke="#00595c" stroke-width="1.5" stroke-dasharray="4 3" />
                    <circle cx="9" cy="9" r="5" fill="#e8f4f4" stroke="#00595c" stroke-width="1.5" />
                  </svg>
                  Origin
                </span>
                <span class="kss-legend-item">
                  <svg width="18" height="18" viewBox="0 0 18 18">
                    <circle cx="9" cy="9" r="5" fill="#fff" stroke="#9eacac" stroke-width="1.2" />
                  </svg>
                  Reference
                </span>
                <span class="kss-legend-item">
                  <svg width="28" height="10" viewBox="0 0 28 10">
                    <line x1="1" y1="5" x2="22" y2="5" stroke="#bec9c9" stroke-width="1" />
                    <path d="M18,2 L24,5 L18,8 Z" fill="#bec9c9" />
                  </svg>
                  Cites
                </span>
              </div>
            </header>
            <div class="kss-center__graph">
              <SearchRelationGraph
                :nodes="graphDisplayNodes"
                :edges="graphEdges"
                :selected-id="graphSelectedId"
                @select="handleGraphSelect"
                @deselect="handleGraphDeselect"
              />
            </div>
            <p class="kss-center__footer">Click node to explore · Click background to deselect · Drag to reposition</p>
          </section>

          <!-- CENTER PANEL — Placeholder (phase 2) -->
          <section v-else-if="phase === 'results'" class="kss-center kss-center--empty">
            <div class="kss-center-placeholder">
              <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                <circle cx="32" cy="32" r="20" stroke="#bec9c9" stroke-width="1.5" stroke-dasharray="5 4" />
                <circle cx="32" cy="32" r="6" fill="#e8e8e5" stroke="#bec9c9" stroke-width="1.5" />
                <circle cx="12" cy="24" r="4" fill="#f4f4f1" stroke="#bec9c9" stroke-width="1.2" />
                <circle cx="52" cy="20" r="4" fill="#f4f4f1" stroke="#bec9c9" stroke-width="1.2" />
                <circle cx="14" cy="44" r="4" fill="#f4f4f1" stroke="#bec9c9" stroke-width="1.2" />
                <line x1="16" y1="24" x2="26" y2="29" stroke="#bec9c9" stroke-width="1" />
                <line x1="48" y1="22" x2="38" y2="28" stroke="#bec9c9" stroke-width="1" />
                <line x1="18" y1="42" x2="26" y2="36" stroke="#bec9c9" stroke-width="1" />
              </svg>
              <p class="kss-center-placeholder__text">Select papers on the left,<br>then click <strong>Build Graph</strong></p>
            </div>
          </section>

          <!-- Resize handle: Center-Right -->
          <div
            v-if="(phase === 'graph' && layoutMode !== 'list') || (phase === 'results' && detailPaper)"
            class="kss-handle"
            @mousedown="startDragRight"
          />

          <!-- RIGHT PANEL — Paper detail (phases 2 & 3) -->
          <aside
            v-if="phase === 'graph' || (phase === 'results' && detailPaper)"
            v-show="phase === 'results' || layoutMode !== 'map' || graphSelectedNode"
            class="kss-right"
            :style="rightStyle"
          >
            <div v-if="!detailPaper" class="kss-right__empty">
              <div class="kss-right__empty-icon">◎</div>
              <p>Click a node to see its details</p>
            </div>
            <div v-else class="kss-detail">
              <!-- Top group -->
              <div class="kss-detail__top">
                <!-- Origin/Reference badge — only in graph phase -->
                <div v-if="phase === 'graph' && detailPaper.is_origin !== undefined" class="kss-detail__eyebrow">
                  <span class="kss-detail__rule" />
                  <span :class="['kss-detail__tag', detailPaper.is_origin ? 'kss-detail__tag--origin' : 'kss-detail__tag--ref']">
                    {{ detailPaper.is_origin ? 'Origin paper' : 'Reference' }}
                  </span>
                </div>
                <!-- Selection indicator — in results phase -->
                <div v-else-if="phase === 'results'" class="kss-detail__eyebrow">
                  <span class="kss-detail__rule" />
                  <span :class="['kss-detail__tag', selectedIds.has(detailPaper.openalex_id) ? 'kss-detail__tag--origin' : 'kss-detail__tag--ref']">
                    {{ selectedIds.has(detailPaper.openalex_id) ? 'Selected for graph' : 'Not selected' }}
                  </span>
                </div>

                <h1 class="kss-detail__title">{{ detailPaper.title }}</h1>

                <!-- Authors as hyperlinks -->
                <div class="kss-detail__authors">
                  <span class="kss-label kss-label--xs" style="display:block;margin-bottom:6px">Authors</span>
                  <div class="kss-detail__author-list">
                    <template v-if="detailPaper.authorships?.length">
                      <a
                        v-for="a in detailPaper.authorships"
                        :key="a.openalex_id"
                        :href="`https://openalex.org/${a.openalex_id}`"
                        target="_blank"
                        rel="noopener"
                        class="kss-detail__author-link"
                        :title="a.institutions?.join(', ')"
                      >{{ a.name }}</a>
                    </template>
                    <template v-else>
                      <span v-for="name in detailPaper.authors" :key="name" class="kss-detail__author-plain">{{ name }}</span>
                    </template>
                  </div>
                </div>

                <div v-if="detailPaper.venue" class="kss-detail__meta-item">
                  <span class="kss-label kss-label--xs">Venue</span>
                  <span class="kss-detail__meta-val kss-detail__meta-val--italic">{{ venueDisplay(detailPaper) }}</span>
                </div>

                <!-- Stats -->
                <div class="kss-detail__stats">
                  <div class="kss-detail__stat">
                    <p class="kss-label kss-label--xs">Year</p>
                    <p class="kss-detail__stat-num">{{ detailPaper.year ?? '—' }}</p>
                  </div>
                  <div class="kss-detail__stat kss-detail__stat--border">
                    <p class="kss-label kss-label--xs">Cited By</p>
                    <p class="kss-detail__stat-num kss-detail__stat-num--accent">{{ formatCitations(detailPaper.cited_by_count) }}</p>
                  </div>
                  <div class="kss-detail__stat">
                    <p class="kss-label kss-label--xs">{{ phase === 'graph' ? 'Connections' : 'Similarity' }}</p>
                    <p class="kss-detail__stat-num kss-detail__stat-num--primary">
                      <template v-if="phase === 'graph'">
                        {{ graphEdges.filter(e => e.source === detailPaper.openalex_id || e.target === detailPaper.openalex_id).length }}
                      </template>
                      <template v-else>
                        {{ detailPaper.similarity_score != null ? (detailPaper.similarity_score * 100).toFixed(0) + '%' : '—' }}
                      </template>
                    </p>
                  </div>
                </div>
              </div>

              <div class="kss-detail__spacer" />

              <!-- Bottom group: abstract + tags + actions -->
              <div class="kss-detail__bottom">
                <!-- Abstract -->
                <section v-if="detailPaper.abstract" class="kss-detail__section">
                  <div class="kss-detail__section-head">
                    <h3 class="kss-label">Abstract</h3>
                    <button
                      class="kss-translate-btn"
                      :disabled="isPending(detailPaper.abstract)"
                      @click="toggleTranslate(detailPaper.abstract)"
                    >
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M5 8l6 6M4 6h7M2 4h7m6 16-3-8-3 8m0 0h6M21 4c-2 5-5 8.5-9 11"/>
                      </svg>
                      {{ showTranslated ? 'Hide Translation' : (isPending(detailPaper.abstract) ? 'Translating…' : '中文') }}
                    </button>
                  </div>
                  <!-- Original Abstract -->
                  <div class="kss-detail__abstract">
                    <div class="kss-detail__abstract-bar" />
                    <div class="kss-detail__abstract-content">
                      <span class="kss-label kss-label--xs" style="display:block;margin-bottom:6px;color:#6e7979">Original</span>
                      <p class="kss-detail__abstract-text">
                        {{ detailPaper.abstract }}
                      </p>
                    </div>
                  </div>
                  <!-- Chinese Translation -->
                  <div v-if="showTranslated && translatedAbstract" class="kss-detail__abstract" style="margin-top:16px">
                    <div class="kss-detail__abstract-bar" style="background:#00595c" />
                    <div class="kss-detail__abstract-content">
                      <span class="kss-label kss-label--xs" style="display:block;margin-bottom:6px;color:#00595c">中文翻译</span>
                      <p class="kss-detail__abstract-text">
                        {{ translatedAbstract }}
                      </p>
                    </div>
                  </div>
                </section>

                <!-- Topics + Keywords + Concepts -->
                <div class="kss-detail__tag-groups">
                  <div v-if="detailPaper.topics?.length" class="kss-detail__tag-group">
                    <span class="kss-label kss-label--xs">Topics</span>
                    <div class="kss-detail__tag-list">
                      <span v-for="t in detailPaper.topics.slice(0, 6)" :key="t.id" class="kss-tag kss-tag--topic">{{ t.display_name }}</span>
                    </div>
                  </div>
                  <div v-if="detailPaper.keywords?.length" class="kss-detail__tag-group">
                    <span class="kss-label kss-label--xs">Keywords</span>
                    <div class="kss-detail__tag-list">
                      <span v-for="k in detailPaper.keywords.slice(0, 8)" :key="k.display_name" class="kss-tag kss-tag--keyword">{{ k.display_name }}</span>
                    </div>
                  </div>
                  <div v-if="detailPaper.concepts?.length" class="kss-detail__tag-group">
                    <span class="kss-label kss-label--xs">Concepts</span>
                    <div class="kss-detail__tag-list">
                      <span v-for="c in detailPaper.concepts.slice(0, 6)" :key="c.id" class="kss-tag kss-tag--concept">{{ c.display_name }}</span>
                    </div>
                  </div>
                </div>

                <!-- Actions -->
                <div class="kss-detail__actions">
                  <!-- Add to Collection (only in graph phase) -->
                  <div v-if="phase === 'graph'" class="kss-collection-action">
                    <button
                      class="kss-detail__action-link"
                      :disabled="isAddingToCollection"
                      @click="showCollectionDropdown = !showCollectionDropdown"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" />
                        <polyline points="17 21 17 13 7 13 7 21" />
                        <polyline points="7 3 7 8 15 8" />
                      </svg>
                      {{ isAddingToCollection ? 'Adding…' : 'Add to Collection' }}
                    </button>
                    <!-- Dropdown -->
                    <div v-if="showCollectionDropdown" class="kss-collection-dropdown">
                      <div v-if="collections.length === 0" class="kss-collection-dropdown__empty">
                        No collections found
                      </div>
                      <button
                        v-for="col in collections"
                        :key="col.id"
                        class="kss-collection-dropdown__item"
                        @click="addToCollection(col.id, col.name)"
                      >
                        {{ col.name }}
                      </button>
                    </div>
                    <!-- Success/Error Messages -->
                    <div v-if="addToCollectionSuccess" class="kss-collection-message kss-collection-message--success">
                      {{ addToCollectionSuccess }}
                    </div>
                    <div v-if="addToCollectionError" class="kss-collection-message kss-collection-message--error">
                      {{ addToCollectionError }}
                    </div>
                  </div>

                  <a
                    v-if="detailPaper.oa_url"
                    :href="detailPaper.oa_url"
                    target="_blank" rel="noopener"
                    class="kss-detail__action-link"
                  >
                    Read Paper
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3" />
                    </svg>
                  </a>
                  <a
                    :href="detailPaper.openalex_url ?? `https://openalex.org/${detailPaper.openalex_id}`"
                    target="_blank" rel="noopener"
                    class="kss-detail__action-link kss-detail__action-link--muted"
                  >
                    OpenAlex
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3" />
                    </svg>
                  </a>
                </div>
              </div>
            </div>
          </aside>

        </div><!-- /.kss-body -->
      </div><!-- /.kss-layout -->
    </Transition>

  </div><!-- /.kss-page -->
</template>

<style scoped>
/* ── Root ── */
.kss-page {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100dvh;
  overflow: hidden;
  background: var(--color-bg, #f9f9f6);
}

/* ══ SPOTLIGHT ══════════════════════════════════════════════ */
.kss-spotlight {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg, #f9f9f6);
  z-index: 20;
}

.kss-spotlight__inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  width: min(90vw, 600px);
  transform: translateY(-30%);
}

.kss-spotlight__logo {
  width: 52px;
  height: 52px;
  object-fit: contain;
  margin-bottom: 8px;
}

.kss-spotlight__brand {
  font: 700 2rem/1 var(--font-display, 'Playfair Display', serif);
  font-style: italic;
  color: var(--color-primary, #00595c);
  margin-bottom: 4px;
}

.kss-spotlight__sub {
  font: 400 0.75rem/1 var(--font-sans, 'Inter', sans-serif);
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: #9eacac;
  margin-bottom: 20px;
}

.kss-spotlight__box {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 14px 20px;
  background: #fff;
  border: 1px solid #e2e3e0;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(26,26,26,0.08), 0 1px 4px rgba(26,26,26,0.06);
  transition: box-shadow 0.2s, border-color 0.2s;
}
.kss-spotlight__box:focus-within {
  border-color: #00595c;
  box-shadow: 0 4px 24px rgba(0,89,92,0.12), 0 0 0 3px rgba(0,89,92,0.08);
}
.kss-spotlight__box--loading { opacity: 0.7; }

.kss-spotlight__icon {
  width: 20px;
  height: 20px;
  color: #00595c;
  flex-shrink: 0;
}

.kss-spotlight__input {
  flex: 1;
  border: none;
  outline: none;
  background: none;
  font: 400 1.05rem/1.4 var(--font-serif, 'Noto Serif', serif);
  color: #1a1c1b;
}
.kss-spotlight__input::placeholder { color: #9eacac; }
.kss-spotlight__input:disabled { opacity: 0.5; }

.kss-spotlight__kbd {
  flex-shrink: 0;
  padding: 3px 8px;
  font: 500 0.7rem/1 var(--font-mono, monospace);
  color: #6e7979;
  background: #f4f4f1;
  border: 1px solid #e2e3e0;
  border-radius: 4px;
}

.kss-spotlight__spinner {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  border: 2px solid #e2e3e0;
  border-top-color: #00595c;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.kss-spotlight__hint {
  font: 400 0.6875rem/1 var(--font-sans, sans-serif);
  color: #9eacac;
  margin-top: 8px;
}

.kss-spotlight__error {
  font: 400 0.8125rem/1.4 var(--font-serif, serif);
  color: #ba1a1a;
  margin-top: 8px;
}

/* ══ THREE-COLUMN LAYOUT ════════════════════════════════════ */
.kss-layout {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  overflow: hidden;
}

/* ── Nav ── */
.kss-nav {
  display: flex;
  align-items: center;
  gap: 24px;
  height: 40px;
  padding: 0 20px;
  border-bottom: 1px solid #e2e3e0;
  background: rgba(250,250,247,0.95);
  backdrop-filter: blur(8px);
  flex-shrink: 0;
}

.kss-nav__brand {
  display: flex;
  align-items: center;
  gap: 7px;
  font: 700 0.95rem/1 var(--font-display, serif);
  font-style: italic;
  color: var(--color-primary, #00595c);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}
.kss-nav__brand:hover { opacity: 0.75; }
.kss-nav__brand-icon {
  width: 22px;
  height: 22px;
  object-fit: contain;
  flex-shrink: 0;
}

.kss-nav__modes { display: flex; gap: 16px; }
.kss-nav__mode {
  font: 400 0.75rem/1 var(--font-serif, serif);
  color: #6e7979;
  background: none; border: none;
  padding: 3px 0;
  cursor: pointer;
  border-bottom: 2px solid transparent;
}
.kss-nav__mode:hover { color: #00595c; }
.kss-nav__mode--active { color: #00595c; border-bottom-color: #00595c; font-weight: 600; }

.kss-nav__back {
  margin-left: auto;
  font: 400 0.75rem/1 var(--font-sans, sans-serif);
  color: #6e7979;
  background: none; border: none; cursor: pointer;
}
.kss-nav__back:hover { color: #00595c; }

/* ── Body ── */
.kss-body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* ── Left panel ── */
.kss-left {
  width: 292px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #eeeeeb;
  border-right: 1px solid #e2e3e0;
  overflow: hidden;
}

.kss-left__search {
  padding: 12px 12px 0;
  flex-shrink: 0;
}

.kss-search-field {
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 2px solid #bec9c9;
  padding-bottom: 6px;
  transition: border-color 0.15s;
}
.kss-search-field:focus-within { border-bottom-color: #00595c; }
.kss-search-input {
  flex: 1; border: none; outline: none; background: none;
  font: 400 0.8125rem/1.4 var(--font-serif, serif);
  font-style: italic;
  color: #00595c;
}
.kss-search-input::placeholder { color: #9eacac; }

.kss-left__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px 4px;
  flex-shrink: 0;
}

.kss-left__header-actions { display: flex; gap: 8px; }
.kss-link-btn {
  background: none; border: none; padding: 0;
  font: 400 0.625rem/1 var(--font-sans, sans-serif);
  text-transform: uppercase; letter-spacing: 0.1em;
  color: #6e7979; cursor: pointer;
}
.kss-link-btn:hover { color: #00595c; }

.kss-label {
  font: 400 0.5625rem/1 var(--font-sans, sans-serif);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #6e7979;
}
.kss-label--xs { font-size: 0.5rem; }

.kss-list {
  flex: 1; overflow-y: auto;
  padding: 0 8px 8px; margin: 0;
  list-style: none;
  display: flex; flex-direction: column; gap: 4px;
}
.kss-list::-webkit-scrollbar { width: 4px; }
.kss-list::-webkit-scrollbar-thumb { background: rgba(110,121,121,0.2); border-radius: 9999px; }

/* Paper card (compact — phase 2 results + graph split/map mode) */
.kss-card {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  padding: 10px;
  background: #fff;
  border: 1px solid rgba(190,201,201,0.15);
  border-radius: 2px;
  cursor: pointer;
  transition: border-color 0.12s, background 0.12s;
  list-style: none;
}
.kss-card:hover { border-color: #00595c; }
.kss-card--checked { background: #f0fafa; border-left: 3px solid #00595c; }
.kss-card--focused { background: #f4fafa; outline: 1px solid #bde0e0; }
.kss-card--checked.kss-card--focused { background: #e8f5f5; }
.kss-card--selected { background: #e8f4f4; border-left: 3px solid #0d7377; }
.kss-card--origin { border-left: 3px solid #7f6421; }

.kss-card__check { flex-shrink: 0; padding-top: 1px; cursor: pointer; padding: 4px; margin: -4px; }

.kss-checkbox {
  width: 14px; height: 14px;
  border: 1.5px solid #bec9c9;
  border-radius: 2px;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.12s, border-color 0.12s;
}
.kss-checkbox--on { background: #00595c; border-color: #00595c; }

.kss-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  margin-top: 3px;
}
.kss-dot--origin { background: #00595c; box-shadow: 0 0 0 2px rgba(0,89,92,0.2); }
.kss-dot--ref { background: #9eacac; }

.kss-card__body { flex: 1; min-width: 0; }
.kss-card__year {
  font: 400 0.5625rem/1 var(--font-mono, monospace);
  color: #7f6421; margin-bottom: 3px;
}
.kss-card__title {
  font: 600 0.75rem/1.3 var(--font-serif, serif);
  color: #1a1c1b;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; margin-bottom: 3px;
}
.kss-card:hover .kss-card__title,
.kss-card--checked .kss-card__title,
.kss-card--selected .kss-card__title { color: #00595c; }
.kss-card__author {
  font: 400 0.5625rem/1 var(--font-sans, sans-serif);
  text-transform: uppercase; letter-spacing: 0.06em; color: #6e7979;
}
.kss-card__venue {
  font: 400 0.5rem/1.2 var(--font-sans, sans-serif);
  color: #9eacac;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Build footer */
.kss-build-footer {
  flex-shrink: 0;
  padding: 10px 12px;
  border-top: 1px solid #e2e3e0;
  background: #e8e8e5;
}
.kss-build-btn {
  width: 100%;
  padding: 10px;
  background: #00595c;
  color: #fff;
  border: none; border-radius: 2px;
  font: 600 0.625rem/1 var(--font-sans, sans-serif);
  letter-spacing: 0.18em; text-transform: uppercase;
  cursor: pointer;
  transition: background 0.15s;
}
.kss-build-btn:hover:not(:disabled) { background: #0d7377; }
.kss-build-btn:disabled { opacity: 0.5; cursor: default; }
.kss-build-error {
  margin-top: 6px;
  font: 400 0.625rem/1.4 var(--font-serif, serif);
  color: #ba1a1a;
}

/* ── Resize handle ── */
.kss-handle {
  width: 6px;
  flex-shrink: 0;
  cursor: col-resize;
  background: transparent;
  transition: background 0.15s;
  position: relative;
  z-index: 5;
}
.kss-handle::after {
  content: '';
  position: absolute;
  top: 0; bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  background: #e2e3e0;
}
.kss-handle:hover::after,
.kss-handle:active::after {
  background: #00595c;
}

/* ── Origin section (graph phase) ── */
.kss-origin-section {
  flex-shrink: 0;
  border-bottom: 1px solid #e2e3e0;
  background: rgba(0,89,92,0.03);
}
.kss-origin-section__header {
  padding: 6px 12px 4px;
}
.kss-origin-list {
  list-style: none;
  margin: 0;
  padding: 0 8px 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 120px;
  overflow-y: auto;
}
.kss-origin-list::-webkit-scrollbar { width: 3px; }
.kss-origin-list::-webkit-scrollbar-thumb { background: rgba(0,89,92,0.2); border-radius: 9999px; }
.kss-origin-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 5px 6px;
  border-radius: 2px;
  cursor: pointer;
  transition: background 0.1s;
}
.kss-origin-item:hover { background: rgba(0,89,92,0.06); }
.kss-origin-item--selected { background: rgba(13,115,119,0.1); }
.kss-origin-dot {
  flex-shrink: 0;
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #00595c;
  box-shadow: 0 0 0 2px rgba(0,89,92,0.2);
  margin-top: 3px;
}
.kss-origin-item__title {
  font: 500 0.6875rem/1.3 var(--font-serif, serif);
  color: #1a1c1b;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── List mode cards ── */
.kss-card-list {
  padding: 14px 16px;
  background: #fff;
  border: 1px solid rgba(190,201,201,0.15);
  border-radius: 2px;
  cursor: pointer;
  list-style: none;
  transition: border-color 0.12s;
}
.kss-card-list:hover { border-color: #00595c; }
.kss-card-list--selected { background: #e8f4f4; border-left: 3px solid #0d7377; }

.kss-card-list__header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 5px;
}
.kss-card-list__author {
  font: 500 0.75rem/1 var(--font-sans);
  color: #3e4949;
}
.kss-card-list__year {
  font: 400 0.625rem/1 var(--font-mono);
  color: #7f6421;
}
.kss-card-list__title {
  font: 600 0.9rem/1.3 var(--font-serif);
  color: #1a1c1b;
  margin-bottom: 4px;
}
.kss-card-list--selected .kss-card-list__title { color: #00595c; }
.kss-card-list__venue {
  font: 400 0.6875rem/1 var(--font-sans);
  color: #6e7979;
  font-style: italic;
  margin-bottom: 8px;
}
.kss-card-list__divider {
  border: none;
  border-top: 1px solid #e8e8e5;
  margin-bottom: 8px;
}
.kss-card-list__abstract {
  font: 400 0.75rem/1.6 var(--font-serif);
  color: #3e4949;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Center ── */
.kss-center {
  flex: 1; min-width: 0;
  display: flex; flex-direction: column;
  border-right: 1px solid #e2e3e0;
  background: var(--color-bg, #f9f9f6);
}

.kss-center--empty {
  align-items: center;
  justify-content: center;
}

.kss-center-placeholder {
  display: flex; flex-direction: column; align-items: center; gap: 16px;
  opacity: 0.5;
}
.kss-center-placeholder__text {
  font: 400 0.875rem/1.7 var(--font-serif, serif);
  font-style: italic;
  color: #6e7979;
  text-align: center;
}

.kss-center__header {
  display: flex; align-items: flex-end; justify-content: space-between;
  padding: 16px 20px 6px;
  flex-shrink: 0;
}
.kss-center__title {
  font: 700 1.25rem/1.1 var(--font-display, serif);
  font-style: italic;
  color: #00595c;
}
.kss-center__sub {
  font: 400 0.5625rem/1 var(--font-mono, monospace);
  text-transform: uppercase; letter-spacing: 0.08em; color: #9eacac;
  margin-top: 3px;
}
.kss-center__legend {
  display: flex; align-items: center; gap: 14px;
  font: 400 0.5625rem/1 var(--font-sans, sans-serif);
  text-transform: uppercase; letter-spacing: 0.1em; color: #6e7979;
}
.kss-legend-item { display: flex; align-items: center; gap: 5px; }

.kss-center__graph { flex: 1; min-height: 0; }

.kss-center__footer {
  padding: 5px 20px 8px;
  font: 400 0.5rem/1 var(--font-sans, sans-serif);
  text-transform: uppercase; letter-spacing: 0.12em; color: #bec9c9;
  flex-shrink: 0;
}

/* ── Right detail ── */
.kss-right {
  flex-shrink: 0;
  overflow-y: auto;
  background: #fff;
}
.kss-right::-webkit-scrollbar { width: 4px; }
.kss-right::-webkit-scrollbar-thumb { background: rgba(110,121,121,0.18); border-radius: 9999px; }

.kss-right__empty {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  height: 100%; gap: 10px; padding: 32px;
}
.kss-right__empty-icon { font-size: 40px; color: #bec9c9; }
.kss-right__empty p {
  font: 400 0.8125rem/1.6 var(--font-serif, serif);
  font-style: italic; color: #9eacac; text-align: center;
}

/* Detail panel layout */
.kss-detail {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  padding: 24px 22px 32px;
  gap: 0;
}

.kss-detail__top {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.kss-detail__spacer {
  flex: 1;
  min-height: 16px;
}

.kss-detail__bottom {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.kss-detail__eyebrow { display: flex; align-items: center; gap: 8px; }
.kss-detail__rule { display: block; width: 28px; height: 1px; background: #bec9c9; }
.kss-detail__tag {
  padding: 2px 8px;
  font: 600 0.5625rem/1.4 var(--font-sans, sans-serif);
  text-transform: uppercase; letter-spacing: 0.1em;
  border-radius: 2px;
}
.kss-detail__tag--origin { background: rgba(0,89,92,0.1); color: #00595c; }
.kss-detail__tag--ref { background: rgba(94,94,94,0.1); color: #5e5e5e; }

.kss-detail__title {
  font: 700 1.15rem/1.25 var(--font-display, serif);
  color: #1a1c1b; margin: 0;
}

/* Authors */
.kss-detail__authors { display: flex; flex-direction: column; }

.kss-detail__author-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 6px;
  align-items: center;
}
.kss-detail__author-link {
  font: 400 0.8125rem/1.3 var(--font-serif, serif);
  color: #0d7377;
  text-decoration: none;
  border-bottom: 1px solid rgba(13,115,119,0.3);
  transition: border-color 0.12s, color 0.12s;
}
.kss-detail__author-link:hover {
  color: #00595c;
  border-bottom-color: #00595c;
}
.kss-detail__author-plain {
  font: 400 0.8125rem/1.3 var(--font-serif, serif);
  color: #3e4949;
}
.kss-detail__author-plain + .kss-detail__author-plain::before {
  content: ', ';
}

.kss-detail__meta-item { display: flex; flex-direction: column; gap: 3px; }
.kss-detail__meta-val { font: 400 0.8125rem/1.3 var(--font-serif, serif); color: #1a1c1b; }
.kss-detail__meta-val--italic { font-style: italic; }

.kss-detail__stats {
  display: grid; grid-template-columns: repeat(3,1fr);
  border-top: 1px solid #e2e3e0; border-bottom: 1px solid #e2e3e0;
  padding: 12px 0;
}
.kss-detail__stat { text-align: center; padding: 0 6px; }
.kss-detail__stat--border { border-left: 1px solid #e2e3e0; border-right: 1px solid #e2e3e0; }
.kss-detail__stat-num {
  font: 700 1.1rem/1 var(--font-mono, monospace); color: #3e4949; margin-top: 4px;
}
.kss-detail__stat-num--primary { color: #00595c; }
.kss-detail__stat-num--accent { color: #7f6421; }

.kss-detail__section {}
.kss-detail__section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.kss-translate-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 7px;
  font: 500 0.5rem/1 var(--font-sans, sans-serif);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #6e7979;
  background: none;
  border: 1px solid #d4d8d8;
  border-radius: 2px;
  cursor: pointer;
  transition: color 0.12s, border-color 0.12s;
}
.kss-translate-btn:hover:not(:disabled) { color: #0d7377; border-color: #0d7377; }
.kss-translate-btn:disabled { opacity: 0.5; cursor: default; }
.kss-detail__abstract { position: relative; padding-left: 12px; }
.kss-detail__abstract-bar {
  position: absolute; left: 0; top: 0; bottom: 0; width: 2px;
  background: rgba(127,100,33,0.2);
}
.kss-detail__abstract-text {
  font: 400 0.8125rem/1.7 var(--font-serif, serif);
  font-style: italic; color: #3e4949;
}

/* Tag groups */
.kss-detail__tag-groups {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.kss-detail__tag-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.kss-detail__tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.kss-tag {
  padding: 2px 7px;
  font: 400 0.5625rem/1.4 var(--font-sans, sans-serif);
  border-radius: 2px;
}
.kss-tag--topic { background: rgba(13,115,119,0.08); color: #00595c; }
.kss-tag--keyword { background: rgba(127,100,33,0.1); color: #7f6421; }
.kss-tag--concept { background: rgba(94,94,94,0.09); color: #3e4949; }

.kss-detail__actions { display: flex; flex-direction: column; gap: 2px; border-top: 1px solid #e2e3e0; padding-top: 12px; }
.kss-detail__action-link {
  display: flex; align-items: center; justify-content: space-between;
  padding: 9px 0; border-bottom: 1px solid #7f6421;
  font: 600 0.625rem/1 var(--font-sans, sans-serif);
  letter-spacing: 0.14em; text-transform: uppercase;
  color: #7f6421; text-decoration: none;
  transition: opacity 0.15s;
}
.kss-detail__action-link--muted { border-color: #bec9c9; color: #6e7979; }
.kss-detail__action-link:hover { opacity: 0.65; }
.kss-detail__action-link:disabled { opacity: 0.4; cursor: not-allowed; }

/* Collection dropdown */
.kss-collection-action {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kss-collection-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: #fff;
  border: 1px solid #d4d5d2;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  max-height: 200px;
  overflow-y: auto;
  z-index: 10;
}

.kss-collection-dropdown__empty {
  padding: 12px;
  font: 400 0.6875rem/1.4 var(--font-sans, sans-serif);
  color: #9eacac;
  text-align: center;
}

.kss-collection-dropdown__item {
  display: block;
  width: 100%;
  padding: 10px 12px;
  font: 400 0.6875rem/1.4 var(--font-sans, sans-serif);
  color: #3e4949;
  text-align: left;
  background: none;
  border: none;
  border-bottom: 1px solid #f4f4f1;
  cursor: pointer;
  transition: background 0.15s;
}

.kss-collection-dropdown__item:last-child {
  border-bottom: none;
}

.kss-collection-dropdown__item:hover {
  background: #f9f9f6;
}

.kss-collection-message {
  padding: 8px 10px;
  font: 400 0.6875rem/1.4 var(--font-sans, sans-serif);
  border-radius: 3px;
}

.kss-collection-message--success {
  background: rgba(13,115,119,0.08);
  color: #00595c;
}

.kss-collection-message--error {
  background: rgba(180,50,50,0.08);
  color: #b43232;
}

/* ══ TRANSITIONS ═══════════════════════════════════════════ */
.kss-fade-enter-active, .kss-fade-leave-active { transition: opacity 0.25s; }
.kss-fade-enter-from, .kss-fade-leave-to { opacity: 0; }

.kss-slide-enter-active { transition: opacity 0.3s 0.1s, transform 0.3s 0.1s; }
.kss-slide-enter-from { opacity: 0; transform: translateY(12px); }
.kss-slide-leave-active { transition: opacity 0.2s; }
.kss-slide-leave-to { opacity: 0; }
</style>
