<script setup lang="ts">
/**
 * TopicsWall — Editorial cover cards for curated research collections.
 *
 * Displays a 2×2 grid of topic "covers" styled after magazine covers.
 * Each cover card shows a collection label, title, subtitle, paper count,
 * and a subtle teal/gold gradient accent.
 */

export interface TopicCover {
  id: string;
  label: string;
  title: string;
  subtitle: string;
  count: number;
  accent: "teal" | "gold";
}

export interface TopicsWallProps {
  topics: TopicCover[];
}

defineProps<TopicsWallProps>();

defineEmits<{
  "topic-click": [topic: TopicCover];
}>();

const uid = useId();
</script>

<template>
  <section
    class="ks-topics-wall ks-motion-paper-reveal"
    :aria-labelledby="`${uid}-title`"
  >
    <h2 :id="`${uid}-title`" class="sr-only">Research Collections</h2>
    <div class="ks-topics-wall__grid">
      <button
        v-for="topic in topics"
        :key="topic.id"
        type="button"
        :class="[
          'ks-topics-wall__cover',
          `ks-topics-wall__cover--${topic.accent}`,
        ]"
        @click="$emit('topic-click', topic)"
      >
        <span class="ks-type-eyebrow" style="color: var(--color-accent)">
          {{ topic.label }}
        </span>
        <span class="ks-topics-wall__cover-title">{{ topic.title }}</span>
        <span class="ks-type-body-sm" style="color: var(--color-secondary)">
          {{ topic.subtitle }}
        </span>
        <span class="ks-type-data" style="color: var(--color-primary)">
          {{ topic.count }} papers
        </span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.ks-topics-wall__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  height: 100%;
}

.ks-topics-wall__cover {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 28px 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  cursor: pointer;
  text-align: left;
  transition:
    transform var(--duration-normal) var(--ease-spring),
    border-color var(--duration-fast) var(--ease-smooth),
    box-shadow var(--duration-normal) var(--ease-smooth);
}

.ks-topics-wall__cover:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
  border-color: var(--color-primary);
}

.ks-topics-wall__cover:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-topics-wall__cover--teal {
  background: linear-gradient(
    135deg,
    var(--gradient-teal-start) 0%,
    var(--color-surface) 60%
  );
}

.ks-topics-wall__cover--gold {
  background: linear-gradient(
    135deg,
    var(--gradient-gold-start) 0%,
    var(--color-surface) 60%
  );
}

.ks-topics-wall__cover-title {
  font: 600 1.5rem / 1.3 var(--font-display);
  color: var(--color-text);
}

@media (max-width: 768px) {
  .ks-topics-wall__grid {
    grid-template-columns: 1fr;
  }
}
</style>
