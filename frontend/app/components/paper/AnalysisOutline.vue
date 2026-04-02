<script setup lang="ts">
/**
 * AnalysisOutline — Grok-style page progress bar (right edge, fixed).
 *
 * Accepts a flat list of page items (page sections + analysis headings).
 * Level 1  = page-level section (longest tick, brightest)
 * Level 2  = H2 heading inside deep analysis
 * Level 3+ = H3+ heading inside deep analysis (shortest)
 *
 * Active state is driven by the parent's scroll tracker.
 * Clicking a tick emits `jump(id)` — parent scrolls to that element.
 * Tooltip appears on hover (no text otherwise).
 */

export interface OutlineItem {
  id: string
  title: string
  level: number // 1 = page section, 2 = H2, 3+ = H3+
}

const props = defineProps<{
  items: OutlineItem[]
  activeIdx: number
}>()

const emit = defineEmits<{
  jump: [id: string]
}>()

const hoveredIdx = ref<number | null>(null)

function topPct(i: number): number {
  if (props.items.length <= 1) return 50
  return (i / (props.items.length - 1)) * 100
}

function tickWidth(level: number): number {
  if (level <= 1) return 26   // page section — longest
  if (level === 2) return 16  // H2
  return 9                    // H3+
}
</script>

<template>
  <Teleport to="body">
    <div v-if="items.length > 1" class="ao-root">
      <!-- Vertical spine -->
      <div class="ao-spine" />

      <!-- Ticks (one per item) -->
      <div
        v-for="(item, i) in items"
        :key="item.id"
        class="ao-tick"
        :class="{
          'ao-tick--active': activeIdx === i,
          'ao-tick--section': item.level <= 1,
        }"
        :style="{
          top: `${topPct(i)}%`,
          width: `${tickWidth(item.level)}px`,
        }"
        @mouseenter="hoveredIdx = i"
        @mouseleave="hoveredIdx = null"
        @click="emit('jump', item.id)"
      />

      <!-- Single shared tooltip -->
      <Transition name="ao-fade">
        <div
          v-if="hoveredIdx !== null"
          class="ao-tooltip"
          :style="{ top: `${topPct(hoveredIdx)}%` }"
        >
          {{ items[hoveredIdx].title }}
        </div>
      </Transition>
    </div>
  </Teleport>
</template>

<style scoped>
.ao-root {
  position: fixed;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  height: 72vh;
  width: 34px;       /* accommodate max tick length + a touch of breathing room */
  z-index: 60;
  pointer-events: none;
}

/* Spine — 1 px vertical line */
.ao-spine {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 1px;
  background: rgba(100, 116, 139, 0.2);
}

/* Individual tick */
.ao-tick {
  position: absolute;
  right: 0;
  height: 1px;
  transform: translateY(-50%);
  background: rgba(100, 116, 139, 0.35);
  cursor: pointer;
  pointer-events: all;
  transition: background 0.15s;
}

/* Emphasis for page-level sections */
.ao-tick--section {
  background: rgba(100, 116, 139, 0.6);
  height: 1.5px;
}

.ao-tick:hover {
  background: rgba(203, 213, 225, 0.8);
}

/* Active tick — clearly highlighted */
.ao-tick--active {
  background: rgba(203, 213, 225, 0.95) !important;
}

.ao-tick--section.ao-tick--active {
  height: 2px;
}

/* Tooltip */
.ao-tooltip {
  position: absolute;
  right: calc(100% + 10px);
  transform: translateY(-50%);
  white-space: nowrap;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  background: var(--color-surface, #0f172a);
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.15));
  color: var(--color-primary, #f1f5f9);
  font: 400 0.72rem / 1.4 var(--font-sans);
  padding: 4px 9px;
  border-radius: 4px;
  pointer-events: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.45);
}

.ao-fade-enter-active,
.ao-fade-leave-active { transition: opacity 0.12s; }
.ao-fade-enter-from,
.ao-fade-leave-to    { opacity: 0; }
</style>
