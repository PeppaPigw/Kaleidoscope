<script setup lang="ts">
/**
 * Paper Profile Page — [paperId]
 *
 * Composes PaperFolio, ThesisLine, ClaimsLedger, MethodsResultsSlice,
 * FigureGallery, SupplementRail, ReproductionStatus, RelatedConstellation.
 */
import type { PaperContent, PaperHighlights, PaperLabels } from '~/composables/useApi'
import type { AnalysisItem } from '~/components/paper/DeepAnalysis.vue'
import type { OutlineItem } from '~/components/paper/AnalysisOutline.vue'
import type { PaperAuthor } from '~/components/paper/PaperFolio.vue'
import type { PaperClaim } from '~/components/paper/ClaimsLedger.vue'
import type { MethodItem, ResultItem } from '~/components/paper/MethodsResultsSlice.vue'
import type { PaperFigure } from '~/components/paper/FigureGallery.vue'
import type { SupplementItem } from '~/components/paper/supplements'
import type { ReproductionAttempt } from '~/components/paper/ReproductionStatus.vue'
import type { RelatedPaper } from '~/components/paper/RelatedConstellation.vue'
import { extractPaperSupplements } from '~/utils/paperSupplements'

definePageMeta({ layout: 'default' })

const { t } = useTranslation()

const route = useRoute()
const { apiFetch, getClaimsForPaper, getPaperContent, getPaperHighlights, getSimilarPapers } = useApi()
const paperId = computed(() => route.params.paperId as string)

useHead({
  title: 'Paper Profile — Kaleidoscope',
  meta: [
    { name: 'description', content: 'Detailed paper analysis with claims, methods, results, and reproducibility.' },
  ],
})

// ─── Fetch paper data from API ───────────────────────────────
type PaperDetailAuthor = {
  id?: string
  display_name?: string
  name?: string
  affiliation?: string | null
  position?: number
}

type PaperRawMetadata = {
  authors_parsed?: PaperDetailAuthor[] | null
  authors?: Array<string | PaperDetailAuthor> | null
  pdf_url?: string | null
  best_oa_url?: string | null
  github_url?: string | null
  code_url?: string | null
  artifact_links?: Array<{
    url?: string | null
    type?: string | null
    label?: string | null
  }> | null
}

type PaperDetailResponse = {
  id: string
  title: string
  abstract?: string | null
  doi?: string | null
  arxiv_id?: string | null
  published_at?: string | null
  citation_count?: number
  venue?: string
  has_full_text?: boolean
  authors?: PaperDetailAuthor[] | null
  raw_metadata?: PaperRawMetadata | null
}

const paperData = ref<PaperDetailResponse | null>(null)

const claims = ref<PaperClaim[]>([])
const figures = ref<PaperFigure[]>([])
const relatedPapers = ref<RelatedPaper[]>([])
const paperHighlights = ref<PaperHighlights | null>(null)
const paperContent = ref<PaperContent | null>(null)
const methodsResultHighlights = computed(
  () => paperHighlights.value?.highlights ?? [],
)

// ─── Mock data ───────────────────────────────────────────────
const mockAuthors: PaperAuthor[] = [
  { id: 'a1', name: 'Jiawei Liu', affiliation: 'Tsinghua University' },
  { id: 'a2', name: 'Xiaoming Wang', affiliation: 'Stanford University' },
  { id: 'a3', name: 'Hui Chen', affiliation: 'Google DeepMind' },
  { id: 'a4', name: 'Yafeng Zhang', affiliation: 'Tsinghua University' },
]

