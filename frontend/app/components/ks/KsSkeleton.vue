<script setup lang="ts">
/**
 * KsSkeleton — Warm-toned loading skeleton placeholder.
 *
 * Renders a pulsing block with configurable shape (line, circle, paragraph,
 * card). Used inside every data-dependent component as the loading state
 * instead of spinners — per editorial design guidelines.
 *
 * Usage:
 *   <KsSkeleton variant="line" />         — single text line
 *   <KsSkeleton variant="circle" />       — avatar circle
 *   <KsSkeleton variant="paragraph" />    — 4-line paragraph block
 *   <KsSkeleton variant="card" />         — full card skeleton
 *   <KsSkeleton class="h-48 w-full" />    — custom dimensions via class
 */

export interface KsSkeletonProps {
  variant?: 'line' | 'circle' | 'paragraph' | 'card' | 'custom'
  /** Width override (CSS value). Ignored for paragraph/card. */
  width?: string
  /** Height override (CSS value). Ignored for paragraph/card. */
  height?: string
  /** Number of lines in paragraph mode */
  lines?: number
  /** Animate pulse — disable for reduced-motion fallback */
  animate?: boolean
}

const props = withDefaults(defineProps<KsSkeletonProps>(), {
  variant: 'custom',
  width: undefined,
  height: undefined,
  lines: 4,
  animate: true,
})

const rootStyle = computed(() => {
  if (props.variant === 'paragraph' || props.variant === 'card') return {}
  return {
    width: props.width,
    height: props.height,
  }
})

const lineWidths = computed(() => {
  const widths = ['100%', '92%', '85%', '72%', '60%', '88%', '78%', '95%']
  return Array.from({ length: props.lines }, (_, i) => widths[i % widths.length])
})
</script>

<template>
  <!-- Single line / circle / custom -->
  <div
    v-if="variant === 'line' || variant === 'circle' || variant === 'custom'"
    :class="[
      'ks-skeleton',
      { 'ks-skeleton--circle': variant === 'circle' },
      { 'ks-skeleton--line': variant === 'line' },
      { 'ks-skeleton--no-animate': !animate },
    ]"
    :style="rootStyle"
    role="progressbar"
    aria-label="Loading content"
    aria-busy="true"
  />

  <!-- Paragraph — stacked lines with staggered widths -->
  <div
    v-else-if="variant === 'paragraph'"
    class="ks-skeleton-paragraph"
    role="progressbar"
    aria-label="Loading text content"
    aria-busy="true"
  >
    <div
      v-for="(w, i) in lineWidths"
      :key="i"
      class="ks-skeleton ks-skeleton--line"
      :class="{ 'ks-skeleton--no-animate': !animate }"
      :style="{ width: w, animationDelay: `${i * 60}ms` }"
    />
  </div>

  <!-- Card skeleton — image block + paragraph + meta line -->
  <div
    v-else-if="variant === 'card'"
    class="ks-skeleton-card"
    role="progressbar"
    aria-label="Loading card"
    aria-busy="true"
  >
    <div
      class="ks-skeleton ks-skeleton-card__image"
      :class="{ 'ks-skeleton--no-animate': !animate }"
    />
    <div class="ks-skeleton-card__body">
      <div
        class="ks-skeleton ks-skeleton--line ks-skeleton-card__title"
        :class="{ 'ks-skeleton--no-animate': !animate }"
      />
      <div
        class="ks-skeleton ks-skeleton--line"
        :class="{ 'ks-skeleton--no-animate': !animate }"
        style="width: 88%"
      />
      <div
        class="ks-skeleton ks-skeleton--line"
        :class="{ 'ks-skeleton--no-animate': !animate }"
        style="width: 64%"
      />
      <div class="ks-skeleton-card__meta">
        <div
          class="ks-skeleton"
          :class="{ 'ks-skeleton--no-animate': !animate }"
          style="width: 60px; height: 22px"
        />
        <div
          class="ks-skeleton"
          :class="{ 'ks-skeleton--no-animate': !animate }"
          style="width: 80px; height: 22px"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ─── Single line ──────────────────────────────────── */
.ks-skeleton--line {
  height: 14px;
  width: 100%;
  border-radius: 2px;
}

/* ─── Circle (avatar) ──────────────────────────────── */
.ks-skeleton--circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

/* ─── Paragraph ────────────────────────────────────── */
.ks-skeleton-paragraph {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* ─── Card skeleton ────────────────────────────────── */
.ks-skeleton-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  overflow: hidden;
  background: var(--color-surface);
}

.ks-skeleton-card__image {
  height: 160px;
  border-radius: 0;
}

.ks-skeleton-card__body {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ks-skeleton-card__title {
  height: 18px !important;
  width: 72%;
}

.ks-skeleton-card__meta {
  display: flex;
  gap: 8px;
  margin-top: 6px;
}

/* ─── No-animate override ──────────────────────────── */
.ks-skeleton--no-animate {
  animation: none;
  opacity: 0.72;
}
</style>
