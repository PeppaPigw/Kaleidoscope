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

const { t, isZh } = useTranslation()

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
    void loadDeepAnalysis(paperId.value).then(() => {
      if (isZh.value && paperId.value)
        void loadDeepAnalysisZh(paperId.value)
    })
    void loadOverviewImage(paperId.value)
    void loadPaperLinks(paperId.value)
  }
  window.addEventListener('scroll', onPageScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', onPageScroll)
  if (rafId !== null) cancelAnimationFrame(rafId)
  stopPollingOverviewImage()
})

watch(paperId, (currentPaperId, previousPaperId) => {
  if (previousPaperId && currentPaperId !== previousPaperId) {
    void loadPaperData()
    deepAnalysisText.value = null
    deepAnalysisZhText.value = null
    deepAnalysisZhStatus.value = 'idle'
    analysisItems.value = []
    activeOutlineIdx.value = 0
    overviewImage.value = null
    paperLinks.value = null
    stopPollingOverviewImage()
    void loadLabels(currentPaperId)
    void loadDeepAnalysis(currentPaperId).then(() => {
      if (isZh.value)
        void loadDeepAnalysisZh(currentPaperId)
    })
    void loadOverviewImage(currentPaperId)
    void loadPaperLinks(currentPaperId)
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

// ─── 一图速览 Overview Image ───────────────────────────────────────────────
type OverviewImageRecord = {
  status: 'ok' | 'generating' | 'error'
  url?: string
  error?: string
  generated_at?: string
}

const overviewImage = ref<OverviewImageRecord | null>(null)
const overviewImageLoading = ref(false)
let overviewImagePollTimer: ReturnType<typeof setInterval> | null = null

async function loadOverviewImage(id: string) {
  try {
    const config = useRuntimeConfig()
    const apiBase = config.public.apiUrl as string
    const data = await $fetch<OverviewImageRecord>(`${apiBase}/api/v1/papers/${id}/overview-image`)
    overviewImage.value = data
  }
  catch {
    overviewImage.value = null
  }
}

function startPollingOverviewImage(id: string) {
  if (overviewImagePollTimer) return
  overviewImagePollTimer = setInterval(async () => {
    await loadOverviewImage(id)
    if (overviewImage.value?.status !== 'generating') {
      stopPollingOverviewImage()
    }
  }, 3000)
}

function stopPollingOverviewImage() {
  if (overviewImagePollTimer) {
    clearInterval(overviewImagePollTimer)
    overviewImagePollTimer = null
  }
}

async function triggerOverviewImage() {
  if (!paperId.value || overviewImageLoading.value) return
  overviewImageLoading.value = true
  try {
    const config = useRuntimeConfig()
    const apiBase = config.public.apiUrl as string
    const result = await $fetch<{ status: string }>(`${apiBase}/api/v1/papers/${paperId.value}/overview-image`, {
      method: 'POST',
    })
    overviewImage.value = { status: result.status as 'generating' }
    if (result.status === 'generating') {
      startPollingOverviewImage(paperId.value)
    }
  }
  catch {
    // ignore — button stays visible
  }
  finally {
    overviewImageLoading.value = false
  }
}

// ─── Deep Analysis + Full-page outline ──────────────────────────────────────
const deepAnalysisText = ref<string | null>(null)
const deepAnalysisZhText = ref<string | null>(null)
const deepAnalysisZhStatus = ref<'idle' | 'loading' | 'translating' | 'ok' | 'error'>('idle')
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

async function loadDeepAnalysisZh(id: string) {
  if (deepAnalysisZhStatus.value === 'loading') return
  deepAnalysisZhStatus.value = 'loading'
  try {
    const config = useRuntimeConfig()
    const apiBase = config.public.apiUrl as string
    const data = await $fetch<{ analysis: string }>(`${apiBase}/api/v1/papers/${id}/deep-analysis-zh`)
    deepAnalysisZhText.value = data.analysis ?? null
    deepAnalysisZhStatus.value = 'ok'
  }
  catch (e: any) {
    const detail = e?.data?.detail ?? ''
    deepAnalysisZhStatus.value = detail === 'translating' ? 'translating' : 'error'
    deepAnalysisZhText.value = null
  }
}

const deepAnalysisDisplay = computed(() =>
  isZh.value && deepAnalysisZhText.value ? deepAnalysisZhText.value : deepAnalysisText.value,
)

// Load Chinese translation when locale is zh
watch(isZh, (zh) => {
  if (zh && paperId.value && deepAnalysisText.value && deepAnalysisZhStatus.value === 'idle')
    void loadDeepAnalysisZh(paperId.value)
}, { immediate: false })

// ─── Paper Links (AI-fetched) ─────────────────────────────────────────────────
type PaperLinksRelated = {
  blog_url?: string | null
  discussion_url?: string | null
  social_url?: string | null
}

type PaperLinksData = {
  paper_id: string
  venue?: string | null
  code_url?: string | null
  dataset_urls?: string[] | null
  model_weights_url?: string | null
  project_page_url?: string | null
  related_links?: PaperLinksRelated | null
  fetched_at?: string | null
}

const paperLinks = ref<PaperLinksData | null>(null)

async function loadPaperLinks(id: string) {
  try {
    const config = useRuntimeConfig()
    const apiBase = config.public.apiUrl as string
    paperLinks.value = await $fetch<PaperLinksData>(`${apiBase}/api/v1/papers/${id}/links`)
  }
  catch {
    paperLinks.value = null
  }
}

const hasPaperLinks = computed(() => {
  const pl = paperLinks.value
  if (!pl) return false
  const rel = pl.related_links
  return !!(
    pl.code_url
    || pl.project_page_url
    || pl.model_weights_url
    || (pl.dataset_urls?.length)
    || rel?.blog_url
    || rel?.discussion_url
    || rel?.social_url
  )
})

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

        <!-- 一图速览 Overview Image -->
        <div class="ks-overview-image">
          <!-- Image loaded -->
          <template v-if="overviewImage?.status === 'ok' && overviewImage.url">
            <div class="ks-overview-image__header">
              <span class="ks-overview-image__badge">一图速览</span>
            </div>
            <img
              :src="overviewImage.url"
              alt="Paper overview poster"
              class="ks-overview-image__img"
              loading="lazy"
            >
          </template>

          <!-- Generating in progress -->
          <template v-else-if="overviewImage?.status === 'generating'">
            <div class="ks-overview-image__generating">
              <span class="ks-overview-image__spinner" />
              <span>正在生成一图速览，请稍候…</span>
            </div>
          </template>

          <!-- Error state -->
          <template v-else-if="overviewImage?.status === 'error'">
            <div class="ks-overview-image__error">
              <span>生成失败</span>
              <button class="ks-overview-image__btn" @click="triggerOverviewImage">重试</button>
            </div>
          </template>

          <!-- Not generated yet — show generate button if deep analysis exists -->
          <template v-else-if="deepAnalysisText">
            <div class="ks-overview-image__empty">
              <button
                class="ks-overview-image__btn"
                :disabled="overviewImageLoading"
                @click="triggerOverviewImage"
              >
                {{ overviewImageLoading ? '提交中…' : '✦ 生成一图速览' }}
              </button>
              <span class="ks-overview-image__hint">根据 Deep Analysis 自动生成论文海报</span>
            </div>
          </template>
        </div>

        <!-- Deep Analysis -->
        <div v-if="deepAnalysisText" id="ks-sec-analysis">
          <div v-if="isZh && deepAnalysisZhStatus === 'translating'" class="ks-zh-translating">
            <span class="ks-overview-image__spinner" />
            <span>正在翻译中文版，请稍候…</span>
          </div>
          <PaperDeepAnalysis
            :analysis="deepAnalysisDisplay!"
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
        <!-- AI-fetched Paper Links -->
        <div v-if="hasPaperLinks" class="ks-paper-links-panel">
          <h3 class="ks-type-eyebrow" style="color: var(--color-accent); margin-bottom: 12px;">
            {{ isZh ? '相关链接' : 'Links' }}
          </h3>
          <ul class="ks-paper-links-panel__list">
            <li v-if="paperLinks.code_url">
              <a :href="paperLinks.code_url" target="_blank" rel="noopener" class="ks-paper-links-panel__link">
                <span class="ks-paper-links-panel__icon" aria-hidden="true">
                  <!-- GitHub -->
                  <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.335-1.755-1.335-1.755-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.605-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 21.795 24 17.295 24 12c0-6.63-5.37-12-12-12z"/></svg>
                </span>
                <span class="ks-paper-links-panel__label">{{ isZh ? '代码' : 'Code' }}</span>
                <KsTag variant="neutral" style="font-size: 0.625rem;">code</KsTag>
              </a>
            </li>
            <li v-if="paperLinks.project_page_url">
              <a :href="paperLinks.project_page_url" target="_blank" rel="noopener" class="ks-paper-links-panel__link">
                <span class="ks-paper-links-panel__icon" aria-hidden="true">
                  <!-- arXiv -->
                  <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M10.427 5.376c-.668-.31-1.379-.26-1.851.164L3.302 9.652a1.79 1.79 0 0 0-.087 2.565l5.894 6.269 1.403-1.484-5.16-5.48 4.683-3.813.045-.037c.019-.015.034-.023.04-.016.006.007 0 .024-.006.04l-.027.063L7.08 12.21l1.658.8 3.214-6.671c.276-.573.141-1.252-.303-1.764zm8.845 10.907-5.897-6.269-1.4 1.484 5.156 5.48-4.679 3.81-.045.037c-.018.015-.033.023-.04.016-.005-.007.001-.024.007-.04l.026-.063 3.011-4.447-1.658-.801-3.214 6.671c-.275.573-.141 1.252.303 1.764.667.31 1.378.26 1.85-.164l5.274-4.112a1.79 1.79 0 0 0 .087-2.566z"/></svg>
                </span>
                <span class="ks-paper-links-panel__label">{{ isZh ? '项目主页' : 'Project Page' }}</span>
                <KsTag variant="neutral" style="font-size: 0.625rem;">paper</KsTag>
              </a>
            </li>
            <li v-if="paperLinks.model_weights_url">
              <a :href="paperLinks.model_weights_url" target="_blank" rel="noopener" class="ks-paper-links-panel__link">
                <span class="ks-paper-links-panel__icon" aria-hidden="true">
                  <!-- Hugging Face -->
                  <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 2c5.523 0 10 4.477 10 10s-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2zm-3.5 7.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm7 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm-7.07 5.43a.5.5 0 0 0-.43.75C8.88 17.27 10.35 18 12 18s3.12-.73 4-1.82a.5.5 0 0 0-.43-.75.5.5 0 0 0-.4.2C14.5 16.46 13.33 17 12 17s-2.5-.54-3.17-1.37a.5.5 0 0 0-.4-.2z"/></svg>
                </span>
                <span class="ks-paper-links-panel__label">{{ isZh ? '模型权重' : 'Weights' }}</span>
                <KsTag variant="neutral" style="font-size: 0.625rem;">weights</KsTag>
              </a>
            </li>
            <template v-if="paperLinks.dataset_urls?.length">
              <li v-for="(url, i) in paperLinks.dataset_urls" :key="`ds-${i}`">
                <a :href="url" target="_blank" rel="noopener" class="ks-paper-links-panel__link">
                  <span class="ks-paper-links-panel__icon" aria-hidden="true">
                    <!-- Hugging Face -->
                    <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 2c5.523 0 10 4.477 10 10s-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2zm-3.5 7.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm7 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm-7.07 5.43a.5.5 0 0 0-.43.75C8.88 17.27 10.35 18 12 18s3.12-.73 4-1.82a.5.5 0 0 0-.43-.75.5.5 0 0 0-.4.2C14.5 16.46 13.33 17 12 17s-2.5-.54-3.17-1.37a.5.5 0 0 0-.4-.2z"/></svg>
                  </span>
                  <span class="ks-paper-links-panel__label">{{ isZh ? `数据集${paperLinks.dataset_urls!.length > 1 ? ` ${i + 1}` : ''}` : `Dataset${paperLinks.dataset_urls!.length > 1 ? ` ${i + 1}` : ''}` }}</span>
                  <KsTag variant="neutral" style="font-size: 0.625rem;">dataset</KsTag>
                </a>
              </li>
            </template>
            <li v-if="paperLinks.related_links?.blog_url">
              <a :href="paperLinks.related_links.blog_url" target="_blank" rel="noopener" class="ks-paper-links-panel__link">
                <span class="ks-paper-links-panel__icon" aria-hidden="true">
                  <!-- Medium -->
                  <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M13.54 12a6.8 6.8 0 0 1-6.77 6.82A6.8 6.8 0 0 1 0 12a6.8 6.8 0 0 1 6.77-6.82A6.8 6.8 0 0 1 13.54 12zm7.42 0c0 3.54-1.51 6.42-3.38 6.42-1.87 0-3.39-2.88-3.39-6.42s1.52-6.42 3.39-6.42 3.38 2.88 3.38 6.42M24 12c0 3.17-.53 5.75-1.19 5.75-.66 0-1.19-2.58-1.19-5.75s.53-5.75 1.19-5.75C23.47 6.25 24 8.83 24 12z"/></svg>
                </span>
                <span class="ks-paper-links-panel__label">{{ isZh ? '博客' : 'Blog' }}</span>
                <KsTag variant="neutral" style="font-size: 0.625rem;">blog</KsTag>
              </a>
            </li>
            <li v-if="paperLinks.related_links?.discussion_url">
              <a :href="paperLinks.related_links.discussion_url" target="_blank" rel="noopener" class="ks-paper-links-panel__link">
                <span class="ks-paper-links-panel__icon" aria-hidden="true">
                  <!-- Reddit -->
                  <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/></svg>
                </span>
                <span class="ks-paper-links-panel__label">{{ isZh ? '社区' : 'Community' }}</span>
                <KsTag variant="neutral" style="font-size: 0.625rem;">reddit</KsTag>
              </a>
            </li>
            <li v-if="paperLinks.related_links?.social_url">
              <a :href="paperLinks.related_links.social_url" target="_blank" rel="noopener" class="ks-paper-links-panel__link">
                <span class="ks-paper-links-panel__icon" aria-hidden="true">
                  <!-- X (Twitter) -->
                  <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                </span>
                <span class="ks-paper-links-panel__label">{{ isZh ? '社交媒体' : 'Social' }}</span>
                <KsTag variant="neutral" style="font-size: 0.625rem;">X</KsTag>
              </a>
            </li>
          </ul>
        </div>


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

.ks-paper-links-panel {
  padding: 20px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
}

.ks-paper-links-panel__list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ks-paper-links-panel__link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  text-decoration: none;
  border-radius: 2px;
  transition: background-color var(--duration-fast) var(--ease-smooth);
}

.ks-paper-links-panel__link:hover {
  background: rgba(13, 115, 119, 0.04);
}

.ks-paper-links-panel__link:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}

.ks-paper-links-panel__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: var(--color-text);
  opacity: 0.7;
}

