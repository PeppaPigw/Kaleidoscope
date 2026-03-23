<script setup lang="ts">
/**
 * TrendSnapshot — Compact trend card with sparkline and related topics.
 *
 * Shows the top trending research topic with a 30-day sparkline chart,
 * percentage change, and related topic pills. SVG sparkline is generated
 * from data points rather than hardcoded.
 */

export interface TrendSnapshotProps {
  /** Topic name */
  topic: string
  /** Percentage change (e.g. "+36%") */
  change: string
  /** Period label (e.g. "30-day trend") */
  period: string
  /** Description text */
  description: string
  /** Related topic labels */
  relatedTopics?: string[]
  /** Sparkline data points (0-100 normalized) */
  sparklineData?: number[]
}

const props = withDefaults(defineProps<TrendSnapshotProps>(), {
  relatedTopics: () => [],
  sparklineData: () => [10, 15, 22, 18, 35, 42, 38, 55, 62, 58, 72, 78, 82, 88],
})

defineEmits<{ click: [] }>()

/**
 * Convert data points to SVG polyline points string.
 * Maps to a 264×112 viewBox.
 */
const uid = useId()

const sparklinePoints = computed(() => {
  const data = props.sparklineData
  if (data.length < 2) return ''

  const viewW = 264
  const viewH = 112
  const padding = 8
  const maxVal = Math.max(...data)
  const minVal = Math.min(...data)
  const range = maxVal - minVal || 1

  return data
    .map((val, i) => {
      const x = (i / Math.max(data.length - 1, 1)) * viewW
      const y = viewH - padding - ((val - minVal) / range) * (viewH - padding * 2)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
})

const endPoint = computed(() => {
  const data = props.sparklineData
  if (data.length < 2) return { x: 0, y: 0 }

  const viewW = 264
  const viewH = 112
  const padding = 8
  const maxVal = Math.max(...data)
  const minVal = Math.min(...data)
  const range = maxVal - minVal || 1

  const lastVal = data[data.length - 1]!
  return {
    x: viewW,
    y: viewH - padding - ((lastVal - minVal) / range) * (viewH - padding * 2),
  }
})
</script>

<template>
  <section
    class="ks-trend-snapshot ks-card ks-motion-paper-reveal ks-motion-paper-reveal--delay-3"
    :aria-labelledby="`${uid}-title`"
    role="button"
    tabindex="0"
    @click="$emit('click')"
    @keydown.enter="$emit('click')"
    @keydown.space.prevent="$emit('click')"
  >
    <h3 :id="`${uid}-title`" class="ks-type-section-title">Trending</h3>
    <p class="ks-type-label">{{ topic }}</p>

    <!-- Sparkline -->
    <div class="ks-trend-snapshot__chart">
      <svg viewBox="0 0 264 112" class="ks-trend-snapshot__sparkline" aria-hidden="true">
        <polyline
          fill="none"
          stroke="var(--color-primary)"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          :points="sparklinePoints"
        />
        <circle
          :cx="endPoint.x"
          :cy="endPoint.y"
          r="4"
          fill="var(--color-accent)"
        />
      </svg>
    </div>

    <!-- Change stat -->
    <div class="ks-trend-snapshot__value">
      <span class="ks-type-stat-lg">{{ change }}</span>
      <span class="ks-type-label" style="color: var(--color-primary);">{{ period }}</span>
    </div>
    <p class="ks-type-body-sm" style="color: var(--color-secondary);">
      {{ description }}
    </p>

    <!-- Related topics -->
    <div v-if="relatedTopics.length > 0" class="ks-trend-snapshot__pills">
      <KsTag
        v-for="rt in relatedTopics"
        :key="rt"
        variant="primary"
      >
        {{ rt }}
      </KsTag>
    </div>
  </section>
</template>

<style scoped>
.ks-trend-snapshot {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  cursor: pointer;
  transition: transform var(--duration-normal) var(--ease-spring),
              box-shadow var(--duration-normal) var(--ease-smooth);
}

.ks-trend-snapshot:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(26, 26, 26, 0.06);
}

.ks-trend-snapshot:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-trend-snapshot__chart {
  width: 100%;
}

.ks-trend-snapshot__sparkline {
  width: 100%;
  height: auto;
}

.ks-trend-snapshot__value {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.ks-trend-snapshot__pills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
</style>
