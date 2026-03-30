<script setup lang="ts">
/**
 * Graph & Trends — insights/landscape
 */
import type { BurstTopic } from '~/components/graph/BurstMoments.vue'
import type { Opportunity } from '~/components/graph/OpportunityLens.vue'
import type { GraphStats } from '~/composables/useApi'

definePageMeta({ layout: 'default' })

const { t } = useTranslation()
const { getTrendingKeywords, getGraphStats } = useApi()

useHead({
  title: 'Insights Landscape — Kaleidoscope',
  meta: [{ name: 'description', content: 'Research trends, burst detection, and opportunity analysis.' }],
})

const burstTopics = ref<BurstTopic[]>([])
const graphStats = ref<GraphStats | null>(null)
const isLoading = ref(true)
const loadError = ref(false)

// Static until a dedicated opportunities endpoint exists.
const opportunities: Opportunity[] = [
  { id: 'o1', title: 'Claim-Level RAG for Legal Documents', description: 'While claim extraction has been proven for biomedical text, legal domain remains largely unexplored despite similar structural properties.', gapType: 'unexplored', relevantPapers: 8, confidence: 0.87 },
  { id: 'o2', title: 'Multi-Lingual Claim Extraction', description: 'Current methods are English-only. Cross-lingual claim decomposition could unlock access to non-English scientific literature.', gapType: 'underdeveloped', relevantPapers: 3, confidence: 0.79 },
  { id: 'o3', title: 'Long-Context vs. Atomic Retrieval', description: 'Contradictory findings on whether finer granularity always helps — systematic comparison needed.', gapType: 'contradictory', relevantPapers: 12, confidence: 0.92 },
]

onMounted(async () => {
  try {
    const keywordData = await getTrendingKeywords(10)
    burstTopics.value = keywordData.keywords.map(keyword => ({
      id: keyword.keyword,
      topic: keyword.keyword,
      paperCount: keyword.total_count,
      growth: Math.round(keyword.growth_rate * 100),
      period: '2024–2025',
      trending: keyword.trend === 'rising',
    }))
  } catch {
    loadError.value = true
  } finally {
    isLoading.value = false
  }

  try {
    graphStats.value = await getGraphStats()
  } catch {
    graphStats.value = null
  }
})

function handleTopicClick(topic: BurstTopic) {
  navigateTo(`/search?topic=${encodeURIComponent(topic.topic)}`)
}

function handleOpportunityClick(opportunity: Opportunity) {
  navigateTo(`/search?opportunity=${opportunity.id}`)
}
</script>

<template>
  <div class="ks-insights">
    <KsPageHeader :title="t('insights')" :subtitle="t('insightsSubtitle')" />

    <div class="ks-insights__content">
      <div v-if="isLoading" class="ks-insights__state">
        <KsSkeleton variant="paragraph" :lines="4" />
      </div>
      <KsEmptyState
        v-else-if="loadError || !burstTopics.length"
        title="Trend data is unavailable"
        description="Hot keywords could not be loaded from the trends API right now."
      />
      <GraphBurstMoments v-else :topics="burstTopics" @topic-click="handleTopicClick" />

      <GraphOpportunityLens :opportunities="opportunities" @opportunity-click="handleOpportunityClick" />

      <section v-if="graphStats" class="ks-card ks-insights__stats">
        <span class="ks-type-eyebrow">Graph Stats</span>
        <div class="ks-insights__stats-grid">
          <span class="ks-type-data">Papers {{ graphStats.paper_count }}</span>
          <span class="ks-type-data">Citations {{ graphStats.citation_count }}</span>
          <span class="ks-type-data">Authors {{ graphStats.author_count }}</span>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.ks-insights {
  min-height: 100vh;
  padding-bottom: 80px;
}

.ks-insights__content {
  max-width: 1040px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.ks-insights__state {
  padding: 24px 0;
}

.ks-insights__stats {
  padding: 24px;
  display: grid;
  gap: 12px;
}

.ks-insights__stats-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
</style>
