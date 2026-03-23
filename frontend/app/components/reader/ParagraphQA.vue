<script setup lang="ts">
/**
 * ParagraphQA — Q&A panel for paragraph-level questions.
 */

export interface ParagraphQuestion {
  id: string
  question: string
  answer: string
  paragraph: number
  source: string
}

export interface ParagraphQAProps {
  questions: ParagraphQuestion[]
}

defineProps<ParagraphQAProps>()

const uid = useId()
const expandedId = ref<string | null>(null)

function toggle(id: string) {
  expandedId.value = expandedId.value === id ? null : id
}
</script>

<template>
  <section class="ks-paragraph-qa ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <h3 :id="`${uid}-title`" class="ks-type-eyebrow" style="color: var(--color-accent); margin-bottom: 12px;">
      Paragraph Q&A
    </h3>

    <div class="ks-paragraph-qa__list">
      <div
        v-for="q in questions"
        :key="q.id"
        :class="['ks-paragraph-qa__item', { 'ks-paragraph-qa__item--expanded': expandedId === q.id }]"
      >
        <button
          type="button"
          class="ks-paragraph-qa__question"
          :aria-expanded="expandedId === q.id"
          :aria-controls="`${uid}-answer-${q.id}`"
          @click="toggle(q.id)"
        >
          <span class="ks-paragraph-qa__q-icon" aria-hidden="true">Q</span>
          <span class="ks-paragraph-qa__q-text">{{ q.question }}</span>
          <span class="ks-paragraph-qa__toggle" aria-hidden="true">{{ expandedId === q.id ? '−' : '+' }}</span>
        </button>
        <div
          v-if="expandedId === q.id"
          :id="`${uid}-answer-${q.id}`"
          class="ks-paragraph-qa__answer"
          role="region"
        >
          <p class="ks-paragraph-qa__a-text">{{ q.answer }}</p>
          <div class="ks-paragraph-qa__a-meta">
            <span class="ks-type-data">¶ {{ q.paragraph }}</span>
            <span class="ks-type-data" style="color: var(--color-primary);">{{ q.source }}</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.ks-paragraph-qa__list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ks-paragraph-qa__item {
  border: 1px solid var(--color-border);
  border-radius: 2px;
  overflow: hidden;
  transition: border-color var(--duration-fast) var(--ease-smooth);
}

.ks-paragraph-qa__item--expanded {
  border-color: var(--color-primary);
}

.ks-paragraph-qa__question {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  background: none;
  cursor: pointer;
  text-align: left;
}

.ks-paragraph-qa__question:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}

.ks-paragraph-qa__q-icon {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font: 700 0.75rem / 1 var(--font-mono);
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  border-radius: 2px;
}

.ks-paragraph-qa__q-text {
  flex: 1;
  font: 500 0.875rem / 1.4 var(--font-serif);
  color: var(--color-text);
}

.ks-paragraph-qa__toggle {
  font: 700 1rem / 1 var(--font-mono);
  color: var(--color-secondary);
}

.ks-paragraph-qa__answer {
  padding: 0 12px 12px 42px;
}

.ks-paragraph-qa__a-text {
  font: 400 0.875rem / 1.6 var(--font-serif);
  color: var(--color-text);
}

.ks-paragraph-qa__a-meta {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}
</style>
