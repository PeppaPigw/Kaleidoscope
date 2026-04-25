<script setup lang="ts">
import type { RenderedMarkdownHeading } from "~/utils/markdown";

export interface WritingOutlinePaneProps {
  sections: RenderedMarkdownHeading[];
  activeSectionId?: string | null;
}

defineProps<WritingOutlinePaneProps>();
defineEmits<{ "section-click": [section: RenderedMarkdownHeading] }>();
</script>

<template>
  <section class="ks-writing-outline" data-testid="writing-outline">
    <div v-if="sections.length === 0" class="ks-writing-outline__empty">
      Add headings in the editor to build a live outline.
    </div>

    <ol v-else class="ks-writing-outline__list">
      <li
        v-for="section in sections"
        :key="section.id"
        :style="{
          '--ks-outline-level': String(Math.max(section.level - 1, 0)),
        }"
      >
        <button
          type="button"
          class="ks-writing-outline__item"
          :class="{ 'is-active': section.id === activeSectionId }"
          @click="$emit('section-click', section)"
        >
          <span class="ks-writing-outline__title">{{ section.title }}</span>
        </button>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.ks-writing-outline {
  min-height: 0;
  height: 100%;
  overflow: auto;
  padding-right: 0.2rem;
}

.ks-writing-outline__empty {
  display: grid;
  place-items: center;
  min-height: 12rem;
  padding: 1rem;
  border: 1px dashed rgba(13, 115, 119, 0.18);
  border-radius: 1rem;
  color: var(--color-secondary);
  text-align: center;
  font: 500 0.9rem / 1.55 var(--font-serif);
}

.ks-writing-outline__list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.ks-writing-outline__item {
  width: 100%;
  margin: 0;
  padding: 0.72rem 0.85rem 0.72rem
    calc(0.85rem + var(--ks-outline-level) * 0.9rem);
  border: 0;
  border-left: 2px solid transparent;
  border-radius: 0.9rem;
  background: transparent;
  color: inherit;
  cursor: pointer;
  text-align: left;
  transition:
    background-color var(--duration-fast) var(--ease-smooth),
    border-color var(--duration-fast) var(--ease-smooth),
    transform var(--duration-fast) var(--ease-smooth);
}

.ks-writing-outline__item:hover {
  background: rgba(13, 115, 119, 0.05);
  transform: translateX(1px);
}

.ks-writing-outline__item.is-active {
  border-left-color: var(--color-primary);
  background: rgba(13, 115, 119, 0.1);
}

.ks-writing-outline__title {
  display: block;
  color: var(--color-text);
  font: 600 0.9rem / 1.45 var(--font-serif);
}
</style>
