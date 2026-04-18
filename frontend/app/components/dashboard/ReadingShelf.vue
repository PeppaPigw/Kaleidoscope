<script setup lang="ts">
/**
 * ReadingShelf — Recommended reading cards with tabbed categories.
 *
 * Displays paper recommendations in a 3-column grid with gold-top accent cards.
 * Supports "For You", "Trending", and "Controversial" tabs.
 * Uses proper ARIA tab pattern with keyboard arrow-key switching.
 * Cards use `role="link"` with Space + Enter handling for screen readers.
 */

export interface LabelDim {
  value: string
  color: string
}

export interface ReadingPick {
  id: string
  eyebrow: string
  title: string
  venue: string
  tags: string[]
  abstract: string
  labelDims?: LabelDim[]
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

const { t } = useTranslation()

type ShelfTab = 'for-you' | 'trending' | 'controversial'

const activeTab = ref<ShelfTab>('for-you')

const tabLabelKeys: Record<ShelfTab, keyof typeof import('~/composables/useTranslation').UI_LABELS.en> = {
  'for-you': 'forYou',
  'trending': 'trending',
  'controversial': 'controversial',
}

const tabs: ShelfTab[] = ['for-you', 'trending', 'controversial']

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
    activeTab.value = tabs[newIdx]!
    emit('tab-change', tabs[newIdx]!)
    // Move focus to the new tab
    const el = document.getElementById(tabId(tabs[newIdx]!))
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
      <h3 :id="`${uid}-title`" class="ks-type-section-title">{{ t('recommendedReading') }}</h3>
      <div class="ks-reading-shelf__tabs" role="tablist" :aria-label="t('recommendedReading')">
        <button
          v-for="(tab, idx) in tabs"
          :id="tabId(tab)"
          :key="tab"
          role="tab"
          :aria-selected="activeTab === tab"
          :aria-controls="panelId(tab)"
          :tabindex="activeTab === tab ? 0 : -1"
          :class="[
            'ks-reading-shelf__tab',
            { 'ks-reading-shelf__tab--active': activeTab === tab },
          ]"
          @click="selectTab(tab)"
          @keydown="handleTabKeydown($event, idx)"
        >
          {{ t(tabLabelKeys[tab]) }}
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
        <KsTranslatableTitle :text="pick.title" tag="h4" title-class="ks-reading-shelf__card-title" />
        <p class="ks-type-body-sm ks-reading-shelf__card-abstract">
          {{ pick.abstract }}
        </p>
        <KsTranslateBtn :text="pick.abstract" />
        <!-- Taxonomy label chips (one per dimension) — shown whenever labels object exists -->
        <div v-if="pick.labelDims !== undefined" class="ks-reading-shelf__card-labels">
          <span
            v-for="dim in pick.labelDims"
            :key="dim.value"
            class="ks-reading-shelf__label-chip"
            :style="{ borderColor: dim.color, color: dim.color }"
          >{{ dim.value }}</span>
        </div>
        <!-- Fallback meta row only for papers without any labels data -->
        <div v-else class="ks-reading-shelf__card-meta">
          <span class="ks-type-data">{{ pick.venue }}</span>
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

.ks-reading-shelf__card-labels {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.ks-reading-shelf__label-chip {
  display: inline-block;
  padding: 2px 8px;
  border: 1px solid;
  border-radius: 3px;
  font: 400 0.72rem / 1.5 var(--font-sans);
  background: transparent;
  white-space: nowrap;
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
