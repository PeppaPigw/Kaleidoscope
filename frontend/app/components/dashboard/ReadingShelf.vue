<script setup lang="ts">
/**
 * ReadingShelf — Recommended reading cards with tabbed categories.
 *
 * Displays paper recommendations in a 3-column grid with gold-top accent cards.
 * Supports "For You", "Trending", and "Controversial" tabs.
 * Uses proper ARIA tab pattern with keyboard arrow-key switching.
 * Cards use `role="link"` with Space + Enter handling for screen readers.
 */

export interface ReadingPick {
  id: string
  eyebrow: string
  title: string
  venue: string
  tags: string[]
  abstract: string
  /** Optional tab category to filter by */
  category?: 'for-you' | 'trending' | 'controversial'
}

export interface ReadingShelfProps {
  picks: ReadingPick[]
}

const props = defineProps<ReadingShelfProps>()

const emit = defineEmits<{
  'card-click': [pick: ReadingPick]
  'tab-change': [tab: ShelfTab]
}>()

type ShelfTab = 'for-you' | 'trending' | 'controversial'

const activeTab = ref<ShelfTab>('for-you')

const tabs: { key: ShelfTab; label: string }[] = [
  { key: 'for-you', label: 'For You' },
  { key: 'trending', label: 'Trending' },
  { key: 'controversial', label: 'Controversial' },
]

// ─── Generate unique IDs for ARIA ──────────────────────────
const uid = useId()
const tabId = (key: ShelfTab) => `${uid}-tab-${key}`
const panelId = (key: ShelfTab) => `${uid}-panel-${key}`

// ─── Filter picks by active tab ────────────────────────────
const filteredPicks = computed(() => {
  // If no picks have a category, show all picks for any tab (mock-data friendly)
  const hasCategories = props.picks.some(p => p.category)
  if (!hasCategories) return props.picks

  return props.picks.filter(p => p.category === activeTab.value)
})

// ─── Tab keyboard navigation (Arrow Left/Right) ───────────
function handleTabKeydown(e: KeyboardEvent, idx: number) {
  let newIdx: number | null = null

  if (e.key === 'ArrowRight') {
    newIdx = (idx + 1) % tabs.length
  } else if (e.key === 'ArrowLeft') {
    newIdx = (idx - 1 + tabs.length) % tabs.length
  } else if (e.key === 'Home') {
    newIdx = 0
  } else if (e.key === 'End') {
    newIdx = tabs.length - 1
  }

  if (newIdx !== null) {
    e.preventDefault()
    activeTab.value = tabs[newIdx]!.key
    emit('tab-change', tabs[newIdx]!.key)
    // Move focus to the new tab
    const el = document.getElementById(tabId(tabs[newIdx]!.key))
    el?.focus()
  }
}

function selectTab(tab: ShelfTab) {
  activeTab.value = tab
  emit('tab-change', tab)
}

function handleCardAction(pick: ReadingPick) {
  emit('card-click', pick)
}
</script>

<template>
  <section class="ks-reading-shelf" :aria-labelledby="`${uid}-title`">
    <div class="ks-reading-shelf__header">
      <h3 :id="`${uid}-title`" class="ks-type-section-title">Recommended Reading</h3>
      <div class="ks-reading-shelf__tabs" role="tablist" aria-label="Reading categories">
        <button
          v-for="(tab, idx) in tabs"
          :key="tab.key"
          :id="tabId(tab.key)"
          role="tab"
          :aria-selected="activeTab === tab.key"
          :aria-controls="panelId(tab.key)"
          :tabindex="activeTab === tab.key ? 0 : -1"
          :class="[
            'ks-reading-shelf__tab',
            { 'ks-reading-shelf__tab--active': activeTab === tab.key },
          ]"
          @click="selectTab(tab.key)"
          @keydown="handleTabKeydown($event, idx)"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>
    <div
      :id="panelId(activeTab)"
      class="ks-reading-shelf__cards"
      role="tabpanel"
      :aria-labelledby="tabId(activeTab)"
    >
      <a
        v-for="(pick, i) in filteredPicks"
        :key="pick.id"
        :href="`/papers/${pick.id}`"
        :class="[
          'ks-card ks-card--gold-top ks-reading-shelf__card',
          'ks-motion-paper-reveal',
          `ks-motion-paper-reveal--delay-${i + 1}`,
        ]"
        @click.prevent="handleCardAction(pick)"
      >
        <span class="ks-type-eyebrow ks-reading-shelf__card-eyebrow">
          {{ pick.eyebrow }}
        </span>
        <h4 class="ks-reading-shelf__card-title">{{ pick.title }}</h4>
        <p class="ks-type-body-sm ks-reading-shelf__card-abstract">
          {{ pick.abstract }}
        </p>
        <div class="ks-reading-shelf__card-meta">
          <span class="ks-type-data">{{ pick.venue }}</span>
          <KsTag
            v-for="tag in pick.tags"
            :key="tag"
            variant="primary"
          >
            {{ tag }}
          </KsTag>
        </div>
      </a>
    </div>
  </section>
</template>

<style scoped>
.ks-reading-shelf__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.ks-reading-shelf__tabs {
  display: flex;
  gap: 4px;
}

.ks-reading-shelf__tab {
  padding: 6px 12px;
  background: none;
  border: none;
  font: 500 0.8125rem / 1 var(--font-sans);
  color: var(--color-secondary);
  cursor: pointer;
  border-radius: 4px;
  transition: background-color var(--duration-fast) var(--ease-smooth),
              color var(--duration-fast) var(--ease-smooth);
}

.ks-reading-shelf__tab:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.ks-reading-shelf__tab--active {
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: 600;
}

.ks-reading-shelf__tab:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-reading-shelf__cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.ks-reading-shelf__card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 24px;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
}

.ks-reading-shelf__card:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-reading-shelf__card-eyebrow {
  color: var(--color-accent);
}

.ks-reading-shelf__card-title {
  font: 600 1.125rem / 1.4 var(--font-serif);
  color: var(--color-text);
}

.ks-reading-shelf__card-abstract {
  color: var(--color-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ks-reading-shelf__card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

@media (max-width: 1280px) {
  .ks-reading-shelf__cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .ks-reading-shelf__cards {
    grid-template-columns: 1fr;
  }
}
</style>
