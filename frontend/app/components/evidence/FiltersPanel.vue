<script setup lang="ts">
/**
 * FiltersPanel — dataset/metric toggles plus method search for Evidence Lab.
 */
import { Filter, Search, X } from "lucide-vue-next";

export interface EvidenceFilterOption {
  id: string;
  label: string;
  count: number;
}

export interface FiltersPanelProps {
  datasets: EvidenceFilterOption[];
  metrics: EvidenceFilterOption[];
  activeDatasets: string[];
  activeMetrics: string[];
  methodQuery: string;
  visibleCount: number;
  totalCount: number;
}

const props = defineProps<FiltersPanelProps>();

const emit = defineEmits<{
  "update:datasets": [value: string[]];
  "update:metrics": [value: string[]];
  "update:methodQuery": [value: string];
  clear: [];
}>();

const uid = useId();
const localMethodQuery = ref(props.methodQuery);

watch(
  () => props.methodQuery,
  (value) => {
    localMethodQuery.value = value;
  },
);

const activeCount = computed(() => {
  let count = props.activeDatasets.length + props.activeMetrics.length;
  if (props.methodQuery.trim()) count += 1;
  return count;
});

function toggleValue(current: string[], nextValue: string): string[] {
  return current.includes(nextValue)
    ? current.filter((value) => value !== nextValue)
    : [...current, nextValue];
}

function toggleDataset(nextValue: string) {
  const next = toggleValue(props.activeDatasets, nextValue);
  emit("update:datasets", next);
}

function toggleMetric(nextValue: string) {
  const next = toggleValue(props.activeMetrics, nextValue);
  emit("update:metrics", next);
}

function emitMethodQuery() {
  emit("update:methodQuery", localMethodQuery.value.trim());
}
</script>

<template>
  <section
    class="ks-evidence-filters ks-motion-paper-reveal"
    :aria-labelledby="`${uid}-title`"
  >
    <div class="ks-evidence-filters__header">
      <div class="ks-evidence-filters__title-wrap">
        <div class="ks-evidence-filters__icon">
          <Filter :size="15" />
        </div>
        <div>
          <h2 :id="`${uid}-title`" class="ks-type-section-title">
            Results Filters
          </h2>
          <p class="ks-evidence-filters__subtitle">
            Showing {{ visibleCount }} of {{ totalCount }} method rows
          </p>
        </div>
      </div>

      <div class="ks-evidence-filters__actions">
        <span v-if="activeCount" class="ks-evidence-filters__badge">
          {{ activeCount }} active
        </span>
        <KsButton
          v-if="activeCount"
          variant="ghost"
          size="sm"
          @click="$emit('clear')"
        >
          Clear all
        </KsButton>
      </div>
    </div>

    <div class="ks-evidence-filters__search">
      <label :for="`${uid}-method-search`" class="sr-only">Method search</label>
      <div class="ks-evidence-filters__search-input-wrap">
        <Search :size="14" class="ks-evidence-filters__search-icon" />
        <input
          :id="`${uid}-method-search`"
          v-model="localMethodQuery"
          type="search"
          class="ks-evidence-filters__search-input"
          placeholder="Search methods…"
          @input="emitMethodQuery"
        />
        <button
          v-if="localMethodQuery"
          type="button"
          class="ks-evidence-filters__search-clear"
          aria-label="Clear method search"
          @click="
            localMethodQuery = '';
            emitMethodQuery();
          "
        >
          <X :size="14" />
        </button>
      </div>
    </div>

    <div class="ks-evidence-filters__groups">
      <div class="ks-evidence-filters__group">
        <h3 class="ks-evidence-filters__group-title">Datasets</h3>
        <div class="ks-evidence-filters__chips">
          <button
            v-for="dataset in datasets"
            :key="dataset.id"
            type="button"
            :class="[
              'ks-evidence-filters__chip',
              {
                'ks-evidence-filters__chip--active': activeDatasets.includes(
                  dataset.id,
                ),
              },
            ]"
            :aria-pressed="activeDatasets.includes(dataset.id)"
            @click="toggleDataset(dataset.id)"
          >
            <span>{{ dataset.label }}</span>
            <span class="ks-type-data">{{ dataset.count }}</span>
          </button>
          <p v-if="datasets.length === 0" class="ks-evidence-filters__empty">
            No datasets detected for the current scope.
          </p>
        </div>
      </div>

      <div class="ks-evidence-filters__group">
        <h3 class="ks-evidence-filters__group-title">Metrics</h3>
        <div class="ks-evidence-filters__chips">
          <button
            v-for="metric in metrics"
            :key="metric.id"
            type="button"
            :class="[
              'ks-evidence-filters__chip',
              {
                'ks-evidence-filters__chip--active': activeMetrics.includes(
                  metric.id,
                ),
              },
            ]"
            :aria-pressed="activeMetrics.includes(metric.id)"
            @click="toggleMetric(metric.id)"
          >
            <span>{{ metric.label }}</span>
            <span class="ks-type-data">{{ metric.count }}</span>
          </button>
          <p v-if="metrics.length === 0" class="ks-evidence-filters__empty">
            No metrics detected for the current scope.
          </p>
        </div>
      </div>
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

.ks-evidence-filters {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: 18px 20px 20px;
  background: var(--color-surface);
}

.ks-evidence-filters__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.ks-evidence-filters__title-wrap {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.ks-evidence-filters__icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: rgba(13, 115, 119, 0.1);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ks-evidence-filters__subtitle {
  margin-top: 4px;
  color: var(--color-secondary);
  font: 400 0.8125rem / 1.5 var(--font-serif);
}

.ks-evidence-filters__actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ks-evidence-filters__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  background: rgba(196, 163, 90, 0.12);
  color: var(--color-accent);
  font: 600 0.6875rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.ks-evidence-filters__search {
  margin-top: 18px;
}

.ks-evidence-filters__search-input-wrap {
  position: relative;
}

.ks-evidence-filters__search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-secondary);
}

.ks-evidence-filters__search-input {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  color: var(--color-text);
  padding: 10px 38px 10px 36px;
  font: 400 0.875rem / 1.4 var(--font-serif);
}

.ks-evidence-filters__search-input:focus {
  outline: 2px solid rgba(13, 115, 119, 0.14);
  border-color: var(--color-primary);
}

.ks-evidence-filters__search-clear {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  border: none;
  background: none;
  color: var(--color-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ks-evidence-filters__groups {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 18px;
}

.ks-evidence-filters__group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ks-evidence-filters__group-title {
  font: 600 0.7rem / 1.2 var(--font-sans);
  color: var(--color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.ks-evidence-filters__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ks-evidence-filters__chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: none;
  padding: 7px 12px;
  color: var(--color-text);
  cursor: pointer;
  font: 400 0.8125rem / 1.2 var(--font-serif);
  transition:
    border-color var(--duration-fast) var(--ease-smooth),
    background-color var(--duration-fast) var(--ease-smooth),
    color var(--duration-fast) var(--ease-smooth);
}

.ks-evidence-filters__chip:hover {
  border-color: var(--color-primary);
}

.ks-evidence-filters__chip--active {
  background: rgba(13, 115, 119, 0.08);
  border-color: rgba(13, 115, 119, 0.3);
  color: var(--color-primary);
}

.ks-evidence-filters__empty {
  color: var(--color-secondary);
  font: 400 0.8125rem / 1.5 var(--font-serif);
}

@media (max-width: 768px) {
  .ks-evidence-filters__groups {
    grid-template-columns: 1fr;
  }

  .ks-evidence-filters__header {
    flex-direction: column;
  }

  .ks-evidence-filters__actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