const authors = computed<PaperAuthor[]>(() => {
  const paper = paperData.value

  const structuredAuthors = [...(paper?.authors ?? [])]
    .sort((a, b) => (a.position ?? Number.MAX_SAFE_INTEGER) - (b.position ?? Number.MAX_SAFE_INTEGER))
    .map((author, index) => ({
      id: String(author.id ?? `author-${author.position ?? index}`),
      name: author.display_name ?? author.name ?? '',
      affiliation: author.affiliation ?? undefined,
    }))
    .filter(author => author.name)

  if (structuredAuthors.length > 0)
    return structuredAuthors

  const rawAuthors = paper?.raw_metadata?.authors_parsed ?? paper?.raw_metadata?.authors ?? []
  const parsedRawAuthors = rawAuthors
    .map((author, index) => {
      if (typeof author === 'string') {
        return { id: `raw-author-${index}`, name: author }
      }

      return {
        id: String(author.id ?? `raw-author-${index}`),
        name: author.display_name ?? author.name ?? '',
        affiliation: author.affiliation ?? undefined,
      }
    })
    .filter(author => author.name)

  return parsedRawAuthors.length > 0 ? parsedRawAuthors : mockAuthors
})

const methods: MethodItem[] = [
  { id: 'm1', name: 'SciBERT-Decomposer', description: 'Fine-tuned SciBERT for sentence-to-claim decomposition with NLI filtering.', type: 'model' },
  { id: 'm2', name: 'BioASQ-Claims', description: 'Extended BioASQ dataset with 12K manually annotated atomic claims.', type: 'dataset' },
  { id: 'm3', name: 'Evidence F1', description: 'F1 score measuring claim-evidence alignment accuracy.', type: 'metric' },
  { id: 'm4', name: 'RAG-Paragraph', description: 'Standard paragraph-level retrieval baseline.', type: 'baseline' },
]

const results: ResultItem[] = [
  { id: 'r1', metric: 'Evidence F1', value: '89.2%', comparison: 'RAG-Paragraph', delta: '+12.1%', positive: true },
  { id: 'r2', metric: 'Claim Precision', value: '94.7%', comparison: 'SciBERT-base', delta: '+8.3%', positive: true },
  { id: 'r3', metric: 'Claims/Paper', value: '47.3', positive: true },
  { id: 'r4', metric: 'Hallucination Reduction', value: '23.1%', comparison: 'Baseline RAG', delta: '-23.1%', positive: true },
]

const supplements = computed<SupplementItem[]>(() => {
  const paper = paperData.value
  if (!paper)
    return []

  return extractPaperSupplements({
    doi: paper.doi,
    arxivId: paper.arxiv_id,
    rawMetadata: paper.raw_metadata ?? null,
    remoteUrls: paperContent.value?.remote_urls ?? [],
    markdown: paperContent.value?.markdown ?? '',
  })
})

const reproAttempts: ReproductionAttempt[] = [
  { id: 'ra1', team: 'Allen AI (Semantic Scholar)', date: '2025-08', success: 'full', notes: 'Successfully reproduced main results within 1% margin on BioASQ benchmark.' },
  { id: 'ra2', team: 'UIUC NLP Lab', date: '2025-09', success: 'partial', notes: 'Reproduced claim extraction, but evidence alignment was 3% lower than reported.' },
]

function mapClaimStatus(status?: string): PaperClaim['status'] {
  switch (status) {
    case 'verified':
    case 'disputed':
      return status
    default:
      return 'unverified'
  }
}

watch(paperId, async id => {
  if (!id) {
    claims.value = []
    figures.value = []
    relatedPapers.value = []
    paperHighlights.value = null
    paperContent.value = null
    return
  }

  const [claimsResult, contentResult, similarResult, highlightsResult] = await Promise.allSettled([
    getClaimsForPaper(id),
    getPaperContent(id),
    getSimilarPapers(id, 5),
    getPaperHighlights(id),
  ])

  claims.value = claimsResult.status === 'fulfilled'
    ? (claimsResult.value.claims || []).map(claim => ({
        id: claim.id,
        text: claim.claim_text || '',
        category: claim.category || 'General',
        confidence: claim.confidence ?? 0.5,
        evidenceCount: 0,
        status: mapClaimStatus(claim.status),
      }))
    : []

  relatedPapers.value = similarResult.status === 'fulfilled'
    ? (similarResult.value.similar_papers || []).map(paper => ({
        id: paper.paper_id,
        title: paper.title || 'Untitled',
        venue: '(no venue)',
        year: 0,
        relationship: 'similar' as const,
        similarity: paper.score ?? 0,
      }))
    : []

  figures.value = contentResult.status === 'fulfilled'
    ? (contentResult.value.figures || []).map((fig, index) => ({
        id: fig.figure_id || `fig-${index}`,
        number: index + 1,
        caption: fig.caption || '',
        imageUrl: fig.image_url || '',
      }))
    : []

  paperContent.value = contentResult.status === 'fulfilled'
    ? contentResult.value
    : null

  paperHighlights.value = highlightsResult.status === 'fulfilled'
    ? highlightsResult.value
    : null
}, { immediate: true })

