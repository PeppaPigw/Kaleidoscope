<script setup lang="ts">
/**
 * RecommendationStream — Grid of recommended paper cards.
 *
 * Displays a 2-column grid of paper recommendation cards with
 * eyebrow labels, relevance scores, abstracts, venue/tags meta,
 * and hover-revealed action buttons (Save/Compare).
 */

export interface RecommendedPaper {
  id: string
  eyebrow: string
  title: string
  abstract: string
  venue: string
  score: number
  tags: string[]
  /** Whether the paper has extra emphasis (teal top border) */
  strong: boolean
}

export interface RecommendationStreamProps {
  papers: RecommendedPaper[]
}

defineProps<RecommendationStreamProps>()

defineEmits<{
  'paper-click': [paper: RecommendedPaper]
  'save': [paper: RecommendedPaper]
  'compare': [paper: RecommendedPaper]
}>()

const uid = useId()
</script>

<template>
  <section class="ks-recommendation-stream" :aria-labelledby="`${uid}-title`">
    <h3 :id="`${uid}-title`" class="sr-only">Paper Recommendations</h3>
    <div class="ks-recommendation-stream__grid">
      <a
        v-for="(paper, i) in papers"
        :key="paper.id"
        :href="`/papers/${paper.id}`"
        :class="[
          'ks-card ks-recommendation-stream__card',
          { 'ks-recommendation-stream__card--strong': paper.strong },
          'ks-motion-paper-reveal',
          `ks-motion-paper-reveal--delay-${(i % 3) + 1}`,
        ]"
        @click.prevent="$emit('paper-click', paper)"
      >
        <div class="ks-recommendation-stream__card-header">
          <span class="ks-type-eyebrow" style="color: var(--color-accent);">
            {{ paper.eyebrow }}
          </span>
          <span class="ks-type-data" style="color: var(--color-primary);">
            {{ (paper.score * 100).toFixed(0) }}%
          </span>
        </div>
        <KsTranslatableTitle :text="paper.title" tag="h4" title-class="ks-recommendation-stream__card-title" />
        <p class="ks-type-body-sm ks-recommendation-stream__card-abstract">
          {{ paper.abstract }}
        </p>
        <KsTranslateBtn :text="paper.abstract" />
        <div class="ks-recommendation-stream__card-meta">
          <span class="ks-type-data">{{ paper.venue }}</span>
          <KsTag
            v-for="tag in paper.tags"
            :key="tag"
            variant="primary"
          >
            {{ tag }}
          </KsTag>
        </div>
        <div class="ks-recommendation-stream__card-actions">
          <KsButton
            variant="secondary"
            size="sm"
            :aria-label="`Save ${paper.title}`"
            @click.stop.prevent="$emit('save', paper)"
          >
            Save
          </KsButton>
          <KsButton
            variant="secondary"
            size="sm"
            :aria-label="`Compare ${paper.title}`"
            @click.stop.prevent="$emit('compare', paper)"
          >
            Compare
          </KsButton>
        </div>
      </a>
    </div>
  </section>
</template>

<style scoped>
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.ks-recommendation-stream__grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.ks-recommendation-stream__card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 24px;
  text-decoration: none;
  color: inherit;
  cursor: pointer;
}

.ks-recommendation-stream__card--strong {
  border-top: 2px solid var(--color-primary);
}

.ks-recommendation-stream__card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 24px rgba(26, 26, 26, 0.06);
}

.ks-recommendation-stream__card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ks-recommendation-stream__card-link {
  text-decoration: none;
  color: inherit;
}

.ks-recommendation-stream__card-link:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: 2px;
}

.ks-recommendation-stream__card-title {
  font: 600 1.125rem / 1.4 var(--font-serif);
  color: var(--color-text);
}

.ks-recommendation-stream__card-abstract {
  color: var(--color-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ks-recommendation-stream__card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.ks-recommendation-stream__card-actions {
  display: flex;
  gap: 6px;
  opacity: 0;
  transition: opacity var(--duration-fast) var(--ease-smooth);
}

.ks-recommendation-stream__card:hover .ks-recommendation-stream__card-actions,
.ks-recommendation-stream__card:focus-within .ks-recommendation-stream__card-actions {
  opacity: 1;
}

@media (max-width: 1280px) {
  .ks-recommendation-stream__grid {
    grid-template-columns: 1fr;
  }
}
</style>
