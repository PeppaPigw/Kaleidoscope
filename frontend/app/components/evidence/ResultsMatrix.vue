<script setup lang="ts">
/**
 * ResultsMatrix — Structured results comparison table.
 */

export interface MatrixResult {
  id: string;
  method: string;
  metrics: Record<string, string | number>;
  isBest: boolean;
  source: string;
}

export interface ResultsMatrixProps {
  results: MatrixResult[];
  metricNames: string[];
  title?: string;
}

defineProps<ResultsMatrixProps>();

const uid = useId();
</script>

<template>
  <section
    class="ks-results-matrix ks-motion-paper-reveal"
    :aria-labelledby="`${uid}-title`"
  >
    <h2 :id="`${uid}-title`" class="ks-type-section-title">
      {{ title || "Results Comparison" }}
    </h2>

    <div class="ks-results-matrix__wrapper">
      <table class="ks-results-matrix__table">
        <thead>
          <tr>
            <th class="ks-results-matrix__th">Method</th>
            <th
              v-for="metric in metricNames"
              :key="metric"
              class="ks-results-matrix__th ks-results-matrix__th--metric"
            >
              {{ metric }}
            </th>
            <th class="ks-results-matrix__th">Source</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in results"
            :key="r.id"
            :class="{ 'ks-results-matrix__row--best': r.isBest }"
          >
            <td class="ks-results-matrix__td ks-results-matrix__td--method">
              {{ r.method }}
              <KsTag v-if="r.isBest" variant="success">best</KsTag>
            </td>
            <td
              v-for="metric in metricNames"
              :key="metric"
              class="ks-results-matrix__td ks-results-matrix__td--value"
            >
              {{ r.metrics[metric] ?? "—" }}
            </td>
            <td class="ks-results-matrix__td ks-type-data">{{ r.source }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.ks-results-matrix__wrapper {
  overflow-x: auto;
  margin-top: 16px;
}

.ks-results-matrix__table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-mono);
  font-size: 0.8125rem;
}

.ks-results-matrix__th {
  text-align: left;
  padding: 10px 12px;
  font: 600 0.75rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-secondary);
  border-bottom: 2px solid var(--color-border);
}

.ks-results-matrix__th--metric {
  text-align: right;
}

.ks-results-matrix__td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text);
}

.ks-results-matrix__td--method {
  font: 500 0.875rem / 1.3 var(--font-serif);
  display: flex;
  align-items: center;
  gap: 8px;
}

.ks-results-matrix__td--value {
  text-align: right;
  font: 500 0.875rem / 1 var(--font-mono);
}

.ks-results-matrix__row--best {
  background: rgba(13, 115, 119, 0.03);
}
</style>
