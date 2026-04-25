<script setup lang="ts">
/**
 * KsPullQuote — Editorial pull quote with gold accent border.
 *
 * Prominently displays a key quote or insight from a paper with the
 * editorial gold left-border and italic Playfair Display typography.
 * Optional citation attribution via the `cite` slot.
 *
 * Usage:
 *   <KsPullQuote>
 *     "The model achieves state-of-the-art performance..."
 *     <template #cite>Zhang et al., 2025</template>
 *   </KsPullQuote>
 *
 * @slot default — Quote text
 * @slot cite — Citation attribution line
 */

export interface KsPullQuoteProps {
  /** Align center or left (center = magazine, left = academic) */
  align?: "center" | "left";
}

withDefaults(defineProps<KsPullQuoteProps>(), {
  align: "center",
});
</script>

<template>
  <blockquote class="ks-pull-quote" :class="`ks-pull-quote--${align}`">
    <slot />
    <cite v-if="$slots.cite" class="ks-pull-quote__cite">
      <slot name="cite" />
    </cite>
  </blockquote>
</template>

<style scoped>
.ks-pull-quote--left {
  margin-left: 0;
  margin-right: auto;
}

.ks-pull-quote__cite {
  display: block;
  margin-top: 0.75rem;
  font: 600 0.72rem / 1.2 var(--font-sans);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-secondary);
  font-style: normal;
}
</style>
