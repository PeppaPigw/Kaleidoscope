<script setup lang="ts">
/**
 * RelatedConstellation — Related papers in a visual star-map layout.
 *
 * Shows conceptually, citation-linked, and methodologically related papers
 * as interactive cards with relationship labels.
 */

export interface RelatedPaper {
  id: string
  title: string
  venue: string
  year: number
  relationship: 'cites' | 'cited-by' | 'similar' | 'extends' | 'contradicts'
  similarity: number
}

export interface RelatedConstellationProps {
  papers: RelatedPaper[]
}

defineProps<RelatedConstellationProps>()
defineEmits<{ 'paper-click': [paper: RelatedPaper] }>()

const uid = useId()

type TagVariant = 'primary' | 'accent' | 'neutral' | 'danger'

function relColor(r: RelatedPaper['relationship']): TagVariant {
  switch (r) {
    case 'cites': return 'primary'
    case 'cited-by': return 'primary'
    case 'similar': return 'accent'
    case 'extends': return 'neutral'
    case 'contradicts': return 'danger'
  }
}
</script>

<template>
  <section class="ks-related-constellation ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <h2 :id="`${uid}-title`" class="ks-type-section-title">Related Papers</h2>

    <div class="ks-related-constellation__grid">
      <button
        v-for="paper in papers"
        :key="paper.id"
        type="button"
        class="ks-card ks-related-constellation__card"
        :aria-label="`${paper.title} (${paper.relationship})`"
        @click="$emit('paper-click', paper)"
      >
        <div class="ks-related-constellation__card-header">
          <KsTag :variant="relColor(paper.relationship)">{{ paper.relationship }}</KsTag>
          <span class="ks-type-data" style="color: var(--color-primary); font-weight: 700;">
            {{ (paper.similarity * 100).toFixed(0) }}%
          </span>
        </div>
        <span class="ks-related-constellation__card-title">{{ paper.title }}</span>
        <span class="ks-type-data">{{ paper.venue }} {{ paper.year }}</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.ks-related-constellation__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.ks-related-constellation__card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  text-align: left;
  cursor: pointer;
  transition: transform var(--duration-normal) var(--ease-spring),
              box-shadow var(--duration-normal) var(--ease-smooth);
}

.ks-related-constellation__card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(26, 26, 26, 0.06);
}

.ks-related-constellation__card:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-related-constellation__card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ks-related-constellation__card-title {
  font: 600 0.9375rem / 1.4 var(--font-serif);
  color: var(--color-text);
}
</style>
