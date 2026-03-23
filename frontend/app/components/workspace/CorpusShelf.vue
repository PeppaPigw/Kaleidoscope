<script setup lang="ts">
/**
 * CorpusShelf — Paper collection within a workspace.
 */

export interface CorpusPaper {
  id: string
  title: string
  authors: string
  year: number
  status: 'read' | 'unread' | 'annotated'
}

export interface CorpusShelfProps {
  papers: CorpusPaper[]
}

defineProps<CorpusShelfProps>()
defineEmits<{ 'paper-click': [paper: CorpusPaper] }>()

const uid = useId()

type TagVariant = 'success' | 'neutral' | 'accent'

function statusVariant(s: CorpusPaper['status']): TagVariant {
  const map: Record<CorpusPaper['status'], TagVariant> = { read: 'success', unread: 'neutral', annotated: 'accent' }
  return map[s]
}
</script>

<template>
  <section class="ks-corpus-shelf ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <h2 :id="`${uid}-title`" class="ks-type-section-title">Corpus ({{ papers.length }} papers)</h2>

    <div class="ks-corpus-shelf__list">
      <button
        v-for="p in papers"
        :key="p.id"
        type="button"
        class="ks-corpus-shelf__item"
        :aria-label="`${p.title} by ${p.authors}`"
        @click="$emit('paper-click', p)"
      >
        <div class="ks-corpus-shelf__item-main">
          <span class="ks-corpus-shelf__title">{{ p.title }}</span>
          <span class="ks-type-data" style="color: var(--color-secondary);">{{ p.authors }} · {{ p.year }}</span>
        </div>
        <KsTag :variant="statusVariant(p.status)">{{ p.status }}</KsTag>
      </button>
    </div>
  </section>
</template>

<style scoped>
.ks-corpus-shelf__list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 12px;
}

.ks-corpus-shelf__item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
  border-radius: 2px;
  transition: background-color var(--duration-fast) var(--ease-smooth);
}

.ks-corpus-shelf__item:hover {
  background: rgba(250, 250, 247, 0.8);
}

.ks-corpus-shelf__item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-corpus-shelf__item-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ks-corpus-shelf__title {
  font: 500 0.9375rem / 1.4 var(--font-serif);
  color: var(--color-text);
}
</style>
