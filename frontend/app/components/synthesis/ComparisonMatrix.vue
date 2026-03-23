<script setup lang="ts">
/**
 * ComparisonMatrix — Cross-paper feature comparison table.
 */

export interface ComparisonPaper {
  id: string
  title: string
  shortName: string
}

export interface ComparisonFeature {
  id: string
  name: string
  category: string
  values: Record<string, boolean | string>
}

export interface ComparisonMatrixProps {
  papers: ComparisonPaper[]
  features: ComparisonFeature[]
}

defineProps<ComparisonMatrixProps>()

const uid = useId()
</script>

<template>
  <section class="ks-comparison-matrix ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <h2 :id="`${uid}-title`" class="ks-type-section-title">Cross-Paper Comparison</h2>

    <div class="ks-comparison-matrix__wrapper">
      <table class="ks-comparison-matrix__table">
        <thead>
          <tr>
            <th class="ks-comparison-matrix__th">Feature</th>
            <th v-for="p in papers" :key="p.id" class="ks-comparison-matrix__th ks-comparison-matrix__th--paper">
              {{ p.shortName }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="f in features" :key="f.id">
            <td class="ks-comparison-matrix__td ks-comparison-matrix__td--feature">
              <span>{{ f.name }}</span>
              <span class="ks-type-data" style="color: var(--color-secondary);">{{ f.category }}</span>
            </td>
            <td v-for="p in papers" :key="p.id" class="ks-comparison-matrix__td ks-comparison-matrix__td--value">
              <span v-if="typeof f.values[p.id] === 'boolean'" :style="{ color: f.values[p.id] ? 'var(--color-primary)' : '#B54A4A' }">
                {{ f.values[p.id] ? '✓' : '✗' }}
              </span>
              <span v-else class="ks-type-data">{{ f.values[p.id] || '—' }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.ks-comparison-matrix__wrapper {
  overflow-x: auto;
  margin-top: 16px;
}

.ks-comparison-matrix__table {
  width: 100%;
  border-collapse: collapse;
}

.ks-comparison-matrix__th {
  text-align: left;
  padding: 10px 12px;
  font: 600 0.75rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-secondary);
  border-bottom: 2px solid var(--color-border);
}

.ks-comparison-matrix__th--paper {
  text-align: center;
  min-width: 100px;
}

.ks-comparison-matrix__td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border);
}

.ks-comparison-matrix__td--feature {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font: 500 0.875rem / 1.4 var(--font-serif);
  color: var(--color-text);
}

.ks-comparison-matrix__td--value {
  text-align: center;
  font: 700 1rem / 1 var(--font-mono);
}
</style>