async function loadPaperData() {
  if (!paperId.value) {
    paperData.value = null
    return
  }

  try {
    paperData.value = await apiFetch<PaperDetailResponse>(`/papers/${paperId.value}`)
  } catch {
    paperData.value = null
  }
}

onMounted(() => {
  void loadPaperData()
  if (paperId.value) {
    void loadLabels(paperId.value)
    void loadDeepAnalysis(paperId.value)
  }
  window.addEventListener('scroll', onPageScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', onPageScroll)
  if (rafId !== null) cancelAnimationFrame(rafId)
})

watch(paperId, (currentPaperId, previousPaperId) => {
  if (previousPaperId && currentPaperId !== previousPaperId) {
    void loadPaperData()
    deepAnalysisText.value = null
    analysisItems.value = []
    activeOutlineIdx.value = 0
    void loadLabels(currentPaperId)
    void loadDeepAnalysis(currentPaperId)
  }
})

// ─── Labels ──────────────────────────────────────────────────
const paperLabels = ref<PaperLabels | null>(null)

const LABEL_DIMS = [
  { key: 'domain', label: 'Domain', color: '#6366f1' },
  { key: 'task', label: 'Task', color: '#0ea5e9' },
  { key: 'method', label: 'Method', color: '#10b981' },
  { key: 'data_object', label: 'Data / Object', color: '#f59e0b' },
  { key: 'application', label: 'Application', color: '#ec4899' },
] as const

const META_DIMS = [
  { key: 'paper_type', label: 'Paper Type', color: '#8b5cf6' },
  { key: 'evaluation_quality', label: 'Evaluation', color: '#64748b' },
  { key: 'resource_constraint', label: 'Resource', color: '#78716c' },
] as const

async function loadLabels(id: string) {
  try {
    const config = useRuntimeConfig()
    const apiBase = config.public.apiUrl as string
    const data = await $fetch<{ labels: PaperLabels }>(`${apiBase}/api/v1/papers/${id}/labels`)
    paperLabels.value = data.labels
  }
  catch {
    paperLabels.value = null
  }
}

// ─── Deep Analysis + Full-page outline ──────────────────────────────────────
const deepAnalysisText = ref<string | null>(null)
const analysisItems = ref<AnalysisItem[]>([])

// Page sections — must match the ids on the wrapper divs in the template
const PAGE_SECTIONS: OutlineItem[] = [
  { id: 'ks-sec-folio', title: 'Paper', level: 1 },
  { id: 'ks-sec-thesis', title: 'Thesis', level: 1 },
  { id: 'ks-sec-analysis', title: 'Deep Analysis', level: 1 },
  { id: 'ks-sec-claims', title: 'Claims', level: 1 },
  { id: 'ks-sec-methods', title: 'Methods & Results', level: 1 },
  { id: 'ks-sec-figures', title: 'Figures', level: 1 },
  { id: 'ks-sec-repro', title: 'Reproducibility', level: 1 },
  { id: 'ks-sec-related', title: 'Related Papers', level: 1 },
]

// Combined flat list: page sections interleaved with analysis sub-headings
const outlineItems = computed<OutlineItem[]>(() => {
  const items: OutlineItem[] = []
  for (const sec of PAGE_SECTIONS) {
    // Skip analysis section if not loaded
    if (sec.id === 'ks-sec-analysis' && !deepAnalysisText.value) continue
    items.push(sec)
    if (sec.id === 'ks-sec-analysis') {
      for (const h of analysisItems.value) {
        items.push({ id: h.id, title: h.title, level: h.level <= 2 ? 2 : 3 })
      }
    }
  }
  return items
})

// Scroll-based active tracking
const activeOutlineIdx = ref(0)
let rafId: number | null = null

function updateActiveFromScroll() {
  const threshold = window.scrollY + window.innerHeight * 0.28 + 72
  const items = outlineItems.value
  let newIdx = 0
  for (let i = items.length - 1; i >= 0; i--) {
    const el = document.getElementById(items[i].id)
    if (!el) continue
    const top = el.getBoundingClientRect().top + window.scrollY
    if (top <= threshold) {
      newIdx = i
      break
    }
  }
  activeOutlineIdx.value = newIdx
}

function onPageScroll() {
  if (rafId !== null) return
  rafId = requestAnimationFrame(() => {
    rafId = null
    updateActiveFromScroll()
  })
}

// Re-evaluate when outline items change (analysis items load asynchronously)
watch(outlineItems, () => { updateActiveFromScroll() })

function handleOutlineJump(id: string) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function loadDeepAnalysis(id: string) {
  try {
    const config = useRuntimeConfig()
    const apiBase = config.public.apiUrl as string
    const data = await $fetch<{ analysis: string }>(`${apiBase}/api/v1/papers/${id}/deep-analysis`)
    deepAnalysisText.value = data.analysis ?? null
  }
  catch {
    deepAnalysisText.value = null
  }
}

// ─── Handlers ────────────────────────────────────────────────
function handleRead() {
  navigateTo(`/reader/${paperId.value}`)
}

function handleSave() {
  // TODO: integrate with library store
  console.log('Paper saved:', paperId.value)
}

function handleCite() {
  // TODO: open citation modal
  console.log('Cite:', paperId.value)
}

function handleShowProvenance() {
  // TODO: open provenance drawer
  console.log('Show provenance for:', paperId.value)
}

function handleClaimClick(claim: PaperClaim) {
  // TODO: open claim detail drawer
  console.log('Claim clicked:', claim.id)
}

function handleFigureClick(fig: PaperFigure) {
  // TODO: open lightbox
  console.log('Figure clicked:', fig.number)
}

function handleAuthorClick(author: PaperAuthor) {
  navigateTo(`/researchers/${author.id}`)
}

function handleRelatedClick(paper: RelatedPaper) {
  navigateTo(`/papers/${paper.id}`)
}
</script>

<template>
  <div class="ks-paper-profile">
    <KsPageHeader :title="t('paperProfile')" :subtitle="`PAPER ${paperId}`" />

    <div class="ks-paper-profile__layout">
      <div class="ks-paper-profile__main">
        <!-- Hero -->
        <div id="ks-sec-folio">
          <PaperFolio
            :title="paperData?.title || 'Loading...'"
            :authors="authors"
            :venue="paperData?.venue || ''"
            :year="paperData?.published_at ? new Date(paperData.published_at).getFullYear() : 0"
            :doi="paperData?.doi || undefined"
            :open-access="true"
            :abstract="paperData?.abstract || ''"
            :cited-by="paperData?.citation_count || 0"
            :references="0"
            @read="handleRead"
            @save="handleSave"
            @cite="handleCite"
            @author-click="handleAuthorClick"
          />
        </div>

        <!-- Thesis -->
        <div id="ks-sec-thesis">
          <PaperThesisLine
            thesis="Claim-level granularity in scientific document processing enables significantly more accurate evidence retrieval and fact verification compared to traditional paragraph-level approaches."
            :confidence="0.92"
            model-source="Kaleidoscope Thesis-v3"
            @show-provenance="handleShowProvenance"
          />
        </div>

        <!-- Deep Analysis -->
        <div v-if="deepAnalysisText" id="ks-sec-analysis">
          <PaperDeepAnalysis
            :analysis="deepAnalysisText"
            @analysis-items-ready="analysisItems = $event"
          />
        </div>

        <!-- Claims -->
        <div id="ks-sec-claims">
          <PaperClaimsLedger :claims="claims" @claim-click="handleClaimClick" />
        </div>

        <!-- Methods & Results -->
        <div id="ks-sec-methods">
          <PaperMethodsResultsSlice
            :methods="methods"
            :results="results"
            :highlights="methodsResultHighlights"
          />
        </div>

        <!-- Figures -->
        <div id="ks-sec-figures">
          <PaperFigureGallery :figures="figures" @figure-click="handleFigureClick" />
        </div>

        <!-- Reproducibility -->
        <div id="ks-sec-repro">
          <PaperReproductionStatus
            overall-status="reproduced"
            :attempts="reproAttempts"
            :code-available="true"
            :data-available="true"
          />
        </div>

        <!-- Related -->
        <div id="ks-sec-related">
          <PaperRelatedConstellation :papers="relatedPapers" @paper-click="handleRelatedClick" />
        </div>
      </div>

      <!-- Sidebar -->
      <aside class="ks-paper-profile__sidebar">
        <PaperSupplementRail :items="supplements" />

        <!-- Taxonomy Labels -->
        <div v-if="paperLabels" class="ks-paper-labels">
          <h4 class="ks-paper-labels__title">Labels</h4>
          <div v-for="dim in LABEL_DIMS" :key="dim.key" class="ks-paper-labels__group">
            <span class="ks-paper-labels__dim" :style="{ color: dim.color }">{{ dim.label }}</span>
            <div class="ks-paper-labels__chips">
              <span
                v-for="tag in (paperLabels[dim.key] as string[])"
                :key="tag"
                class="ks-paper-labels__chip"
                :style="{ borderColor: dim.color, color: dim.color }"
              >{{ tag }}</span>
              <span v-if="!(paperLabels[dim.key] as string[]).length" class="ks-paper-labels__none">—</span>
            </div>
          </div>
          <div class="ks-paper-labels__divider" />
          <div v-for="dim in META_DIMS" :key="dim.key" class="ks-paper-labels__group">
            <span class="ks-paper-labels__dim" :style="{ color: dim.color }">{{ dim.label }}</span>
            <div class="ks-paper-labels__chips">
              <span
                v-for="tag in (paperLabels.meta[dim.key] as string[])"
                :key="tag"
                class="ks-paper-labels__chip"
                :style="{ borderColor: dim.color, color: dim.color }"
              >{{ tag }}</span>
              <span v-if="!(paperLabels.meta[dim.key] as string[]).length" class="ks-paper-labels__none">—</span>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- Grok-style full-page outline -->
    <PaperAnalysisOutline
      :items="outlineItems"
      :active-idx="activeOutlineIdx"
      @jump="handleOutlineJump"
    />
  </div>
</template>

<style scoped>
.ks-paper-profile {
  min-height: 100vh;
  padding-bottom: 80px;
}

.ks-paper-profile__layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 32px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.ks-paper-profile__main {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.ks-paper-profile__sidebar {
  position: sticky;
  top: 96px;
  height: fit-content;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.ks-paper-labels {
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-surface, rgba(30, 41, 59, 0.4));
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ks-paper-labels__title {
  font: 600 0.75rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-secondary);
  margin: 0 0 2px;
}

.ks-paper-labels__group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ks-paper-labels__dim {
  font: 600 0.65rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.07em;
}

.ks-paper-labels__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.ks-paper-labels__chip {
  display: inline-block;
  padding: 2px 7px;
  border: 1px solid;
  border-radius: 3px;
  font: 400 0.72rem / 1.5 var(--font-sans);
  background: transparent;
}

.ks-paper-labels__none {
  font: 400 0.72rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
}

.ks-paper-labels__divider {
  height: 1px;
  background: var(--color-border);
  margin: 2px 0;
}

@media (max-width: 960px) {
  .ks-paper-profile__layout {
    grid-template-columns: 1fr;
  }
  .ks-paper-profile__sidebar {
    position: static;
  }
}
</style>