.ks-paper-links-panel__label {
  flex: 1;
  font: 500 0.875rem / 1.3 var(--font-sans);
  color: var(--color-text);
}

.ks-zh-translating {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0 12px;
  font: 400 0.8rem / 1 var(--font-sans);
  color: var(--color-secondary);
  opacity: 0.75;
}

@media (max-width: 960px) {
  .ks-paper-profile__layout {
    grid-template-columns: 1fr;
  }
  .ks-paper-profile__sidebar {
    position: static;
  }
}

/* ── 一图速览 Overview Image ─────────────────────────── */
.ks-overview-image {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  overflow: hidden;
  background: var(--color-surface, rgba(15, 23, 42, 0.6));
}

.ks-overview-image__header {
  padding: 12px 18px 0;
}

.ks-overview-image__badge {
  font: 600 0.7rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-secondary);
  border: 1px solid var(--color-border);
  border-radius: 3px;
  padding: 3px 8px;
}

.ks-overview-image__img {
  display: block;
  width: 100%;
  height: auto;
  margin-top: 12px;
  border-radius: 0 0 var(--radius-card) var(--radius-card);
}

.ks-overview-image__generating,
.ks-overview-image__error,
.ks-overview-image__empty {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  font: 400 0.875rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-overview-image__spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: ks-spin 0.9s linear infinite;
  flex-shrink: 0;
}

@keyframes ks-spin { to { transform: rotate(360deg); } }

.ks-overview-image__btn {
  padding: 6px 16px;
  border: 1px solid var(--color-primary);
  border-radius: 5px;
  background: none;
  color: var(--color-primary);
  font: 500 0.8125rem / 1 var(--font-sans);
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s, color 0.15s;
}

.ks-overview-image__btn:hover:not(:disabled) {
  background: var(--color-primary);
  color: #fff;
}

.ks-overview-image__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ks-overview-image__hint {
  font: 400 0.78rem / 1 var(--font-sans);
  color: var(--color-secondary);
  opacity: 0.7;
}
</style>
