<script setup lang="ts">
/**
 * KsFullBleed — Full-width bleed image container.
 *
 * Breaks out of the content column to span the full viewport width.
 * Typically used for hero images, paper header visuals, or editorial
 * photo spreads. Includes an optional figcaption.
 *
 * Usage:
 *   <KsFullBleed src="/images/cover.jpg" alt="Paper cover image">
 *     <template #caption>Figure 1 — Attention visualization</template>
 *   </KsFullBleed>
 *
 * @slot caption — Optional figure caption below the image
 */

export interface KsFullBleedProps {
  /** Image source URL */
  src: string
  /** Alt text for accessibility */
  alt: string
  /** Aspect ratio override (default: 16/7) */
  aspectRatio?: string
  /** Object-fit override */
  objectFit?: 'cover' | 'contain' | 'fill'
}

withDefaults(defineProps<KsFullBleedProps>(), {
  aspectRatio: '16 / 7',
  objectFit: 'cover',
})
</script>

<template>
  <figure class="ks-full-bleed">
    <img
      :src="src"
      :alt="alt"
      :style="{ aspectRatio, objectFit }"
      loading="lazy"
      decoding="async"
    >
    <figcaption v-if="$slots.caption">
      <slot name="caption" />
    </figcaption>
  </figure>
</template>

<style scoped>
/* Styling is fully handled by global .ks-full-bleed in editorial.css.
   Component adds loading/decoding attrs for performance. */
</style>
