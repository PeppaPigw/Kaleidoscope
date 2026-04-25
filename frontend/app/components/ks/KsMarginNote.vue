<script setup lang="ts">
/**
 * KsMarginNote — Editorial margin note for side commentary.
 *
 * On wide viewports (≥72rem), floats to the right margin of the content area.
 * On narrower viewports, renders inline below the current paragraph.
 * Used for AI provenance annotations, supplementary context, and
 * editorial commentary.
 *
 * Usage:
 *   <div style="position: relative;">
 *     <p>Main paragraph text...</p>
 *     <KsMarginNote>This paragraph draws on CrossRef data.</KsMarginNote>
 *   </div>
 *
 * @slot default — Note content
 * @slot icon — Optional icon before the note text
 */

export interface KsMarginNoteProps {
  /** Optional label above the note (e.g. "AI Note", "Editor") */
  label?: string;
}

withDefaults(defineProps<KsMarginNoteProps>(), {
  label: undefined,
});
</script>

<template>
  <aside class="ks-margin-note" aria-label="Margin note">
    <span v-if="label" class="ks-margin-note__label">{{ label }}</span>
    <span v-if="$slots.icon" class="ks-margin-note__icon" aria-hidden="true">
      <slot name="icon" />
    </span>
    <slot />
  </aside>
</template>

<style scoped>
.ks-margin-note__label {
  display: block;
  margin-bottom: 4px;
  font: 600 0.625rem / 1 var(--font-sans);
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--color-accent);
}

.ks-margin-note__icon {
  display: inline-flex;
  margin-right: 4px;
  vertical-align: middle;
  opacity: 0.7;
}
</style>
