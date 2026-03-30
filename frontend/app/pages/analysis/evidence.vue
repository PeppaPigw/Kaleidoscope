<script setup lang="ts">
/**
 * Evidence & Methods Lab — analysis/evidence
 */
import type { MatrixResult } from '~/components/evidence/ResultsMatrix.vue'
import type { Contradiction } from '~/components/evidence/ContradictionsPanel.vue'

definePageMeta({ layout: 'default' })

const { t } = useTranslation()

useHead({
  title: 'Evidence Lab — Kaleidoscope',
  meta: [{ name: 'description', content: 'Analyze methods, results, and contradictions across papers.' }],
})

// ─── Live stats from analytics API ────────────────────────────────
const paperCount = ref(0)
const claimCount = ref(0)
const contradictions = ref<Contradiction[]>([
  {
    id: 'c1',
    claimA: { text: 'Atomic claim extraction improves RAG accuracy by 12%', paper: 'ClaimMiner', year: 2025 },
    claimB: { text: 'Finer granularity adds noise and decreases retrieval quality', paper: 'Long-Context Failures', year: 2025 },
    severity: 'high',
    resolved: false,
  },
  {
    id: 'c2',
    claimA: { text: 'SciBERT fine-tuning is sufficient for biomedical claim decomposition', paper: 'ClaimMiner', year: 2025 },
    claimB: { text: 'Larger models (7B+) are necessary for scientific text understanding', paper: 'ScaleLM Survey', year: 2024 },
    severity: 'medium',
    resolved: true,
  },
])

onMounted(async () => {
  const { getAnalyticsOverview, getClaimsStats, getContradictions } = useApi()
  try {
    const overview = await getAnalyticsOverview()
    paperCount.value = overview.total_papers ?? 0
  } catch {
    // Keep zero defaults
  }

  try {
    const stats = await getClaimsStats()
    claimCount.value = stats.total_claims ?? 0
  } catch {
    claimCount.value = 0
  }

  try {
    const contrasResp = await getContradictions(10)
    if (contrasResp.contradictions.length > 0) {
      contradictions.value = contrasResp.contradictions.map(c => ({
        id: c.id,
        claimA: { text: c.claimA.text, paper: c.claimA.paper || c.claimA.paper_id || 'Unknown', year: c.claimA.year || 0 },
        claimB: { text: c.claimB.text, paper: c.claimB.paper || c.claimB.paper_id || 'Unknown', year: c.claimB.year || 0 },
        severity: c.severity,
        resolved: c.resolved,
      }))
    }
  } catch {
    // Keep static stubs if endpoint fails
  }
})

// ─── Results matrix (static stubs — TODO: wire to GET /analysis/methods) ───
const metricNames = ['Evidence F1', 'Claim Precision', 'Throughput']

const results: MatrixResult[] = [
  { id: 'r1', method: 'ClaimMiner (Ours)', metrics: { 'Evidence F1': '89.2%', 'Claim Precision': '94.7%', 'Throughput': '12.3 papers/min' }, isBest: true, source: 'EMNLP 2025' },
  { id: 'r2', method: 'RAG-Paragraph', metrics: { 'Evidence F1': '77.1%', 'Claim Precision': '86.4%', 'Throughput': '18.7 papers/min' }, isBest: false, source: 'ACL 2024' },
  { id: 'r3', method: 'SciBERT-base', metrics: { 'Evidence F1': '71.3%', 'Claim Precision': '81.2%', 'Throughput': '22.1 papers/min' }, isBest: false, source: 'NAACL 2023' },
]

function handleEditRQ() {
  console.info('[Evidence Lab] Edit research question triggered')
}
</script>

<template>
  <div class="ks-evidence-lab">
    <KsPageHeader :title="t('evidenceLab')" :subtitle="t('evidenceLabSubtitle')" />

    <div class="ks-evidence-lab__content">
      <EvidenceRQHeader
        question="How does claim-level granularity affect retrieval-augmented generation accuracy?"
        description="Investigating the trade-off between decomposition granularity and downstream retrieval quality in biomedical NLP."
        :paper-count="paperCount"
        :claim-count="claimCount"
        @edit="handleEditRQ"
      />

      <EvidenceResultsMatrix
        :results="results"
        :metric-names="metricNames"
        title="Cross-Paper Results Comparison"
      />

      <EvidenceContradictionsPanel :contradictions="contradictions" />
    </div>
  </div>
</template>

<style scoped>
.ks-evidence-lab {
  min-height: 100vh;
  padding-bottom: 80px;
}

.ks-evidence-lab__content {
  max-width: 1040px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}
</style>
