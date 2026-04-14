<script setup lang="ts">
/**
 * Subscriptions settings page — manage arXiv category subscriptions,
 * keyword alerts, and author tracking.
 */
import { Check, Rss, Tag, Users } from 'lucide-vue-next'

definePageMeta({ layout: 'default' })

useHead({
  title: 'Subscriptions — Kaleidoscope',
  meta: [{ name: 'description', content: 'Manage your research topic subscriptions and alerts.' }],
})

const { preferences, loadPreferences, savePreferences } = useUserPreferences()

const ARXIV_CATEGORIES = [
  { id: 'cs.AI', label: 'Artificial Intelligence', group: 'Computer Science' },
  { id: 'cs.CL', label: 'Computation & Language', group: 'Computer Science' },
  { id: 'cs.CV', label: 'Computer Vision', group: 'Computer Science' },
  { id: 'cs.LG', label: 'Machine Learning', group: 'Computer Science' },
  { id: 'cs.NE', label: 'Neural & Evolutionary', group: 'Computer Science' },
  { id: 'cs.RO', label: 'Robotics', group: 'Computer Science' },
  { id: 'cs.IR', label: 'Information Retrieval', group: 'Computer Science' },
  { id: 'cs.CR', label: 'Cryptography & Security', group: 'Computer Science' },
  { id: 'cs.SE', label: 'Software Engineering', group: 'Computer Science' },
  { id: 'cs.DC', label: 'Distributed Computing', group: 'Computer Science' },
  { id: 'cs.DB', label: 'Databases', group: 'Computer Science' },
  { id: 'stat.ML', label: 'Machine Learning', group: 'Statistics' },
  { id: 'math.ST', label: 'Statistics Theory', group: 'Mathematics' },
  { id: 'eess.IV', label: 'Image & Video Processing', group: 'Electrical Engineering' },
  { id: 'eess.SP', label: 'Signal Processing', group: 'Electrical Engineering' },
  { id: 'q-bio.BM', label: 'Biomolecules', group: 'Quantitative Biology' },
  { id: 'q-bio.NC', label: 'Neurons & Cognition', group: 'Quantitative Biology' },
  { id: 'physics.data-an', label: 'Data Analysis', group: 'Physics' },
  { id: 'astro-ph', label: 'Astrophysics', group: 'Physics' },
  { id: 'quant-ph', label: 'Quantum Physics', group: 'Physics' },
]

const categoryGroups = computed(() => {
  const groups: Record<string, typeof ARXIV_CATEGORIES> = {}
  for (const cat of ARXIV_CATEGORIES) {
    if (!groups[cat.group]) groups[cat.group] = []
    groups[cat.group].push(cat)
  }
  return groups
})

const selectedCategories = ref<string[]>([])
const keywords = ref<string[]>([])
const trackedAuthors = ref<string[]>([])
const keywordInput = ref('')
const authorInput = ref('')
const saving = ref(false)

let saveTimer: ReturnType<typeof setTimeout> | null = null

onMounted(async () => {
  await loadPreferences()
  selectedCategories.value = [...preferences.value.subscribed_categories]
  keywords.value = [...preferences.value.keywords]
  trackedAuthors.value = [...preferences.value.tracked_authors]
})

function toggleCategory(id: string) {
  const idx = selectedCategories.value.indexOf(id)
  if (idx >= 0) {
    selectedCategories.value.splice(idx, 1)
  }
  else {
    selectedCategories.value.push(id)
  }
  scheduleSave()
}

function addKeyword() {
  const kw = keywordInput.value.trim()
  if (kw && !keywords.value.includes(kw)) {
    keywords.value.push(kw)
    scheduleSave()
  }
  keywordInput.value = ''
}

function removeKeyword(kw: string) {
  keywords.value = keywords.value.filter(k => k !== kw)
  scheduleSave()
}

function addAuthor() {
  const a = authorInput.value.trim()
  if (a && !trackedAuthors.value.includes(a)) {
    trackedAuthors.value.push(a)
    scheduleSave()
  }
  authorInput.value = ''
}

