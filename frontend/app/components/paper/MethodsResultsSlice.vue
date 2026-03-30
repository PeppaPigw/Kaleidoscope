<script setup lang="ts">
/**
 * MethodsResultsSlice — Methods & Results summary cards.
 *
 * Two-column layout showing method approach and key results
 * extracted from the paper with evidence linkage.
 */

export interface MethodItem {
  id: string
  name: string
  description: string
  type: 'dataset' | 'model' | 'metric' | 'baseline' | 'technique'
}

export interface ResultItem {
  id: string
  metric: string
  value: string
  comparison?: string
  delta?: string
  positive: boolean
}

export interface MethodsResultsSliceProps {
  methods: MethodItem[]
  results: ResultItem[]
  highlights?: string[]
}

const props = withDefaults(defineProps<MethodsResultsSliceProps>(), {
  highlights: () => [],
})
const uid = useId()

type TagVariant = 'primary' | 'accent' | 'neutral'

function typeColor(t: MethodItem['type']): TagVariant {
  const map: Record<MethodItem['type'], TagVariant> = {
    dataset: 'primary',
    model: 'accent',
    metric: 'neutral',
    baseline: 'neutral',
    technique: 'primary',
  }
  return map[t]
}
</script>

<template>
  <section class="ks-methods-results ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <h2 :id="`${uid}-title`" class="ks-type-section-title">Methods & Results</h2>

    <div v-if="props.highlights.length" class="ks-methods-results__highlights">
      <h3 class="ks-type-eyebrow" style="color: var(--color-secondary); margin-bottom: 12px;">AI Highlights</h3>
      <div class="ks-methods-results__items">
        <div
          v-for="(highlight, index) in props.highlights"
          :key="`highlight-${index}`"
          class="ks-card ks-methods-results__highlight"
        >
          <p class="ks-type-body-sm">{{ highlight }}</p>
        </div>
      </div>
    </div>

    <div class="ks-methods-results__grid">
      <!-- Methods column -->
      <div class="ks-methods-results__col">
        <h3 class="ks-type-eyebrow" style="color: var(--color-accent); margin-bottom: 12px;">Methods</h3>
        <div class="ks-methods-results__items">
          <div v-for="m in methods" :key="m.id" class="ks-card ks-methods-results__item">
            <div class="ks-methods-results__item-header">
              <span class="ks-methods-results__item-name">{{ m.name }}</span>
              <KsTag :variant="typeColor(m.type)">{{ m.type }}</KsTag>
            </div>
            <p class="ks-type-body-sm" style="color: var(--color-secondary);">{{ m.description }}</p>
          </div>
        </div>
      </div>

      <!-- Results column -->
      <div class="ks-methods-results__col">
        <h3 class="ks-type-eyebrow" style="color: var(--color-primary); margin-bottom: 12px;">Key Results</h3>
        <div class="ks-methods-results__items">
          <div v-for="r in results" :key="r.id" class="ks-card ks-methods-results__result">
            <div class="ks-methods-results__result-header">
              <span class="ks-type-data" style="font-weight: 600;">{{ r.metric }}</span>
              <span :style="{ color: r.positive ? 'var(--color-primary)' : '#B54A4A' }" class="ks-methods-results__result-value">
                {{ r.value }}
              </span>
            </div>
            <div v-if="r.comparison" class="ks-methods-results__result-compare">
              <span class="ks-type-data">vs {{ r.comparison }}</span>
              <span v-if="r.delta" :style="{ color: r.positive ? 'var(--color-primary)' : '#B54A4A' }" class="ks-type-data" style="font-weight: 700;">
                {{ r.delta }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.ks-methods-results__highlights {
  margin-top: 16px;
  margin-bottom: 24px;
}

.ks-methods-results__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-top: 16px;
}

.ks-methods-results__items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ks-methods-results__item {
  padding: 14px 16px;
}

.ks-methods-results__highlight {
  padding: 14px 16px;
}

.ks-methods-results__item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.ks-methods-results__item-name {
  font: 600 0.9375rem / 1.3 var(--font-serif);
  color: var(--color-text);
}

.ks-methods-results__result {
  padding: 14px 16px;
}

.ks-methods-results__result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ks-methods-results__result-value {
  font: 700 1.25rem / 1 var(--font-mono);
}

.ks-methods-results__result-compare {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid var(--color-border);
}

@media (max-width: 768px) {
  .ks-methods-results__grid {
    grid-template-columns: 1fr;
  }
}
</style>
