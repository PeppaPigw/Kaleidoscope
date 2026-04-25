<script setup lang="ts">
/**
 * SemanticHighlights — AI-detected key passages with category tags.
 */

export interface SemanticHighlight {
  id: string;
  text: string;
  category:
    | "hypothesis"
    | "methodology"
    | "result"
    | "limitation"
    | "contribution";
  confidence: number;
  page: number;
}

export interface SemanticHighlightsProps {
  highlights: SemanticHighlight[];
}

defineProps<SemanticHighlightsProps>();
defineEmits<{ "highlight-click": [highlight: SemanticHighlight] }>();

const uid = useId();

type TagVariant = "primary" | "accent" | "success" | "warning" | "neutral";

function catVariant(c: SemanticHighlight["category"]): TagVariant {
  const map: Record<SemanticHighlight["category"], TagVariant> = {
    hypothesis: "accent",
    methodology: "primary",
    result: "success",
    limitation: "warning",
    contribution: "neutral",
  };
  return map[c];
}
</script>

<template>
  <section
    class="ks-semantic-highlights ks-motion-paper-reveal"
    :aria-labelledby="`${uid}-title`"
  >
    <h3
      :id="`${uid}-title`"
      class="ks-type-eyebrow"
      style="color: var(--color-accent); margin-bottom: 12px"
    >
      AI Highlights ({{ highlights.length }})
    </h3>

    <div class="ks-semantic-highlights__list">
      <button
        v-for="h in highlights"
        :key="h.id"
        type="button"
        class="ks-card ks-semantic-highlights__item"
        :aria-label="`${h.category}: ${h.text.substring(0, 40)}...`"
        @click="$emit('highlight-click', h)"
      >
        <div class="ks-semantic-highlights__header">
          <KsTag :variant="catVariant(h.category)">{{ h.category }}</KsTag>
          <span class="ks-type-data" style="color: var(--color-primary)"
            >{{ (h.confidence * 100).toFixed(0) }}%</span
          >
        </div>
        <p class="ks-semantic-highlights__text">{{ h.text }}</p>
        <span class="ks-type-data">Page {{ h.page }}</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.ks-semantic-highlights__list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ks-semantic-highlights__item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 14px;
  text-align: left;
  cursor: pointer;
  transition:
    transform var(--duration-fast) var(--ease-smooth),
    box-shadow var(--duration-fast) var(--ease-smooth);
}

.ks-semantic-highlights__item:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(26, 26, 26, 0.06);
}

.ks-semantic-highlights__item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-semantic-highlights__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ks-semantic-highlights__text {
  font: 400 0.875rem / 1.5 var(--font-serif);
  color: var(--color-text);
}
</style>
