<script setup lang="ts">
/**
 * ReadingQueue — Ordered reading queue with drag handles.
 *
 * Shows a prioritized list of papers to read, each with estimated reading
 * time and reading mode. Items appear draggable with a grip handle.
 */

export interface QueueItem {
  id: string;
  title: string;
  time: string;
  mode: string;
}

export interface ReadingQueueProps {
  items: QueueItem[];
}

defineProps<ReadingQueueProps>();

defineEmits<{
  "item-click": [item: QueueItem];
}>();

const uid = useId();
</script>

<template>
  <section
    class="ks-reading-queue ks-card ks-motion-paper-reveal ks-motion-paper-reveal--delay-4"
    :aria-labelledby="`${uid}-title`"
  >
    <h3 :id="`${uid}-title`" class="ks-type-section-title">Reading Queue</h3>
    <ol class="ks-reading-queue__list" :aria-labelledby="`${uid}-title`">
      <li v-for="item in items" :key="item.id" class="ks-reading-queue__li">
        <a
          :href="`/reader/${item.id}`"
          class="ks-reading-queue__item"
          @click.prevent="$emit('item-click', item)"
        >
          <div class="ks-reading-queue__item-drag" aria-hidden="true">
            <svg width="8" height="14" viewBox="0 0 8 14" fill="none">
              <circle cx="2" cy="2" r="1.5" fill="currentColor" opacity="0.3" />
              <circle cx="6" cy="2" r="1.5" fill="currentColor" opacity="0.3" />
              <circle cx="2" cy="7" r="1.5" fill="currentColor" opacity="0.3" />
              <circle cx="6" cy="7" r="1.5" fill="currentColor" opacity="0.3" />
              <circle
                cx="2"
                cy="12"
                r="1.5"
                fill="currentColor"
                opacity="0.3"
              />
              <circle
                cx="6"
                cy="12"
                r="1.5"
                fill="currentColor"
                opacity="0.3"
              />
            </svg>
          </div>
          <div class="ks-reading-queue__item-info">
            <span class="ks-reading-queue__item-title">{{ item.title }}</span>
            <span class="ks-type-data">{{ item.time }} · {{ item.mode }}</span>
          </div>
        </a>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.ks-reading-queue {
  padding: 24px;
}

.ks-reading-queue__list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
  list-style: none;
  padding: 0;
}

.ks-reading-queue__li {
  list-style: none;
}

.ks-reading-queue__item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--color-surface);
  border-radius: 4px;
  cursor: grab;
  text-decoration: none;
  color: inherit;
  transition:
    background-color var(--duration-fast) var(--ease-smooth),
    transform var(--duration-normal) var(--ease-spring);
}

.ks-reading-queue__item:hover {
  background: rgba(13, 115, 119, 0.06);
}

.ks-reading-queue__item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-reading-queue__item-drag {
  color: var(--color-secondary);
  cursor: grab;
  flex-shrink: 0;
}

.ks-reading-queue__item-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ks-reading-queue__item-title {
  font: 600 1rem / 1.35 var(--font-serif);
  color: var(--color-text);
}
</style>
