<script setup lang="ts">
/**
 * FacetWall — Sticky sidebar with filterable facet groups.
 *
 * Displays categorized facet options (Year, Task, Venue, Code) with
 * toggle buttons and counts. Supports toggling active state and emitting
 * filter changes.
 */

export interface FacetOption {
  label: string;
  count: number;
  active: boolean;
}

export interface FacetGroup {
  title: string;
  options: FacetOption[];
}

export interface FacetWallProps {
  groups: FacetGroup[];
}

defineProps<FacetWallProps>();

defineEmits<{
  "facet-toggle": [group: string, option: string, active: boolean];
}>();

const uid = useId();
</script>

<template>
  <aside
    class="ks-facet-wall ks-motion-paper-reveal ks-motion-paper-reveal--delay-2"
    :aria-labelledby="`${uid}-title`"
  >
    <h3 :id="`${uid}-title`" class="sr-only">Filter Facets</h3>
    <div
      v-for="group in groups"
      :key="group.title"
      class="ks-facet-wall__group"
    >
      <h4 class="ks-facet-wall__group-title">{{ group.title }}</h4>
      <div
        class="ks-facet-wall__options"
        role="group"
        :aria-label="group.title"
      >
        <button
          v-for="opt in group.options"
          :key="opt.label"
          type="button"
          :class="[
            'ks-facet-wall__option',
            { 'ks-facet-wall__option--active': opt.active },
          ]"
          :aria-pressed="opt.active"
          @click="$emit('facet-toggle', group.title, opt.label, !opt.active)"
        >
          <span class="ks-facet-wall__option-label">{{ opt.label }}</span>
          <span class="ks-facet-wall__option-count ks-type-data">{{ opt.count }}</span>
        </button>
      </div>
    </div>
  </aside>
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

.ks-facet-wall {
  position: sticky;
  top: 104px;
  max-height: calc(100dvh - 128px);
  overflow-y: auto;
  padding: 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  align-self: start;
  scrollbar-width: thin;
}

.ks-facet-wall__group {
  padding-bottom: 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

.ks-facet-wall__group:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.ks-facet-wall__group-title {
  font: 600 0.8125rem / 1.2 var(--font-sans);
  color: var(--color-text);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 10px;
}

.ks-facet-wall__options {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ks-facet-wall__option {
  display: flex;
  justify-content: flex-start;
  align-items: flex-start;
  gap: 8px;
  width: 100%;
  padding: 7px 10px;
  background: none;
  border: none;
  border-radius: 2px;
  font: 400 0.9375rem / 1.4 var(--font-serif);
  color: var(--color-text);
  text-align: left;
  cursor: pointer;
  transition:
    background-color var(--duration-fast) var(--ease-smooth),
    color var(--duration-fast) var(--ease-smooth);
}

.ks-facet-wall__option-label,
.ks-facet-wall__option-count {
  text-align: left;
}

.ks-facet-wall__option:hover {
  background: rgba(196, 163, 90, 0.06);
}

.ks-facet-wall__option--active {
  background: rgba(13, 115, 119, 0.08);
  color: var(--color-primary);
  font-weight: 600;
}

.ks-facet-wall__option:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}

@media (max-width: 768px) {
  .ks-facet-wall {
    position: static;
    max-height: none;
  }
}
</style>
