<script setup lang="ts">
/**
 * Graph & Trends — insights/landscape
 */
import type { BurstTopic } from '~/components/graph/BurstMoments.vue'
import type { Opportunity } from '~/components/graph/OpportunityLens.vue'

definePageMeta({ layout: 'default' })

useHead({
  title: 'Insights Landscape — Kaleidoscope',
  meta: [{ name: 'description', content: 'Research trends, burst detection, and opportunity analysis.' }],
})

const burstTopics: BurstTopic[] = [
  { id: 'b1', topic: 'Atomic Claim Extraction', paperCount: 34, growth: 280, period: 'Q4 2024–Q1 2025', trending: true },
  { id: 'b2', topic: 'Retrieval-Augmented Generation', paperCount: 412, growth: 85, period: '2024', trending: true },
  { id: 'b3', topic: 'Scientific Fact Verification', paperCount: 67, growth: 45, period: '2024–2025', trending: false },
  { id: 'b4', topic: 'Long-Context LLM Failures', paperCount: 28, growth: 190, period: 'Q1 2025', trending: true },
  { id: 'b5', topic: 'Biomedical Knowledge Graphs', paperCount: 156, growth: 12, period: '2024', trending: false },
]

const opportunities: Opportunity[] = [
  { id: 'o1', title: 'Claim-Level RAG for Legal Documents', description: 'While claim extraction has been proven for biomedical text, legal domain remains largely unexplored despite similar structural properties.', gapType: 'unexplored', relevantPapers: 8, confidence: 0.87 },
  { id: 'o2', title: 'Multi-Lingual Claim Extraction', description: 'Current methods are English-only. Cross-lingual claim decomposition could unlock access to non-English scientific literature.', gapType: 'underdeveloped', relevantPapers: 3, confidence: 0.79 },
  { id: 'o3', title: 'Long-Context vs. Atomic Retrieval', description: 'Contradictory findings on whether finer granularity always helps — systematic comparison needed.', gapType: 'contradictory', relevantPapers: 12, confidence: 0.92 },
]

function handleTopicClick(topic: BurstTopic) {
  navigateTo(`/search?topic=${encodeURIComponent(topic.topic)}`)
}

function handleOpportunityClick(opportunity: Opportunity) {
  navigateTo(`/search?opportunity=${opportunity.id}`)
}
</script>

<template>
  <div class="ks-insights">
    <KsPageHeader title="Insights Landscape" subtitle="GRAPH & TRENDS" />

    <div class="ks-insights__content">
      <GraphBurstMoments :topics="burstTopics" @topic-click="handleTopicClick" />
      <GraphOpportunityLens :opportunities="opportunities" @opportunity-click="handleOpportunityClick" />
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
</style>
