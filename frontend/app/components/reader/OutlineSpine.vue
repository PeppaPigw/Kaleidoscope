<script setup lang="ts">
/**
 * OutlineSpine — Document outline sidebar.
 */

export interface OutlineSection {
  id: string
  title: string
  level: number
  page: number
}

export interface OutlineSpineProps {
  sections: OutlineSection[]
  activeSectionId?: string
}

defineProps<OutlineSpineProps>()
defineEmits<{ 'section-click': [section: OutlineSection] }>()

const uid = useId()
</script>

<template>
  <nav class="ks-outline-spine ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <h3 :id="`${uid}-title`" class="ks-type-eyebrow" style="color: var(--color-accent); margin-bottom: 12px;">Contents</h3>
    <ol class="ks-outline-spine__list">
      <li
        v-for="section in sections"
        :key="section.id"
        :style="{ paddingLeft: `${(section.level - 1) * 16}px` }"
      >
        <button
          type="button"
          :class="['ks-outline-spine__item', { 'ks-outline-spine__item--active': section.id === activeSectionId }]"
          @click="$emit('section-click', section)"
        >
          <span class="ks-outline-spine__title">{{ section.title }}</span>
          <span class="ks-type-data">p.{{ section.page }}</span>
        </button>
      </li>
    </ol>
  </nav>
</template>

<style scoped>
.ks-outline-spine__list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.ks-outline-spine__item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 10px;
  border: none;
  background: none;
  border-radius: 2px;
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-smooth);
  text-align: left;
}

.ks-outline-spine__item:hover {
  background: rgba(13, 115, 119, 0.04);
}

.ks-outline-spine__item--active {
  background: rgba(13, 115, 119, 0.08);
  border-left: 2px solid var(--color-primary);
}

.ks-outline-spine__item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-outline-spine__title {
  font: 500 0.875rem / 1.4 var(--font-serif);
  color: var(--color-text);
}
</style>
