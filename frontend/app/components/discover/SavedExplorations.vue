<script setup lang="ts">
/**
 * SavedExplorations — List of previously saved discovery queries.
 *
 * Displays saved research exploration queries with dates. Pinned items
 * are visually highlighted. Each item has a hover-revealed "Reopen" button.
 */

export interface SavedExploration {
  id: string
  title: string
  date: string
  pinned: boolean
}

export interface SavedExplorationsProps {
  explorations: SavedExploration[]
}

defineProps<SavedExplorationsProps>()

defineEmits<{
  'reopen': [exploration: SavedExploration]
}>()

const uid = useId()
</script>

<template>
  <section
    class="ks-saved-explorations ks-card ks-motion-paper-reveal ks-motion-paper-reveal--delay-4"
    :aria-labelledby="`${uid}-title`"
  >
    <h4 :id="`${uid}-title`" class="ks-type-section-title">Saved Explorations</h4>
    <ul class="ks-saved-explorations__list">
      <li
        v-for="item in explorations"
        :key="item.id"
        :class="[
          'ks-saved-explorations__item',
          { 'ks-saved-explorations__item--pinned': item.pinned },
        ]"
      >
        <div class="ks-saved-explorations__item-info">
          <span class="ks-saved-explorations__item-title">{{ item.title }}</span>
          <span class="ks-type-data">{{ item.date }}</span>
        </div>
        <button
          type="button"
          class="ks-saved-explorations__reopen"
          :tabindex="-1"
          :aria-label="`Reopen ${item.title}`"
          @click="$emit('reopen', item)"
        >
          Reopen
        </button>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.ks-saved-explorations {
  padding: 20px;
}

.ks-saved-explorations__list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 12px;
  list-style: none;
  padding: 0;
}

.ks-saved-explorations__item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 2px;
  transition: background-color var(--duration-fast) var(--ease-smooth);
}

.ks-saved-explorations__item:hover {
  background: rgba(250, 250, 247, 0.86);
}

.ks-saved-explorations__item--pinned {
  border-left: 2px solid var(--color-primary);
  padding-left: 10px;
}

.ks-saved-explorations__item-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ks-saved-explorations__item-title {
  font: 600 0.9375rem / 1.3 var(--font-serif);
  color: var(--color-text);
}

.ks-saved-explorations__reopen {
  opacity: 0;
  padding: 4px 8px;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 2px;
  font: 500 0.6875rem / 1 var(--font-sans);
  color: var(--color-primary);
  cursor: pointer;
  transition: opacity var(--duration-fast) var(--ease-smooth);
}

.ks-saved-explorations__item:hover .ks-saved-explorations__reopen,
.ks-saved-explorations__reopen:focus {
  opacity: 1;
}

.ks-saved-explorations__reopen:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  opacity: 1;
}
</style>