function removeAuthor(a: string) {
  trackedAuthors.value = trackedAuthors.value.filter(x => x !== a)
  scheduleSave()
}

function scheduleSave() {
  if (saveTimer) clearTimeout(saveTimer)
  saving.value = true
  saveTimer = setTimeout(async () => {
    await savePreferences({
      subscribed_categories: selectedCategories.value,
      keywords: keywords.value,
      tracked_authors: trackedAuthors.value,
      interests_set: true,
    })
    saving.value = false
  }, 800)
}
</script>

<template>
  <div class="ks-sub">
    <div class="ks-sub__header">
      <div class="ks-sub__header-text">
        <p class="ks-sub__eyebrow">
          <Rss :size="12" :stroke-width="2" /> SUBSCRIPTIONS
        </p>
        <h1 class="ks-sub__title">Research Interests</h1>
        <p class="ks-sub__desc">
          Personalize your dashboard and alert feed by selecting what you follow.
        </p>
      </div>
      <Transition name="ks-fade">
        <span v-if="saving" class="ks-sub__saving">Saving…</span>
        <span v-else-if="preferences.interests_set" class="ks-sub__saved">Saved ✓</span>
      </Transition>
    </div>

    <!-- arXiv categories -->
    <section class="ks-sub__section">
      <h2 class="ks-sub__section-title">
        <Tag :size="14" :stroke-width="2" /> arXiv Categories
      </h2>
      <p class="ks-sub__section-desc">
        Selected categories appear as personalized paper feeds on your dashboard.
      </p>

      <div
        v-for="(cats, group) in categoryGroups"
        :key="group"
        class="ks-sub__group"
      >
        <h3 class="ks-sub__group-label">{{ group }}</h3>
        <div class="ks-sub__chips">
          <button
            v-for="cat in cats"
            :key="cat.id"
            type="button"
            :class="['ks-chip', { 'ks-chip--active': selectedCategories.includes(cat.id) }]"
            @click="toggleCategory(cat.id)"
          >
            <Check v-if="selectedCategories.includes(cat.id)" :size="11" :stroke-width="3" />
            <span class="ks-chip__label">{{ cat.label }}</span>
            <span class="ks-chip__id">{{ cat.id }}</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Keywords -->
    <section class="ks-sub__section">
      <h2 class="ks-sub__section-title">
        <Tag :size="14" :stroke-width="2" /> Keyword Alerts
      </h2>
      <p class="ks-sub__section-desc">
        Papers mentioning these keywords surface in your "For You" feed.
      </p>

      <div class="ks-sub__tag-input-row">
        <input
          v-model="keywordInput"
          type="text"
          class="ks-sub__input"
          placeholder="e.g. diffusion models, retrieval-augmented generation…"
          @keydown.enter.prevent="addKeyword"
          @keydown.exact.prevent.comma="addKeyword"
        >
        <button type="button" class="ks-sub__add-btn" :disabled="!keywordInput.trim()" @click="addKeyword">
          Add
        </button>
      </div>
      <div class="ks-sub__tags">
        <span v-for="kw in keywords" :key="kw" class="ks-tag">
          {{ kw }}
          <button type="button" class="ks-tag__remove" :aria-label="`Remove ${kw}`" @click="removeKeyword(kw)">×</button>
        </span>
        <span v-if="keywords.length === 0" class="ks-sub__empty-hint">No keywords yet. Type one above and press Enter.</span>
      </div>
    </section>

    <!-- Author tracking -->
    <section class="ks-sub__section">
      <h2 class="ks-sub__section-title">
        <Users :size="14" :stroke-width="2" /> Author Tracking
      </h2>
      <p class="ks-sub__section-desc">
        Get notified when tracked authors publish new papers on arXiv.
      </p>

      <div class="ks-sub__tag-input-row">
        <input
          v-model="authorInput"
          type="text"
          class="ks-sub__input"
          placeholder="e.g. Yann LeCun, Andrej Karpathy…"
          @keydown.enter.prevent="addAuthor"
        >
        <button type="button" class="ks-sub__add-btn" :disabled="!authorInput.trim()" @click="addAuthor">
          Add
        </button>
      </div>
      <div class="ks-sub__tags">
        <span v-for="author in trackedAuthors" :key="author" class="ks-tag ks-tag--author">
          {{ author }}
          <button type="button" class="ks-tag__remove" :aria-label="`Remove ${author}`" @click="removeAuthor(author)">×</button>
        </span>
        <span v-if="trackedAuthors.length === 0" class="ks-sub__empty-hint">No tracked authors. Type a name above and press Enter.</span>
      </div>
    </section>
  </div>
