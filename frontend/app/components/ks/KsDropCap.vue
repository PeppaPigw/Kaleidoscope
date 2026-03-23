<script setup lang="ts">
/**
 * KsDropCap — Editorial drop capital letter.
 *
 * Wraps a paragraph and makes the first letter float as a large,
 * decorative initial capital in Playfair Display — a hallmark of
 * magazine/editorial layouts.
 *
 * Usage:
 *   <KsDropCap>Lorem ipsum dolor sit amet...</KsDropCap>
 *
 * @slot default — Paragraph text (first letter becomes the drop cap)
 */
</script>

<template>
  <p class="ks-drop-cap ks-type-body">
    <slot />
  </p>
</template>

<style scoped>
/* Extends the global .ks-drop-cap from editorial.css.
   Additional component-level refinements: */

.ks-drop-cap {
  position: relative;
  max-width: 68ch;
}

/* Ensure the drop cap letter gets proper vertical alignment
   across different font rendering engines */
.ks-drop-cap::first-letter {
  padding-top: 0.06em;
}
</style>
