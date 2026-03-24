<script setup lang="ts">
/**
 * Discovery Explorer Page — Curated research collection browsing.
 *
 * Composes:
 *  - TopicsWall: Magazine-cover topic collection cards
 *  - QueryComposer: Natural-language research frontier input
 *  - FacetWall: Sticky sidebar with toggleable facets
 *  - RecommendationStream: Paper recommendation cards
 *  - VenueShelf: Top venues sidebar
 *  - GraphTeaser: Concept graph SVG preview
 *  - SavedExplorations: Saved discovery queries
 *  - NextActionsBar: Fixed bottom action toolbar
 */
import type { TopicCover } from '~/components/discover/TopicsWall.vue'
import type { FacetGroup } from '~/components/discover/FacetWall.vue'
import type { RecommendedPaper } from '~/components/discover/RecommendationStream.vue'
import type { VenueItem } from '~/components/discover/VenueShelf.vue'
import type { GraphNode, GraphEdge } from '~/components/discover/GraphTeaser.vue'
import type { SavedExploration } from '~/components/discover/SavedExplorations.vue'

definePageMeta({
  layout: 'default',
  title: 'Discovery Explorer',
})

const { t } = useTranslation()

useHead({
  title: 'Discover — Kaleidoscope',
  meta: [
    { name: 'description', content: 'Explore curated research collections and discover papers with intelligent filtering.' },
  ],
})

// ─── Mock data ────────────────────────────────────────────────
const topicCovers: TopicCover[] = [
  {
    id: 'tc-1',
    label: 'Featured Collection',
    title: 'Scientific Agents with Evidence Tracing',
    subtitle: 'End-to-end pipelines that ground agent outputs in citable evidence',
    count: 142,
    accent: 'teal',
  },
  {
    id: 'tc-2',
    label: 'Hot This Month',
    title: 'Multimodal Clinical Reasoning',
    subtitle: 'Vision-language models meeting diagnostic workflows',
    count: 87,
    accent: 'gold',
  },
  {
    id: 'tc-3',
    label: 'Emerging',
    title: 'Efficient Long Context',
    subtitle: 'Attention alternatives and context compression for 128K+ windows',
    count: 96,
    accent: 'teal',
  },
  {
    id: 'tc-4',
    label: 'Controversy',
    title: 'Evaluation Failures & Benchmark Leakage',
    subtitle: "When leaderboard gains don't survive external validation",
    count: 54,
    accent: 'gold',
  },
]

const queryPlaceholder =
  'Find 2024–2026 papers on citation-grounded research agents that report human evaluation, release code, and discuss failure analysis.'

const querySuggestions = [
  'Evidence tracing in RAG',
  'Claim extraction biomedical',
  'Long-context benchmark leakage',
  'Clinical VLM external validation',
]

const facetGroups = ref<FacetGroup[]>([
  {
    title: 'Year',
    options: [
      { label: '2026', count: 24, active: true },
      { label: '2025', count: 41, active: true },
      { label: '2024', count: 53, active: false },
    ],
  },
  {
    title: 'Task',
    options: [
      { label: 'Evidence tracing', count: 38, active: true },
      { label: 'Claim extraction', count: 27, active: false },
      { label: 'Benchmark audit', count: 19, active: false },
    ],
  },
  {
    title: 'Venue',
    options: [
      { label: 'ACL', count: 18, active: false },
      { label: 'NeurIPS', count: 14, active: false },
      { label: 'Nature MI', count: 6, active: false },
      { label: 'JAMIA', count: 8, active: false },
    ],
  },
  {
    title: 'Code',
    options: [
      { label: 'Open source', count: 42, active: true },
      { label: 'Partial', count: 23, active: false },
      { label: 'None', count: 53, active: false },
    ],
  },
])

const recommendations: RecommendedPaper[] = [
  {
    id: 'rec-1',
    eyebrow: 'Evidence Rich',
    title: 'ClaimMiner: Atomic Claim Extraction for Biomedical Papers with Evidence Alignment',
    abstract:
      'A pipeline for decomposing biomedical papers into atomic, verifiable claims linked to supporting evidence sentences.',
    venue: 'EMNLP 2025',
    score: 0.94,
    tags: ['Code', 'Human eval'],
    strong: true,
  },
  {
    id: 'rec-2',
    eyebrow: 'Benchmark',
    title: 'RAGBench-Sci: Failure Modes of Citation-Grounded Retrieval',
    abstract:
      'Systematic analysis of where citation-grounded RAG fails: hallucinated citations, partial quotes, and context window overflow.',
    venue: 'ACL 2025',
    score: 0.89,
    tags: ['Open data'],
    strong: false,
  },
  {
    id: 'rec-3',
    eyebrow: 'Clinical',
    title: 'MedJudge-External: Reassessing Medical QA with Hospital-held Data',
    abstract:
      'External validation study showing 60% of MedQA leaderboard gains disappear under hospital-held test sets.',
    venue: 'Nature MI 2025',
    score: 0.86,
    tags: ['External eval'],
    strong: true,
  },
  {
    id: 'rec-4',
    eyebrow: 'Agents',
    title: 'ToolChain Scholar: Agents under Long-Context Constraints',
    abstract:
      'Evaluating tool-augmented scientific agents when context windows are constrained to 4K tokens.',
    venue: 'NeurIPS 2025',
    score: 0.81,
    tags: ['Code'],
    strong: false,
  },
  {
    id: 'rec-5',
    eyebrow: 'Survey',
    title: 'Citation Graphs Meet Retrieval: A Comprehensive Survey',
    abstract:
      'A survey covering graph-augmented retrieval for academic search, covering 180+ papers from 2020-2025.',
    venue: 'ACM Computing Surveys',
    score: 0.78,
    tags: [],
    strong: false,
  },
  {
    id: 'rec-6',
    eyebrow: 'Negative Result',
    title: 'When More Context Hurts: Failure Analysis for 128K Scientific QA',
    abstract:
      'Documenting systematic performance drops when scaling context beyond 32K tokens in scientific QA benchmarks.',
    venue: 'EMNLP 2025 Findings',
    score: 0.76,
    tags: ['Reproducible'],
    strong: false,
  },
]

