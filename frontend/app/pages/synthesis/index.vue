<script setup lang="ts">
/**
 * Synthesis Studio — synthesis.vue
 */
import type { ComparisonPaper, ComparisonFeature } from '~/components/synthesis/ComparisonMatrix.vue'
import type { ThemeCluster } from '~/components/synthesis/ThemeClusters.vue'

definePageMeta({ layout: 'default' })

const { t } = useTranslation()

useHead({
  title: 'Synthesis Studio — Kaleidoscope',
  meta: [{ name: 'description', content: 'Cross-paper comparison and thematic synthesis.' }],
})

const papers: ComparisonPaper[] = [
  { id: 'p1', title: 'ClaimMiner', shortName: 'ClaimMiner' },
  { id: 'p2', title: 'FactNet', shortName: 'FactNet' },
  { id: 'p3', title: 'RAG-Paragraph', shortName: 'RAG-P' },
]

const features: ComparisonFeature[] = [
  { id: 'f1', name: 'Atomic Claim Extraction', category: 'Method', values: { p1: true, p2: false, p3: false } },
  { id: 'f2', name: 'Evidence Alignment', category: 'Method', values: { p1: true, p2: true, p3: false } },
  { id: 'f3', name: 'Cross-Domain Transfer', category: 'Capability', values: { p1: 'partial', p2: 'no', p3: 'yes' } },
  { id: 'f4', name: 'Open Source', category: 'Access', values: { p1: true, p2: true, p3: false } },
  { id: 'f5', name: 'BioASQ Evaluation', category: 'Benchmark', values: { p1: true, p2: false, p3: true } },
]

const clusters: ThemeCluster[] = [
  { id: 'cl1', name: 'Claim Decomposition', paperCount: 8, color: 'var(--color-primary)', keywords: ['atomic claims', 'NLI', 'decomposition', 'verification'] },
  { id: 'cl2', name: 'Evidence Retrieval', paperCount: 12, color: 'var(--color-accent-decorative)', keywords: ['RAG', 'retrieval', 'alignment', 'grounding'] },
  { id: 'cl3', name: 'Biomedical NLP', paperCount: 6, color: '#6366f1', keywords: ['SciBERT', 'BioASQ', 'PubMed', 'clinical'] },
  { id: 'cl4', name: 'Fact Checking', paperCount: 5, color: '#ec4899', keywords: ['verification', 'hallucination', 'faithfulness'] },
]

function handleClusterClick(cluster: ThemeCluster) {
  navigateTo(`/search?cluster=${cluster.id}`)
}
</script>

<template>
  <div class="ks-synthesis">
    <KsPageHeader :title="t('synthesis')" :subtitle="t('synthesisSubtitle')" />

    <div class="ks-synthesis__content">
      <SynthesisThemeClusters :clusters="clusters" @cluster-click="handleClusterClick" />
      <SynthesisComparisonMatrix :papers="papers" :features="features" />
    </div>
  </div>
</template>

<style scoped>
.ks-synthesis {
  min-height: 100vh;
  padding-bottom: 80px;
}

.ks-synthesis__content {
  max-width: 1040px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}
</style>
