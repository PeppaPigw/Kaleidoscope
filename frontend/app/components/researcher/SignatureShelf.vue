<script setup lang="ts">
/**
 * SignatureShelf — Highlighted publications from a researcher.
 *
 * Shows the researcher's most impactful papers with citation
 * counts and quick navigation.
 */

export interface SignaturePaper {
  id: string
  title: string
  venue: string
  year: number
  citations: number
  highlight?: string
}

export interface SignatureShelfProps {
  papers: SignaturePaper[]
}

defineProps<SignatureShelfProps>()
defineEmits<{ 'paper-click': [paper: SignaturePaper] }>()

const uid = useId()
</script>

<template>
  <section class="ks-signature-shelf ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <h2 :id="`${uid}-title`" class="ks-type-section-title">Signature Papers</h2>

    <ol class="ks-signature-shelf__list">
      <li
        v-for="(paper, i) in papers"
        :key="paper.id"
        class="ks-signature-shelf__item"
      >
        <span class="ks-signature-shelf__rank" aria-hidden="true">{{ i + 1 }}</span>
        <button
          type="button"
          class="ks-signature-shelf__body"
          :aria-label="`${paper.title} - ${paper.citations} citations`"
          @click="$emit('paper-click', paper)"
        >
          <h3 class="ks-signature-shelf__title">{{ paper.title }}</h3>
          <div class="ks-signature-shelf__meta">
            <span class="ks-type-data">{{ paper.venue }} {{ paper.year }}</span>
            <span class="ks-type-data" style="color: var(--color-primary); font-weight: 700;">
              {{ paper.citations.toLocaleString() }} citations
            </span>
          </div>
          <p v-if="paper.highlight" class="ks-signature-shelf__highlight">{{ paper.highlight }}</p>
        </button>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.ks-signature-shelf__list {
  list-style: none;
  padding: 0;
  margin: 16px 0 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ks-signature-shelf__item {
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 2px;
  transition: background-color var(--duration-fast) var(--ease-smooth);
}

.ks-signature-shelf__item:hover {
  background: rgba(250, 250, 247, 0.8);
}

.ks-signature-shelf__rank {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font: 700 0.875rem / 1 var(--font-mono);
  color: var(--color-accent-decorative);
  border: 1px solid var(--color-border);
  border-radius: 50%;
}

.ks-signature-shelf__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}

.ks-signature-shelf__body:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 4px;
}

.ks-signature-shelf__title {
  font: 600 1rem / 1.4 var(--font-serif);
  color: var(--color-text);
  transition: color var(--duration-fast) var(--ease-smooth);
}

.ks-signature-shelf__body:hover .ks-signature-shelf__title {
  color: var(--color-primary);
}

.ks-signature-shelf__meta {
  display: flex;
  gap: 12px;
  align-items: center;
}

.ks-signature-shelf__highlight {
  font: 400 0.875rem / 1.5 var(--font-serif);
  color: var(--color-secondary);
  font-style: italic;
  margin-top: 2px;
}
</style>
