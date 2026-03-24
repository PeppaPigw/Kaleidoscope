<script setup lang="ts">
/**
 * Paper Profile Page — [paperId]
 *
 * Composes PaperFolio, ThesisLine, ClaimsLedger, MethodsResultsSlice,
 * FigureGallery, SupplementRail, ReproductionStatus, RelatedConstellation.
 */
import type { PaperAuthor } from '~/components/paper/PaperFolio.vue'
import type { PaperClaim } from '~/components/paper/ClaimsLedger.vue'
import type { MethodItem, ResultItem } from '~/components/paper/MethodsResultsSlice.vue'
import type { PaperFigure } from '~/components/paper/FigureGallery.vue'
import type { SupplementItem } from '~/components/paper/SupplementRail.vue'
import type { ReproductionAttempt } from '~/components/paper/ReproductionStatus.vue'
import type { RelatedPaper } from '~/components/paper/RelatedConstellation.vue'

definePageMeta({ layout: 'default' })

const { t } = useTranslation()

const route = useRoute()
const paperId = computed(() => route.params.paperId as string)

useHead({
  title: 'Paper Profile — Kaleidoscope',
  meta: [
    { name: 'description', content: 'Detailed paper analysis with claims, methods, results, and reproducibility.' },
  ],
})

// ─── Fetch paper data from API ───────────────────────────────
const apiUrl = useRuntimeConfig().public.apiUrl
const { data: paperData } = useFetch<{
  id: string
  title: string
  abstract?: string | null
  doi?: string | null
  published_at?: string | null
  citation_count?: number
  venue?: string
  has_full_text?: boolean
}>(() => `${apiUrl}/api/v1/papers/${paperId.value}`)

// ─── Mock data ───────────────────────────────────────────────
const authors: PaperAuthor[] = [
  { id: 'a1', name: 'Jiawei Liu', affiliation: 'Tsinghua University' },
  { id: 'a2', name: 'Xiaoming Wang', affiliation: 'Stanford University' },
  { id: 'a3', name: 'Hui Chen', affiliation: 'Google DeepMind' },
  { id: 'a4', name: 'Yafeng Zhang', affiliation: 'Tsinghua University' },
]

const claims: PaperClaim[] = [
  { id: 'c1', text: 'Atomic claim extraction improves downstream RAG accuracy by 12% over paragraph-level retrieval.', category: 'Main Result', confidence: 0.94, evidenceCount: 3, status: 'verified' },
  { id: 'c2', text: 'Our pipeline decomposes biomedical papers into an average of 47 atomic claims per paper.', category: 'Quantitative', confidence: 0.91, evidenceCount: 2, status: 'verified' },
  { id: 'c3', text: 'Evidence alignment reaches 89% F1 on the BioASQ benchmark.', category: 'Benchmark', confidence: 0.88, evidenceCount: 4, status: 'verified' },
  { id: 'c4', text: 'The approach generalizes to legal and financial documents without retraining.', category: 'Generalizability', confidence: 0.62, evidenceCount: 1, status: 'unverified' },
  { id: 'c5', text: 'Claim-level granularity reduces hallucination in fact-checking by 23%.', category: 'Main Result', confidence: 0.85, evidenceCount: 2, status: 'disputed' },
]

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

const figures: PaperFigure[] = [
  { id: 'f1', number: 1, caption: 'Pipeline architecture: document → sentences → atomic claims → evidence alignment', imageUrl: '' },
  { id: 'f2', number: 2, caption: 'Claim decomposition F1 across different document lengths', imageUrl: '' },
  { id: 'f3', number: 3, caption: 'Evidence alignment quality vs. retrieval granularity', imageUrl: '' },
  { id: 'f4', number: 4, caption: 'Cross-domain transfer results (law, finance, biomedical)', imageUrl: '' },
]

const supplements: SupplementItem[] = [
  { id: 's1', label: 'GitHub Repository', type: 'code', url: 'https://github.com/example/claimminer' },
  { id: 's2', label: 'BioASQ-Claims Dataset', type: 'dataset', url: 'https://example.com/bioasq-claims' },
  { id: 's3', label: 'EMNLP 2025 Slides', type: 'slides', url: 'https://example.com/slides' },
  { id: 's4', label: 'Demo Application', type: 'demo', url: 'https://example.com/demo' },
]

const reproAttempts: ReproductionAttempt[] = [
  { id: 'ra1', team: 'Allen AI (Semantic Scholar)', date: '2025-08', success: 'full', notes: 'Successfully reproduced main results within 1% margin on BioASQ benchmark.' },
  { id: 'ra2', team: 'UIUC NLP Lab', date: '2025-09', success: 'partial', notes: 'Reproduced claim extraction, but evidence alignment was 3% lower than reported.' },
]

const relatedPapers: RelatedPaper[] = [
  { id: 'rp1', title: 'RAGBench-Sci: Failure Modes of Citation-Grounded Retrieval', venue: 'ACL 2025', year: 2025, relationship: 'cited-by', similarity: 0.89 },
  { id: 'rp2', title: 'Atomic Facts: Decomposing Knowledge for NLI', venue: 'NAACL 2024', year: 2024, relationship: 'cites', similarity: 0.92 },
  { id: 'rp3', title: 'SciBERT: A Pretrained Language Model for Scientific Text', venue: 'EMNLP 2019', year: 2019, relationship: 'cites', similarity: 0.85 },
  { id: 'rp4', title: 'ContractNLI: Claim Verification for Legal Documents', venue: 'ACL 2023', year: 2023, relationship: 'similar', similarity: 0.76 },
  { id: 'rp5', title: 'When More Context Hurts: Long-Context Failure Analysis', venue: 'EMNLP 2025', year: 2025, relationship: 'contradicts', similarity: 0.71 },
]

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
          :year="paperData?.published_at ? new Date(paperData.published_at).getFullYear() : undefined"
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
        <PaperMethodsResultsSlice :methods="methods" :results="results" />

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
