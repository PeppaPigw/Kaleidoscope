<script setup lang="ts">
/**
 * SectionNav -- Table of contents for paper sections.
 *
 * Lists each section with its name, TLDR (truncated), and token count.
 * The currently active section is highlighted.
 */

export interface PaperSection {
  name: string
  idx: number
  tldr: string
  token_count: number
}

export interface SectionNavProps {
  sections: PaperSection[]
  activeSection: string | null
}

defineProps<SectionNavProps>()

defineEmits<{
  select: [sectionName: string]
}>()
</script>

<template>
  <nav class="ks-section-nav" aria-label="Paper sections">
    <ul class="ks-section-nav__list">
      <li
        v-for="section in sections"
        :key="section.idx"
        class="ks-section-nav__item"
      >
        <button
          type="button"
          :class="[
            'ks-section-nav__btn',
            { 'ks-section-nav__btn--active': activeSection === section.name },
          ]"
          :aria-current="activeSection === section.name ? 'true' : undefined"
          @click="$emit('select', section.name)"
        >
          <div class="ks-section-nav__row">
            <span class="ks-section-nav__name">{{ section.name }}</span>
            <span class="ks-section-nav__tokens">{{ section.token_count.toLocaleString() }}</span>
          </div>
          <p v-if="section.tldr" class="ks-section-nav__tldr">{{ section.tldr }}</p>
        </button>
      </li>
    </ul>
  </nav>
</template>

<style scoped>
.ks-section-nav {
  display: flex;
  flex-direction: column;
}

.ks-section-nav__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ks-section-nav__btn {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
  padding: 10px 12px;
  background: none;
  border: none;
  border-left: 3px solid transparent;
  border-radius: 0 4px 4px 0;
  cursor: pointer;
  text-align: left;
  transition: background-color var(--duration-fast) var(--ease-smooth),
              border-color var(--duration-fast) var(--ease-smooth);
}

.ks-section-nav__btn:hover {
  background: var(--color-primary-light);
}

.ks-section-nav__btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}

.ks-section-nav__btn--active {
  border-left-color: var(--color-primary);
  background: var(--color-primary-light);
}

.ks-section-nav__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.ks-section-nav__name {
  font: 600 0.8125rem / 1.3 var(--font-sans);
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.ks-section-nav__btn--active .ks-section-nav__name {
  color: var(--color-primary);
}

.ks-section-nav__tokens {
  flex-shrink: 0;
  padding: 1px 6px;
  font: 500 0.625rem / 1.4 var(--font-mono);
  color: var(--color-secondary);
  background: var(--color-bg);
  border-radius: 3px;
}

.ks-section-nav__tldr {
  font: 400 0.75rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
