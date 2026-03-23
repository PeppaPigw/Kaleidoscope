<script setup lang="ts">
/**
 * ManuscriptOverview — Manuscript status dashboard.
 */

export interface ManuscriptSection {
  id: string
  title: string
  wordCount: number
  status: 'draft' | 'review' | 'complete' | 'empty'
  order: number
}

export interface ManuscriptOverviewProps {
  title: string
  targetVenue: string
  totalWordCount: number
  targetWordCount: number
  sections: ManuscriptSection[]
}

defineProps<ManuscriptOverviewProps>()
defineEmits<{ 'section-click': [section: ManuscriptSection] }>()

const uid = useId()

type TagVariant = 'warning' | 'accent' | 'success' | 'neutral'

function statusVariant(s: ManuscriptSection['status']): TagVariant {
  const map: Record<ManuscriptSection['status'], TagVariant> = { draft: 'warning', review: 'accent', complete: 'success', empty: 'neutral' }
  return map[s]
}
</script>

<template>
  <section class="ks-manuscript ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <div class="ks-manuscript__header">
      <div>
        <h2 :id="`${uid}-title`" class="ks-manuscript__title">{{ title }}</h2>
        <p class="ks-type-data" style="color: var(--color-accent);">Target: {{ targetVenue }}</p>
      </div>
      <div class="ks-manuscript__progress">
        <span class="ks-type-data" :style="{ color: totalWordCount >= targetWordCount ? 'var(--color-primary)' : 'var(--color-secondary)' }">
          {{ totalWordCount.toLocaleString() }} / {{ targetWordCount.toLocaleString() }} words
        </span>
        <div class="ks-manuscript__bar" aria-hidden="true">
          <div class="ks-manuscript__fill" :style="{ width: `${Math.min((totalWordCount / targetWordCount) * 100, 100)}%` }"></div>
        </div>
      </div>
    </div>

    <ol class="ks-manuscript__sections">
      <li v-for="s in sections" :key="s.id">
        <button type="button" class="ks-manuscript__section" @click="$emit('section-click', s)">
          <span class="ks-manuscript__section-title">{{ s.order }}. {{ s.title }}</span>
          <div class="ks-manuscript__section-meta">
            <span class="ks-type-data">{{ s.wordCount }} words</span>
            <KsTag :variant="statusVariant(s.status)">{{ s.status }}</KsTag>
          </div>
        </button>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.ks-manuscript__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.ks-manuscript__title {
  font: 600 1.5rem / 1.3 var(--font-display);
  color: var(--color-text);
}

.ks-manuscript__progress {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 200px;
}

.ks-manuscript__bar {
  height: 4px;
  background: var(--color-border);
  border-radius: 2px;
  overflow: hidden;
}

.ks-manuscript__fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary), var(--color-accent-decorative));
  border-radius: 2px;
  transition: width var(--duration-normal) var(--ease-smooth);
}

.ks-manuscript__sections {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ks-manuscript__section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 12px 14px;
  border: none;
  background: none;
  cursor: pointer;
  text-align: left;
  border-radius: 2px;
  transition: background-color var(--duration-fast) var(--ease-smooth);
}

.ks-manuscript__section:hover {
  background: rgba(250, 250, 247, 0.8);
}

.ks-manuscript__section:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-manuscript__section-title {
  font: 500 0.9375rem / 1.4 var(--font-serif);
  color: var(--color-text);
}

.ks-manuscript__section-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
