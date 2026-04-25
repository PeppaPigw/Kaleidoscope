<script setup lang="ts">
/**
 * BurstMoments — Trending research topics with burst detection.
 */

export interface BurstTopic {
  id: string;
  topic: string;
  paperCount: number;
  growth: number;
  period: string;
  trending: boolean;
}

export interface BurstMomentsProps {
  topics: BurstTopic[];
}

defineProps<BurstMomentsProps>();
defineEmits<{ "topic-click": [topic: BurstTopic] }>();

const uid = useId();
</script>

<template>
  <section
    class="ks-burst-moments ks-motion-paper-reveal"
    :aria-labelledby="`${uid}-title`"
  >
    <h2 :id="`${uid}-title`" class="ks-type-section-title">Burst Moments</h2>
    <p
      class="ks-type-body-sm"
      style="color: var(--color-secondary); margin-bottom: 16px"
    >
      Topics experiencing sudden research interest
    </p>

    <div class="ks-burst-moments__list">
      <button
        v-for="t in topics"
        :key="t.id"
        type="button"
        :class="[
          'ks-card ks-burst-moments__item',
          { 'ks-burst-moments__item--trending': t.trending },
        ]"
        @click="$emit('topic-click', t)"
      >
        <div class="ks-burst-moments__header">
          <span class="ks-burst-moments__topic">{{ t.topic }}</span>
          <KsTag v-if="t.trending" variant="accent">🔥 trending</KsTag>
        </div>
        <div class="ks-burst-moments__stats">
          <span class="ks-type-data">{{ t.paperCount }} papers</span>
          <span
            class="ks-type-data"
            :style="{
              color: t.growth > 0 ? 'var(--color-primary)' : '#B54A4A',
            }"
          >
            {{ t.growth > 0 ? "+" : "" }}{{ t.growth }}%
          </span>
          <span class="ks-type-data" style="color: var(--color-secondary)">{{
            t.period
          }}</span>
        </div>
      </button>
    </div>
  </section>
</template>

<style scoped>
.ks-burst-moments__list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ks-burst-moments__item {
  padding: 14px 16px;
  text-align: left;
  cursor: pointer;
  transition:
    transform var(--duration-fast) var(--ease-smooth),
    box-shadow var(--duration-fast) var(--ease-smooth);
}

.ks-burst-moments__item:hover {
  transform: translateX(4px);
}

.ks-burst-moments__item--trending {
  border-left: 3px solid var(--color-accent-decorative);
}

.ks-burst-moments__item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-burst-moments__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.ks-burst-moments__topic {
  font: 600 1rem / 1.3 var(--font-serif);
  color: var(--color-text);
}

.ks-burst-moments__stats {
  display: flex;
  gap: 16px;
}
</style>
