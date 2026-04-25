<script setup lang="ts">
/**
 * PrecisionFilters — Collapsible filter panel for search refinement.
 *
 * Horizontal filter bar with Year range, Venue, Task Type, Code availability,
 * and Evidence Quality toggles. Expandable for advanced filters.
 */

export interface FilterOption {
  id: string;
  label: string;
  count: number;
  active: boolean;
}

export interface FilterGroup {
  id: string;
  title: string;
  options: FilterOption[];
}

export interface PrecisionFiltersProps {
  filters: FilterGroup[];
}

const props = defineProps<PrecisionFiltersProps>();

defineEmits<{
  "filter-toggle": [groupId: string, optionId: string, active: boolean];
  "clear-all": [];
}>();

const uid = useId();
const expanded = ref(false);

const activeCount = computed(() => {
  return props.filters.reduce(
    (sum, g) => sum + g.options.filter((o) => o.active).length,
    0,
  );
});
</script>

<template>
  <div
    class="ks-precision-filters ks-motion-paper-reveal"
    :aria-labelledby="`${uid}-title`"
  >
    <div class="ks-precision-filters__header">
      <h3 :id="`${uid}-title`" class="sr-only">Search Filters</h3>
      <button
        type="button"
        class="ks-precision-filters__toggle"
        :aria-expanded="expanded"
        @click="expanded = !expanded"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <line x1="4" y1="21" x2="4" y2="14" />
          <line x1="4" y1="10" x2="4" y2="3" />
          <line x1="12" y1="21" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12" y2="3" />
          <line x1="20" y1="21" x2="20" y2="16" />
          <line x1="20" y1="12" x2="20" y2="3" />
          <line x1="1" y1="14" x2="7" y2="14" />
          <line x1="9" y1="8" x2="15" y2="8" />
          <line x1="17" y1="16" x2="23" y2="16" />
        </svg>
        <span class="ks-type-eyebrow">Filters</span>
        <span v-if="activeCount > 0" class="ks-precision-filters__badge">{{
          activeCount
        }}</span>
      </button>
      <button
        v-if="activeCount > 0"
        type="button"
        class="ks-precision-filters__clear"
        @click="$emit('clear-all')"
      >
        Clear all
      </button>
    </div>
    <Transition name="ks-filters">
      <div v-if="expanded" class="ks-precision-filters__body">
        <div
          v-for="group in filters"
          :key="group.id"
          class="ks-precision-filters__group"
        >
          <h4 class="ks-precision-filters__group-title">{{ group.title }}</h4>
          <div
            class="ks-precision-filters__options"
            role="group"
            :aria-label="group.title"
          >
            <button
              v-for="opt in group.options"
              :key="opt.id"
              type="button"
              :class="[
                'ks-precision-filters__option',
                { 'ks-precision-filters__option--active': opt.active },
              ]"
              :aria-pressed="opt.active"
              @click="$emit('filter-toggle', group.id, opt.id, !opt.active)"
            >
              <span>{{ opt.label }}</span>
              <span class="ks-type-data">{{ opt.count }}</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
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

.ks-precision-filters {
  border-bottom: 1px solid var(--color-border);
  padding: 0 24px;
}

.ks-precision-filters__header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
}

.ks-precision-filters__toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  cursor: pointer;
  color: var(--color-text);
  transition: border-color var(--duration-fast) var(--ease-smooth);
}

.ks-precision-filters__toggle:hover {
  border-color: var(--color-primary);
}

.ks-precision-filters__toggle:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-precision-filters__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  background: var(--color-primary);
  color: white;
  border-radius: 9px;
  font: 600 0.625rem / 1 var(--font-sans);
}

.ks-precision-filters__clear {
  padding: 4px 8px;
  background: none;
  border: none;
  font: 500 0.75rem / 1 var(--font-sans);
  color: var(--color-primary);
  cursor: pointer;
}

.ks-precision-filters__clear:hover {
  text-decoration: underline;
}

.ks-precision-filters__body {
  display: flex;
  gap: 32px;
  padding: 16px 0 20px;
  border-top: 1px solid var(--color-border);
}

.ks-precision-filters__group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 140px;
}

.ks-precision-filters__group-title {
  font: 600 0.6875rem / 1.2 var(--font-sans);
  color: var(--color-text);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 2px;
}

.ks-precision-filters__options {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ks-precision-filters__option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 8px;
  background: none;
  border: none;
  border-radius: 2px;
  font: 400 0.875rem / 1.3 var(--font-serif);
  color: var(--color-text);
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-smooth);
}

.ks-precision-filters__option:hover {
  background: rgba(196, 163, 90, 0.06);
}

.ks-precision-filters__option--active {
  background: rgba(13, 115, 119, 0.08);
  color: var(--color-primary);
  font-weight: 600;
}

.ks-precision-filters__option:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}

/* Transition */
.ks-filters-enter-active,
.ks-filters-leave-active {
  transition:
    max-height var(--duration-normal) var(--ease-spring),
    opacity var(--duration-fast) var(--ease-smooth);
  overflow: hidden;
}
.ks-filters-enter-from,
.ks-filters-leave-to {
  max-height: 0;
  opacity: 0;
}
.ks-filters-enter-to,
.ks-filters-leave-from {
  max-height: 400px;
  opacity: 1;
}

@media (max-width: 768px) {
  .ks-precision-filters__body {
    flex-direction: column;
    gap: 16px;
  }
}
</style>
