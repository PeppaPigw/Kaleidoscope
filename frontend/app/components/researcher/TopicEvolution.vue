<script setup lang="ts">
/**
 * TopicEvolution — Shows how a researcher's topics changed over time.
 *
 * Renders a horizontal timeline of research topics with
 * publication counts per period.
 */

export interface TopicPeriod {
  id: string;
  label: string;
  years: string;
  paperCount: number;
  active: boolean;
}

export interface TopicEvolutionProps {
  topics: TopicPeriod[];
}

const props = defineProps<TopicEvolutionProps>();
defineEmits<{ "topic-click": [topic: TopicPeriod] }>();

const uid = useId();
const maxPaperCount = computed(() =>
  Math.max(...props.topics.map((t) => t.paperCount), 1),
);
</script>

<template>
  <section
    class="ks-topic-evolution ks-motion-paper-reveal"
    :aria-labelledby="`${uid}-title`"
  >
    <h2 :id="`${uid}-title`" class="ks-type-section-title">Topic Evolution</h2>

    <div
      class="ks-topic-evolution__timeline"
      role="group"
      :aria-label="`${topics.length} research topics`"
    >
      <button
        v-for="topic in topics"
        :key="topic.id"
        type="button"
        :class="[
          'ks-topic-evolution__item',
          { 'ks-topic-evolution__item--active': topic.active },
        ]"
        :aria-pressed="topic.active"
        @click="$emit('topic-click', topic)"
      >
        <div class="ks-topic-evolution__bar" aria-hidden="true">
          <div
            class="ks-topic-evolution__fill"
            :style="{ height: `${(topic.paperCount / maxPaperCount) * 100}%` }"
          />
        </div>
        <span class="ks-topic-evolution__label">{{ topic.label }}</span>
        <span class="ks-type-data">{{ topic.years }}</span>
        <span
          class="ks-type-data"
          style="color: var(--color-primary); font-weight: 700"
          >{{ topic.paperCount }} papers</span
        >
      </button>
    </div>
  </section>
</template>

<style scoped>
.ks-topic-evolution__timeline {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.ks-topic-evolution__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  min-width: 130px;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  cursor: pointer;
  transition:
    border-color var(--duration-fast) var(--ease-smooth),
    background-color var(--duration-fast) var(--ease-smooth);
}

.ks-topic-evolution__item:hover {
  border-color: var(--color-primary);
  background: rgba(13, 115, 119, 0.03);
}

.ks-topic-evolution__item--active {
  border-color: var(--color-primary);
  background: rgba(13, 115, 119, 0.06);
}

.ks-topic-evolution__item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-topic-evolution__bar {
  width: 32px;
  height: 48px;
  background: rgba(196, 163, 90, 0.08);
  border-radius: 2px;
  display: flex;
  align-items: flex-end;
  overflow: hidden;
}

.ks-topic-evolution__fill {
  width: 100%;
  background: linear-gradient(
    180deg,
    var(--color-primary),
    var(--color-accent-decorative)
  );
  border-radius: 2px 2px 0 0;
  transition: height var(--duration-normal) var(--ease-spring);
}

.ks-topic-evolution__label {
  font: 600 0.8125rem / 1.3 var(--font-serif);
  color: var(--color-text);
  text-align: center;
}
</style>
