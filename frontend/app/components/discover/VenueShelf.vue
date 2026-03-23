<script setup lang="ts">
/**
 * VenueShelf — Top venues sidebar panel.
 *
 * Shows a ranked list of venues with paper counts. The top venue
 * is highlighted with an accent border.
 */

export interface VenueItem {
  id: string
  name: string
  count: number
}

export interface VenueShelfProps {
  venues: VenueItem[]
}

defineProps<VenueShelfProps>()

defineEmits<{
  'venue-click': [venue: VenueItem]
}>()

const uid = useId()
</script>

<template>
  <section
    class="ks-venue-shelf ks-card ks-motion-paper-reveal ks-motion-paper-reveal--delay-2"
    :aria-labelledby="`${uid}-title`"
  >
    <h4 :id="`${uid}-title`" class="ks-type-section-title">Top Venues</h4>
    <ul class="ks-venue-shelf__list">
      <li
        v-for="(v, i) in venues"
        :key="v.id"
        class="ks-venue-shelf__li"
      >
        <button
          type="button"
          :class="['ks-venue-shelf__item', { 'ks-venue-shelf__item--hot': i === 0 }]"
          @click="$emit('venue-click', v)"
        >
          <span class="ks-venue-shelf__item-name">{{ v.name }}</span>
          <span class="ks-type-data" style="color: var(--color-primary);">
            {{ v.count }} papers
          </span>
        </button>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.ks-venue-shelf {
  padding: 20px;
}

.ks-venue-shelf__list {
  display: flex;
  flex-direction: column;
  margin-top: 12px;
  list-style: none;
  padding: 0;
}

.ks-venue-shelf__li {
  border-bottom: 1px solid var(--color-border);
}

.ks-venue-shelf__li:last-child {
  border-bottom: none;
}

.ks-venue-shelf__item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 10px 0;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: transform var(--duration-fast) var(--ease-spring);
}

.ks-venue-shelf__item:hover {
  transform: translateX(4px);
}

.ks-venue-shelf__item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-venue-shelf__item--hot {
  border-left: 2px solid var(--color-accent-decorative);
  padding-left: 10px;
}

.ks-venue-shelf__item-name {
  font: 600 0.9375rem / 1.3 var(--font-serif);
  color: var(--color-text);
}
</style>
