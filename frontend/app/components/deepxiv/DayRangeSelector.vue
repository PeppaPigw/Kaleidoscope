<script setup lang="ts">
/**
 * DayRangeSelector -- Toggle for selecting a day range (7, 14, or 30 days).
 *
 * Three buttons in a compact row. The active option is highlighted
 * with the primary color. Uses v-model pattern.
 */

export interface DayRangeSelectorProps {
  modelValue: number;
}

defineProps<DayRangeSelectorProps>();

defineEmits<{
  "update:modelValue": [value: number];
}>();

const options = [7, 14, 30] as const;
</script>

<template>
  <div class="ks-day-range" role="group" aria-label="Day range">
    <button
      v-for="days in options"
      :key="days"
      type="button"
      :class="[
        'ks-day-range__btn',
        { 'ks-day-range__btn--active': modelValue === days },
      ]"
      :aria-pressed="modelValue === days"
      @click="$emit('update:modelValue', days)"
    >
      {{ days }}d
    </button>
  </div>
</template>

<style scoped>
.ks-day-range {
  display: inline-flex;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  overflow: hidden;
}

.ks-day-range__btn {
  padding: 6px 14px;
  font: 600 0.8125rem / 1 var(--font-sans);
  color: var(--color-secondary);
  background: var(--color-surface);
  border: none;
  cursor: pointer;
  transition:
    background-color var(--duration-fast) var(--ease-smooth),
    color var(--duration-fast) var(--ease-smooth);
}

.ks-day-range__btn + .ks-day-range__btn {
  border-left: 1px solid var(--color-border);
}

.ks-day-range__btn:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.ks-day-range__btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}

.ks-day-range__btn--active {
  background: var(--color-primary);
  color: #fff;
}

.ks-day-range__btn--active:hover {
  background: var(--color-primary);
  color: #fff;
}
</style>
