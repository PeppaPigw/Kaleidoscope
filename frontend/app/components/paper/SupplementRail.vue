<script setup lang="ts">
/**
 * SupplementRail — Sidebar with supplementary materials.
 *
 * Lists linked code repos, datasets, slides, appendices,
 * and external resources for the paper.
 */

export interface SupplementItem {
  id: string
  label: string
  type: 'code' | 'dataset' | 'slides' | 'appendix' | 'video' | 'demo'
  url: string
}

export interface SupplementRailProps {
  items: SupplementItem[]
}

defineProps<SupplementRailProps>()
const uid = useId()

function typeIcon(t: SupplementItem['type']): string {
  const map: Record<SupplementItem['type'], string> = {
    code: '⌨',
    dataset: '📊',
    slides: '📑',
    appendix: '📎',
    video: '🎬',
    demo: '🚀',
  }
  return map[t]
}
</script>

<template>
  <aside class="ks-supplement-rail ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <h3 :id="`${uid}-title`" class="ks-type-eyebrow" style="color: var(--color-accent); margin-bottom: 12px;">
      Supplementary Materials
    </h3>
    <ul class="ks-supplement-rail__list">
      <li v-for="item in items" :key="item.id">
        <a :href="item.url" target="_blank" rel="noopener" class="ks-supplement-rail__link">
          <span class="ks-supplement-rail__icon" aria-hidden="true">{{ typeIcon(item.type) }}</span>
          <span class="ks-supplement-rail__label">{{ item.label }}</span>
          <KsTag variant="neutral" style="font-size: 0.625rem;">{{ item.type }}</KsTag>
        </a>
      </li>
    </ul>
  </aside>
</template>

<style scoped>
.ks-supplement-rail {
  padding: 20px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
}

.ks-supplement-rail__list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ks-supplement-rail__link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  text-decoration: none;
  border-radius: 2px;
  transition: background-color var(--duration-fast) var(--ease-smooth);
}

.ks-supplement-rail__link:hover {
  background: rgba(13, 115, 119, 0.04);
}

.ks-supplement-rail__link:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}

.ks-supplement-rail__icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.ks-supplement-rail__label {
  flex: 1;
  font: 500 0.875rem / 1.3 var(--font-sans);
  color: var(--color-text);
}
</style>
