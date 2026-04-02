<script setup lang="ts">
/**
 * PublicationTimeline — Bar chart of publications per year.
 * Uses only CSS/HTML (no charting lib dependency).
 */

export interface YearlyPub {
  year: number
  count: number
}

interface Props {
  timeline: YearlyPub[]
}

const props = defineProps<Props>()
const uid = useId()

const maxCount = computed(() => Math.max(...props.timeline.map(t => t.count), 1))
const totalPapers = computed(() => props.timeline.reduce((s, t) => s + t.count, 0))
const activeYears = computed(() => props.timeline.length)
</script>

<template>
  <section v-if="timeline.length" class="ks-pub-timeline ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <div class="ks-pub-timeline__header">
      <h2 :id="`${uid}-title`" class="ks-type-section-title">Publications by Year</h2>
      <span class="ks-pub-timeline__summary ks-type-data">
        {{ totalPapers }} papers · {{ activeYears }} active years
      </span>
    </div>

    <div class="ks-pub-timeline__chart" role="img" :aria-label="`Publication counts from ${timeline[0]?.year} to ${timeline[timeline.length-1]?.year}`">
      <div
        v-for="bar in timeline"
        :key="bar.year"
        class="ks-pub-timeline__col"
      >
        <span class="ks-pub-timeline__count ks-type-data">{{ bar.count }}</span>
        <div class="ks-pub-timeline__bar-wrap" :title="`${bar.count} paper${bar.count !== 1 ? 's' : ''} in ${bar.year}`">
          <div
            class="ks-pub-timeline__bar"
            :style="{ height: `${(bar.count / maxCount) * 100}%` }"
          />
        </div>
        <span class="ks-pub-timeline__year ks-type-data">{{ bar.year }}</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.ks-pub-timeline__header {
  display: flex;
  align-items: baseline;
  gap: 16px;
  flex-wrap: wrap;
}

.ks-pub-timeline__summary {
  color: var(--color-secondary);
}

.ks-pub-timeline__chart {
  display: flex;
  align-items: stretch;
  gap: 6px;
  margin-top: 16px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.ks-pub-timeline__col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 36px;
  flex: 1;
}

.ks-pub-timeline__count {
  font-size: 10px;
  color: var(--color-secondary);
  line-height: 14px;
  height: 14px;
  flex-shrink: 0;
}

.ks-pub-timeline__bar-wrap {
  width: 100%;
  height: 80px;
  flex-shrink: 0;
  display: flex;
  align-items: flex-end;
}

.ks-pub-timeline__bar {
  width: 100%;
  min-height: 3px;
  background: linear-gradient(180deg, var(--color-primary), color-mix(in srgb, var(--color-primary) 60%, transparent));
  border-radius: 3px 3px 0 0;
  transition: height 0.4s var(--ease-spring, cubic-bezier(.34,1.56,.64,1));
}

.ks-pub-timeline__col:hover .ks-pub-timeline__bar {
  background: var(--color-accent-decorative, #c4a35a);
}

.ks-pub-timeline__year {
  font-size: 10px;
  color: var(--color-secondary);
  height: 14px;
  line-height: 14px;
  flex-shrink: 0;
  white-space: nowrap;
}
</style>
