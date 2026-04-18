<script setup lang="ts">
/**
 * ThesisLine — One-sentence thesis summary with AI provenance.
 *
 * A prominent pull-quote-style card showing the AI-extracted thesis,
 * with confidence indicator and linked provenance drawer trigger.
 */

export interface ThesisLineProps {
  thesis: string
  confidence: number
  modelSource: string
}

defineProps<ThesisLineProps>()
defineEmits<{ 'show-provenance': [] }>()
</script>

<template>
  <div class="ks-thesis-line ks-motion-paper-reveal">
    <div class="ks-thesis-line__accent" aria-hidden="true"/>
    <blockquote class="ks-thesis-line__text">
      {{ thesis }}
    </blockquote>
    <div class="ks-thesis-line__meta">
      <span class="ks-type-data">
        AI-extracted · {{ (confidence * 100).toFixed(0) }}% confidence
      </span>
      <button
        type="button"
        class="ks-thesis-line__provenance"
        @click="$emit('show-provenance')"
      >
        <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
        {{ modelSource }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.ks-thesis-line {
  position: relative;
  padding: 24px 24px 24px 28px;
  background: linear-gradient(135deg, rgba(196, 163, 90, 0.04), rgba(13, 115, 119, 0.02));
  border-radius: var(--radius-card);
  border: 1px solid var(--color-border);
}

.ks-thesis-line__accent {
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(180deg, var(--color-accent-decorative), var(--color-primary));
  border-radius: var(--radius-card) 0 0 var(--radius-card);
}

.ks-thesis-line__text {
  font: 500 1.25rem / 1.6 var(--font-serif);
  color: var(--color-text);
  margin: 0;
  quotes: none;
}

.ks-thesis-line__meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.ks-thesis-line__provenance {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 2px;
  font: 500 0.75rem / 1 var(--font-mono);
  color: var(--color-primary);
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-smooth);
}

.ks-thesis-line__provenance:hover {
  border-color: var(--color-primary);
}

.ks-thesis-line__provenance:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
</style>
