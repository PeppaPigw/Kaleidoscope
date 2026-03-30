<script setup lang="ts">
/**
 * Synthesis Studio — synthesis.vue
 */
import type { ComparisonPaper, ComparisonFeature } from '~/components/synthesis/ComparisonMatrix.vue'
import type { ThemeCluster } from '~/components/synthesis/ThemeClusters.vue'

definePageMeta({ layout: 'default' })

const CLUSTER_COLORS = ['var(--color-primary)', 'var(--color-accent-decorative)', '#6366f1', '#ec4899', '#f59e0b', '#10b981']

const { t } = useTranslation()
const { getTrendTopics } = useApi()

useHead({
  title: 'Synthesis Studio — Kaleidoscope',
  meta: [{ name: 'description', content: 'Cross-paper comparison and thematic synthesis.' }],
})

// Selected-paper comparison remains a stub until a user-driven comparison API exists.
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

const clusters = ref<ThemeCluster[]>([])
const isLoading = ref(true)
const loadError = ref(false)

onMounted(async () => {
  try {
    const topicData = await getTrendTopics()
    clusters.value = topicData.topics.map((topic, index) => ({
      id: topic.id,
      name: topic.label,
      paperCount: topic.paper_count,
      color: CLUSTER_COLORS[index % CLUSTER_COLORS.length] ?? CLUSTER_COLORS[0]!,
      keywords: topic.keywords.slice(0, 4),
    }))
  } catch {
    loadError.value = true
  } finally {
    isLoading.value = false
  }
})

function handleClusterClick(cluster: ThemeCluster) {
  navigateTo(`/search?cluster=${cluster.id}`)
}
</script>

<template>
  <div class="ks-synthesis">
    <KsPageHeader :title="t('synthesis')" :subtitle="t('synthesisSubtitle')" />

    <div class="ks-synthesis__content">
      <div v-if="isLoading" class="ks-synthesis__state">
        <KsSkeleton variant="paragraph" :lines="4" />
      </div>
      <KsEmptyState
        v-else-if="loadError || !clusters.length"
        title="Theme clusters unavailable"
        description="Topic cluster data could not be loaded from the trends API."
      />
      <SynthesisThemeClusters v-else :clusters="clusters" @cluster-click="handleClusterClick" />

      <p class="ks-type-body-sm ks-synthesis__note">
        Comparison matrix remains a selected-paper stub until user-driven comparison APIs are available.
      </p>
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
  gap: 24px;
}

.ks-synthesis__state {
  padding: 24px 0 8px;
}

.ks-synthesis__note {
  color: var(--color-secondary);
  margin-top: -8px;
}
</style>
