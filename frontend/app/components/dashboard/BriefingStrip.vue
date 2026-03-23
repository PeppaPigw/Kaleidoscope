<script setup lang="ts">
/**
 * BriefingStrip — Horizontal scrolling news ticker for today's activity.
 *
 * Shows recent ingestion events, alerts, and code releases in a compact
 * ticker-tape format. Uses KsTag for type badges.
 */

export interface BriefingItem {
  id: string
  type: 'NEW' | 'ALERT' | 'CODE' | 'INGEST' | 'UPDATE'
  title: string
  time: string
}

export interface BriefingStripProps {
  items: BriefingItem[]
}

defineProps<BriefingStripProps>()

defineEmits<{
  'item-click': [item: BriefingItem]
}>()

const typeVariantMap: Record<BriefingItem['type'], 'primary' | 'accent' | 'success' | 'warning' | 'default'> = {
  NEW: 'primary',
  ALERT: 'accent',
  CODE: 'success',
  INGEST: 'default',
  UPDATE: 'warning',
}
</script>

<template>
  <section
    class="ks-briefing-strip ks-motion-paper-reveal ks-motion-paper-reveal--delay-2"
    aria-label="Today's briefing"
  >
    <span class="ks-briefing-strip__label ks-type-eyebrow">
      BRIEFING
    </span>
    <ul class="ks-briefing-strip__ticker">
      <li
        v-for="item in items"
        :key="item.id"
        class="ks-briefing-strip__li"
      >
        <button
          type="button"
          class="ks-briefing-strip__item"
          @click="$emit('item-click', item)"
        >
          <KsTag :variant="typeVariantMap[item.type]">
            {{ item.type }}
          </KsTag>
          <span class="ks-briefing-strip__item-title">{{ item.title }}</span>
          <span class="ks-type-data">{{ item.time }}</span>
        </button>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.ks-briefing-strip {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 16px;
  height: 56px;
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
  background: rgba(255, 255, 255, 0.72);
  overflow: hidden;
}

.ks-briefing-strip__label {
  flex-shrink: 0;
  color: var(--color-accent);
}

.ks-briefing-strip__ticker {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  scrollbar-width: none;
  list-style: none;
  margin: 0;
  padding: 0;
}

.ks-briefing-strip__ticker::-webkit-scrollbar {
  display: none;
}

.ks-briefing-strip__li {
  flex-shrink: 0;
}

.ks-briefing-strip__item {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  padding: 6px 12px;
  border: none;
  background: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-smooth),
              transform var(--duration-fast) var(--ease-smooth);
}

.ks-briefing-strip__item:hover {
  background: rgba(13, 115, 119, 0.06);
  transform: translateY(-2px);
}

.ks-briefing-strip__item-title {
  font: 600 0.875rem / 1.4 var(--font-serif);
  color: var(--color-text);
  white-space: nowrap;
}
</style>
