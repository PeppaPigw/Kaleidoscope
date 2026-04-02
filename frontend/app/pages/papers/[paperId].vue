<script setup lang="ts">
/**
 * Paper Profile Page — [paperId]
 *
 * Composes PaperFolio, ThesisLine, ClaimsLedger, MethodsResultsSlice,
 * FigureGallery, SupplementRail, ReproductionStatus, RelatedConstellation.
 */
import type { PaperContent, PaperHighlights } from '~/composables/useApi'
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
})

watch(paperId, (currentPaperId, previousPaperId) => {
  if (previousPaperId && currentPaperId !== previousPaperId) {
    void loadPaperData()
  }
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

        <!-- Thesis -->
        <PaperThesisLine
          thesis="Claim-level granularity in scientific document processing enables significantly more accurate evidence retrieval and fact verification compared to traditional paragraph-level approaches."
          :confidence="0.92"
          model-source="Kaleidoscope Thesis-v3"
          @show-provenance="handleShowProvenance"
        />

        <!-- Claims -->
        <PaperClaimsLedger :claims="claims" @claim-click="handleClaimClick" />

        <!-- Methods & Results -->
        <PaperMethodsResultsSlice
          :methods="methods"
          :results="results"
          :highlights="methodsResultHighlights"
        />

        <!-- Figures -->
        <PaperFigureGallery :figures="figures" @figure-click="handleFigureClick" />

        <!-- Reproducibility -->
        <PaperReproductionStatus
          overall-status="reproduced"
          :attempts="reproAttempts"
          :code-available="true"
          :data-available="true"
        />

        <!-- Related -->
        <PaperRelatedConstellation :papers="relatedPapers" @paper-click="handleRelatedClick" />
      </div>

      <!-- Sidebar -->
      <div class="ks-paper-profile__sidebar">
        <PaperSupplementRail :items="supplements" />
      </div>
    </div>
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