const venueItems: VenueItem[] = [
  { id: 'ven-1', name: 'ACL 2025', count: 18 },
  { id: 'ven-2', name: 'NeurIPS 2025', count: 14 },
  { id: 'ven-3', name: 'Nature Machine Intelligence', count: 6 },
]

const graphNodes: GraphNode[] = [
  { id: 'center', label: 'Citation-grounded agents', cx: 132, cy: 76, r: 10, type: 'primary' },
  { id: 'rrf', label: 'RRF', cx: 44, cy: 40, r: 6, type: 'bridge' },
  { id: 'tool', label: 'Tool use', cx: 220, cy: 36, r: 6, type: 'bridge' },
  { id: 'evidence', label: 'Evidence QA', cx: 56, cy: 120, r: 7, type: 'primary' },
  { id: 'validation', label: 'External validation', cx: 216, cy: 124, r: 6, type: 'bridge' },
]

const graphEdges: GraphEdge[] = [
  { from: 'center', to: 'rrf' },
  { from: 'center', to: 'tool' },
  { from: 'center', to: 'evidence' },
  { from: 'center', to: 'validation' },
  { from: 'evidence', to: 'rrf' },
]

const savedExplorations: SavedExploration[] = [
  { id: 'se-1', title: 'Clinical agent papers with human eval', date: 'Mar 20', pinned: true },
  { id: 'se-2', title: 'Negative results in long-context QA', date: 'Mar 18', pinned: false },
  { id: 'se-3', title: 'Evidence extraction for biomedical reviews', date: 'Mar 15', pinned: false },
]

// ─── Interactive state ────────────────────────────────────────
const selectedCount = ref(0)
const queryText = ref('')

// ─── Handlers ─────────────────────────────────────────────────
function handleTopicClick(topic: TopicCover) {
  console.log('[Discover] Topic clicked:', topic.title)
  navigateTo(`/search?topic=${encodeURIComponent(topic.title)}`)
}

function handleFacetToggle(group: string, option: string, active: boolean) {
  const g = facetGroups.value.find(fg => fg.title === group)
  if (g) {
    const opt = g.options.find(o => o.label === option)
    if (opt) opt.active = active
  }
}

function handlePaperClick(paper: RecommendedPaper) {
  console.log('[Discover] Paper clicked:', paper.title)
  navigateTo(`/papers/${paper.id}`)
}

function handlePaperSave(paper: RecommendedPaper) {
  console.log('[Discover] Paper saved:', paper.title)
}

function handlePaperCompare(paper: RecommendedPaper) {
  console.log('[Discover] Paper compared:', paper.title)
}

function handleQuerySubmit(query: string) {
  console.log('[Discover] Query submitted:', query)
  navigateTo(`/search?q=${encodeURIComponent(query)}`)
}

function handleVenueClick(venue: VenueItem) {
  navigateTo(`/search?venue=${encodeURIComponent(venue.name)}`)
}

function handleGraphExplore() {
  navigateTo('/insights/landscape')
}

function handleExplorationReopen(exploration: SavedExploration) {
  console.log('[Discover] Reopening exploration:', exploration.title)
  queryText.value = exploration.title
}
</script>

<template>
  <div class="ks-discover">
    <!-- ═══ Row 1: Topics Wall + Query Composer ═══ -->
    <div class="ks-discover__row ks-discover__row--top">
      <DiscoverTopicsWall
        :topics="topicCovers"
        @topic-click="handleTopicClick"
      />
      <DiscoverQueryComposer
        v-model="queryText"
        :placeholder="queryPlaceholder"
        :suggestions="querySuggestions"
        @submit="handleQuerySubmit"
      />
    </div>

    <!-- ═══ Row 2+: Facets + Stream + Sidebar ═══ -->
    <div class="ks-discover__row ks-discover__row--main">
      <DiscoverFacetWall
        :groups="facetGroups"
        @facet-toggle="handleFacetToggle"
      />

      <DiscoverRecommendationStream
        :papers="recommendations"
        @paper-click="handlePaperClick"
        @save="handlePaperSave"
        @compare="handlePaperCompare"
      />

      <!-- Right sidebar stack -->
      <div class="ks-discover__sidebar-right">
        <DiscoverVenueShelf
          :venues="venueItems"
          @venue-click="handleVenueClick"
        />
        <DiscoverGraphTeaser
          :nodes="graphNodes"
          :edges="graphEdges"
          @explore="handleGraphExplore"
        />
        <DiscoverSavedExplorations
          :explorations="savedExplorations"
          @reopen="handleExplorationReopen"
        />
      </div>
    </div>

    <!-- ═══ Next Actions Bar (fixed bottom) ═══ -->
    <DiscoverNextActionsBar :selected-count="selectedCount" />
  </div>
</template>

<style scoped>
.ks-discover {
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding-bottom: 96px; /* Space for fixed action bar */
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

/* ─── Responsive ──────────────────────────────────────────── */
@media (max-width: 1280px) {
  .ks-discover__row--main {
    grid-template-columns: 240px 1fr 240px;
    gap: 16px;
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
}
</style>
