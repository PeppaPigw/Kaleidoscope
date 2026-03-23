<script setup lang="ts">
/**
 * OpportunityLens — Research opportunity identification.
 */

export interface Opportunity {
  id: string
  title: string
  description: string
  gapType: 'unexplored' | 'underdeveloped' | 'contradictory'
  relevantPapers: number
  confidence: number
}

export interface OpportunityLensProps {
  opportunities: Opportunity[]
}

defineProps<OpportunityLensProps>()
defineEmits<{ 'opportunity-click': [opportunity: Opportunity] }>()

const uid = useId()

type TagVariant = 'primary' | 'accent' | 'danger'

function gapVariant(g: Opportunity['gapType']): TagVariant {
  const map: Record<Opportunity['gapType'], TagVariant> = { unexplored: 'primary', underdeveloped: 'accent', contradictory: 'danger' }
  return map[g]
}
</script>

<template>
  <section class="ks-opportunity-lens ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <h2 :id="`${uid}-title`" class="ks-type-section-title">Research Opportunities</h2>

    <div class="ks-opportunity-lens__grid">
      <button
        v-for="o in opportunities"
        :key="o.id"
        type="button"
        class="ks-card ks-opportunity-lens__card"
        @click="$emit('opportunity-click', o)"
      >
        <div class="ks-opportunity-lens__header">
          <KsTag :variant="gapVariant(o.gapType)">{{ o.gapType }}</KsTag>
          <span class="ks-type-data" style="color: var(--color-primary); font-weight: 700;">{{ (o.confidence * 100).toFixed(0) }}%</span>
        </div>
        <h3 class="ks-opportunity-lens__title">{{ o.title }}</h3>
        <p class="ks-opportunity-lens__desc">{{ o.description }}</p>
        <span class="ks-type-data">{{ o.relevantPapers }} related papers</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.ks-opportunity-lens__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 10px;
  margin-top: 16px;
}

.ks-opportunity-lens__card {
  padding: 16px;
  text-align: left;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: transform var(--duration-normal) var(--ease-spring),
              box-shadow var(--duration-normal) var(--ease-smooth);
}

.ks-opportunity-lens__card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(26, 26, 26, 0.06);
}

.ks-opportunity-lens__card:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-opportunity-lens__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ks-opportunity-lens__title {
  font: 600 1rem / 1.3 var(--font-serif);
  color: var(--color-text);
}

.ks-opportunity-lens__desc {
  font: 400 0.8125rem / 1.5 var(--font-serif);
  color: var(--color-secondary);
}
</style>
