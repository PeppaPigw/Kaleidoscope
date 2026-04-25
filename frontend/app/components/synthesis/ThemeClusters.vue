<script setup lang="ts">
/**
 * ThemeClusters — Visual topic clusters from synthesized papers.
 */

export interface ThemeCluster {
  id: string;
  name: string;
  paperCount: number;
  color: string;
  keywords: string[];
}

export interface ThemeClustersProps {
  clusters: ThemeCluster[];
}

defineProps<ThemeClustersProps>();
defineEmits<{ "cluster-click": [cluster: ThemeCluster] }>();

const uid = useId();
</script>

<template>
  <section
    class="ks-theme-clusters ks-motion-paper-reveal"
    :aria-labelledby="`${uid}-title`"
  >
    <h2 :id="`${uid}-title`" class="ks-type-section-title">Theme Clusters</h2>

    <div class="ks-theme-clusters__grid">
      <button
        v-for="c in clusters"
        :key="c.id"
        type="button"
        class="ks-card ks-theme-clusters__card"
        :style="{ borderLeftColor: c.color }"
        @click="$emit('cluster-click', c)"
      >
        <div class="ks-theme-clusters__header">
          <span class="ks-theme-clusters__name">{{ c.name }}</span>
          <span
            class="ks-type-data"
            style="font-weight: 700"
            :style="{ color: c.color }"
            >{{ c.paperCount }}</span
          >
        </div>
        <div class="ks-theme-clusters__keywords">
          <KsTag
            v-for="kw in c.keywords.slice(0, 4)"
            :key="kw"
            variant="neutral"
            >{{ kw }}</KsTag
          >
        </div>
      </button>
    </div>
  </section>
</template>

<style scoped>
.ks-theme-clusters__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 10px;
  margin-top: 16px;
}

.ks-theme-clusters__card {
  padding: 16px;
  text-align: left;
  cursor: pointer;
  border-left: 3px solid var(--color-border);
  transition:
    transform var(--duration-normal) var(--ease-spring),
    box-shadow var(--duration-normal) var(--ease-smooth);
}

.ks-theme-clusters__card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(26, 26, 26, 0.06);
}

.ks-theme-clusters__card:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-theme-clusters__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.ks-theme-clusters__name {
  font: 600 1rem / 1.3 var(--font-serif);
  color: var(--color-text);
}

.ks-theme-clusters__keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>
