<script setup lang="ts">
/**
 * ResearchPulseCloud — keyword word cloud visualization.
 * Renders weighted keyword tokens sized by frequency.
 */

const props = defineProps<{
  words: Array<{ text: string; weight: number }>
}>()

const emit = defineEmits<{ click: [word: string] }>()

const COLORS = [
  'var(--color-primary)',
  'rgba(13, 115, 119, 0.7)',
  'rgba(13, 115, 119, 0.5)',
  'var(--color-secondary)',
  'rgba(26, 26, 26, 0.4)',
]

const MAX_SIZE = 32
const MIN_SIZE = 13

function getSize(weight: number, maxWeight: number): number {
  if (maxWeight === 0) return MIN_SIZE
  const ratio = weight / maxWeight
  return Math.round(MIN_SIZE + ratio * (MAX_SIZE - MIN_SIZE))
}

function getColor(index: number, weight: number, maxWeight: number): string {
  const ratio = weight / maxWeight
  if (ratio > 0.7) return COLORS[0]!
  if (ratio > 0.4) return COLORS[1]!
  if (ratio > 0.2) return COLORS[2]!
  if (ratio > 0.1) return COLORS[3]!
  return COLORS[4]!
}

const maxWeight = computed(() => Math.max(...props.words.map(w => w.weight), 1))

const displayWords = computed(() =>
  [...props.words].sort((a, b) => b.weight - a.weight).slice(0, 40)
)
</script>

<template>
  <div class="ks-cloud">
    <div class="ks-cloud__words">
      <button
        v-for="(word, i) in displayWords"
        :key="word.text"
        type="button"
        class="ks-cloud__word"
        :style="{
          fontSize: `${getSize(word.weight, maxWeight)}px`,
          color: getColor(i, word.weight, maxWeight),
          opacity: 0.4 + (word.weight / maxWeight) * 0.6,
        }"
        @click="emit('click', word.text)"
      >
        {{ word.text }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.ks-cloud {
  width: 100%;
  height: 100%;
  min-height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ks-cloud__words {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  justify-content: center;
  align-items: center;
  padding: 8px;
}

.ks-cloud__word {
  background: none;
  border: none;
  font: 600 1rem / 1 var(--font-display);
  letter-spacing: -0.01em;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.15s;
  padding: 2px 4px;
  border-radius: 3px;
}

.ks-cloud__word:hover {
  opacity: 1 !important;
  transform: scale(1.08);
}
</style>
