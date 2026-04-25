<script setup lang="ts">
/**
 * CompareStrip — Sticky bottom comparison tray.
 *
 * When users select papers via "Compare" buttons in result cards,
 * they appear as thumbnails in this strip. Supports up to 4 papers.
 * Shows compare CTA when ≥2 are selected.
 */

export interface CompareItem {
  id: string;
  title: string;
  venue: string;
  year: number;
}

export interface CompareStripProps {
  items: CompareItem[];
  maxItems?: number;
}

const props = withDefaults(defineProps<CompareStripProps>(), {
  maxItems: 4,
});

defineEmits<{
  remove: [item: CompareItem];
  compare: [];
  clear: [];
}>();

const canCompare = computed(() => props.items.length >= 2);
</script>

<template>
  <Transition name="ks-strip">
    <div
      v-if="items.length > 0"
      class="ks-compare-strip"
      role="region"
      aria-label="Paper comparison tray"
    >
      <div class="ks-compare-strip__items">
        <div
          v-for="item in items"
          :key="item.id"
          class="ks-compare-strip__item"
        >
          <div class="ks-compare-strip__item-info">
            <span class="ks-compare-strip__item-title">{{ item.title }}</span>
            <span class="ks-type-data">{{ item.venue }} {{ item.year }}</span>
          </div>
          <button
            type="button"
            class="ks-compare-strip__item-remove"
            :aria-label="`Remove ${item.title} from comparison`"
            @click="$emit('remove', item)"
          >
            ×
          </button>
        </div>
      </div>

      <div class="ks-compare-strip__actions">
        <span class="ks-type-data" style="color: var(--color-secondary)">
          {{ items.length }}/{{ maxItems }}
        </span>
        <KsButton variant="secondary" size="sm" @click="$emit('clear')">
          Clear
        </KsButton>
        <KsButton
          variant="primary"
          :disabled="!canCompare"
          @click="$emit('compare')"
        >
          Compare {{ items.length }} papers
        </KsButton>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.ks-compare-strip {
  position: fixed;
  bottom: 24px;
  left: calc(var(--sidebar-width) + 36px);
  right: 36px;
  max-width: 1600px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 20px;
  background: var(--color-glass-bg);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-float);
  transition:
    left var(--duration-normal) var(--ease-smooth),
    right var(--duration-normal) var(--ease-smooth),
    transform var(--duration-normal) var(--ease-spring),
    opacity var(--duration-fast) var(--ease-smooth);
  z-index: 50;
}

.ks-compare-strip__items {
  display: flex;
  gap: 8px;
  flex: 1;
  overflow-x: auto;
  scrollbar-width: thin;
}

.ks-compare-strip__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 2px;
  min-width: 180px;
  max-width: 260px;
  flex-shrink: 0;
}

.ks-compare-strip__item-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.ks-compare-strip__item-title {
  font: 600 0.8125rem / 1.3 var(--font-serif);
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ks-compare-strip__item-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 2px;
  background: none;
  color: var(--color-secondary);
  cursor: pointer;
  font-size: 1.125rem;
  line-height: 1;
  transition:
    background-color var(--duration-fast) var(--ease-smooth),
    color var(--duration-fast) var(--ease-smooth);
}

.ks-compare-strip__item-remove:hover {
  background: rgba(181, 74, 74, 0.08);
  color: #b54a4a;
}

.ks-compare-strip__item-remove:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-compare-strip__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* Transition */
.ks-strip-enter-active,
.ks-strip-leave-active {
  transition:
    transform var(--duration-normal) var(--ease-spring),
    opacity var(--duration-fast) var(--ease-smooth);
}
.ks-strip-enter-from,
.ks-strip-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

@media (max-width: 768px) {
  .ks-compare-strip {
    left: 16px;
    right: 16px;
    bottom: 16px;
    flex-direction: column;
    gap: 10px;
  }
  .ks-compare-strip__items {
    width: 100%;
  }
}
</style>
