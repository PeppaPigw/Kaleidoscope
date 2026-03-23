<script setup lang="ts">
/**
 * Marginalia — Annotation panel for highlights and notes.
 */

export interface Annotation {
  id: string
  text: string
  page: number
  color: 'yellow' | 'green' | 'blue' | 'pink'
  note?: string
}

export interface MarginaliaProps {
  annotations: Annotation[]
}

defineProps<MarginaliaProps>()
defineEmits<{ 'annotation-click': [annotation: Annotation] }>()

const uid = useId()

const colorMap: Record<Annotation['color'], string> = {
  yellow: 'rgba(196, 163, 90, 0.15)',
  green: 'rgba(13, 115, 119, 0.12)',
  blue: 'rgba(59, 130, 246, 0.12)',
  pink: 'rgba(236, 72, 153, 0.12)',
}
</script>

<template>
  <section class="ks-marginalia ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <h3 :id="`${uid}-title`" class="ks-type-eyebrow" style="color: var(--color-accent); margin-bottom: 12px;">
      Annotations ({{ annotations.length }})
    </h3>

    <div class="ks-marginalia__list">
      <button
        v-for="a in annotations"
        :key="a.id"
        type="button"
        class="ks-marginalia__item"
        :style="{ borderLeftColor: a.color, background: colorMap[a.color] }"
        :aria-label="`${a.text}${a.note ? '. Note: ' + a.note : ''}. Page ${a.page}`"
        @click="$emit('annotation-click', a)"
      >
        <p class="ks-marginalia__text">{{ a.text }}</p>
        <div class="ks-marginalia__meta">
          <span class="ks-type-data">Page {{ a.page }}</span>
          <KsTag v-if="a.note" variant="accent">has note</KsTag>
        </div>
        <p v-if="a.note" class="ks-marginalia__note">{{ a.note }}</p>
      </button>
    </div>
  </section>
</template>

<style scoped>
.ks-marginalia__list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ks-marginalia__item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border: none;
  border-left: 3px solid var(--color-accent-decorative);
  border-radius: 0 2px 2px 0;
  text-align: left;
  cursor: pointer;
  transition: transform var(--duration-fast) var(--ease-smooth);
}

.ks-marginalia__item:hover {
  transform: translateX(2px);
}

.ks-marginalia__item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-marginalia__text {
  font: 400 0.875rem / 1.5 var(--font-serif);
  color: var(--color-text);
}

.ks-marginalia__meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ks-marginalia__note {
  font: italic 400 0.8125rem / 1.4 var(--font-serif);
  color: var(--color-secondary);
  margin-top: 2px;
}
</style>
