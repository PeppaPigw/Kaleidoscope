<script setup lang="ts">
/**
 * KsSectionDivider — Decorative section divider with optional symbol label.
 *
 * Renders a horizontal rule with a fade-gradient line on each side and
 * an uppercase mono-spaced label in the center. Used to separate major
 * content sections within a page, evoking magazine issue dividers.
 *
 * Usage:
 *   <KsSectionDivider />              — plain horizontal rule
 *   <KsSectionDivider label="§" />    — with centered symbol
 *   <KsSectionDivider label="02" />   — with section number
 *
 * @slot default — Override the centered label content
 */

export interface KsSectionDividerProps {
  /** Text/symbol shown in the center. Ignored if default slot is used. */
  label?: string
}

withDefaults(defineProps<KsSectionDividerProps>(), {
  label: undefined,
})
</script>

<template>
  <div class="ks-section-divider" role="separator" aria-hidden="true">
    <span v-if="$slots.default || label">
      <slot>{{ label }}</slot>
    </span>
  </div>
</template>

<style scoped>
/* Styling is fully handled by global .ks-section-divider in editorial.css.
   The scoped block below provides fallback for dividers without a label. */

.ks-section-divider:not(:has(> span)) {
  display: block;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, var(--color-border) 20%, var(--color-border) 80%, transparent 100%);
  margin: clamp(2.5rem, 6vw, 5rem) 0;
}
</style>