</template>

<style scoped>
.ks-sub {
  max-width: 760px;
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.ks-sub__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
}

.ks-sub__eyebrow {
  display: flex;
  align-items: center;
  gap: 6px;
  font: 700 0.6875rem / 1 var(--font-sans);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-primary);
  margin: 0 0 8px;
}

.ks-sub__title {
  font: 700 1.75rem / 1.1 var(--font-display);
  color: var(--color-text);
  margin: 0 0 6px;
  letter-spacing: -0.03em;
}

.ks-sub__desc {
  font: 400 0.9rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
}

.ks-sub__saving {
  font: 500 0.8125rem / 1 var(--font-sans);
  color: var(--color-secondary);
  padding-top: 4px;
  white-space: nowrap;
}

.ks-sub__saved {
  font: 500 0.8125rem / 1 var(--font-sans);
  color: var(--color-primary);
  padding-top: 4px;
  white-space: nowrap;
}

.ks-sub__section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
}

.ks-sub__section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font: 600 0.875rem / 1 var(--font-sans);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text);
  margin: 0;
}

.ks-sub__section-desc {
  font: 400 0.875rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
  margin: -8px 0 0;
}

/* Groups */
.ks-sub__group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ks-sub__group-label {
  font: 600 0.7rem / 1 var(--font-sans);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-secondary);
  margin: 0;
}

.ks-sub__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.ks-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 11px;
  border: 1.5px solid var(--color-border);
  border-radius: 20px;
  background: var(--color-bg);
  font: 500 0.8125rem / 1 var(--font-sans);
  color: var(--color-text);
  cursor: pointer;
  transition: border-color 0.15s, background-color 0.15s, color 0.15s;
}

.ks-chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.ks-chip--active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

.ks-chip__id {
  font: 400 0.6rem / 1 var(--font-mono);
  opacity: 0.6;
}

/* Tag input */
.ks-sub__tag-input-row {
  display: flex;
  gap: 8px;
}

.ks-sub__input {
  flex: 1;
  padding: 9px 12px;
  border: 1.5px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg);
  font: 400 0.9rem / 1.4 var(--font-sans);
  color: var(--color-text);
  outline: none;
  transition: border-color 0.15s;
}

.ks-sub__input:focus {
  border-color: var(--color-primary);
}

.ks-sub__add-btn {
  padding: 9px 18px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  font: 600 0.8125rem / 1 var(--font-sans);
  cursor: pointer;
  transition: opacity 0.15s;
  white-space: nowrap;
}

.ks-sub__add-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ks-sub__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  min-height: 32px;
  align-items: center;
}

.ks-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: 4px;
  font: 500 0.8125rem / 1 var(--font-sans);
}

.ks-tag--author {
  background: rgba(13, 115, 119, 0.06);
  border: 1px solid rgba(13, 115, 119, 0.15);
}

.ks-tag__remove {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0;
  opacity: 0.6;
  transition: opacity 0.15s;
}

.ks-tag__remove:hover {
  opacity: 1;
}

.ks-sub__empty-hint {
  font: 400 0.8125rem / 1 var(--font-sans);
  color: var(--color-secondary);
  font-style: italic;
}
</style>
