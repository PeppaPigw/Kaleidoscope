<script setup lang="ts">
/**
 * Subscriptions settings page — manage arXiv category subscriptions,
 * keyword alerts, and author tracking.
 */
import { Check, Layers3, Rss, Tag, Users } from "lucide-vue-next";
import {
  buildResearchFacetCatalog,
  EMPTY_RESEARCH_FACETS,
  getResearchFacetSelectionCount,
  getResearchFacetSummary,
  normalizeResearchFacetPreferences,
  type ResearchFacetGroup,
  type ResearchFacetKey,
  type ResearchFacetPreferences,
} from "~/utils/researchFacets";

definePageMeta({ layout: "default" });

useHead({
  title: "Subscriptions — Kaleidoscope",
  meta: [
    {
      name: "description",
      content: "Manage your research topic subscriptions and alerts.",
    },
  ],
});

const { preferences, loadPreferences, savePreferences } = useUserPreferences();

const ARXIV_CATEGORIES = [
  { id: "cs.AI", label: "Artificial Intelligence", group: "Computer Science" },
  { id: "cs.CL", label: "Computation & Language", group: "Computer Science" },
  { id: "cs.CV", label: "Computer Vision", group: "Computer Science" },
  { id: "cs.LG", label: "Machine Learning", group: "Computer Science" },
  { id: "cs.NE", label: "Neural & Evolutionary", group: "Computer Science" },
  { id: "cs.RO", label: "Robotics", group: "Computer Science" },
  { id: "cs.IR", label: "Information Retrieval", group: "Computer Science" },
  { id: "cs.CR", label: "Cryptography & Security", group: "Computer Science" },
  { id: "cs.SE", label: "Software Engineering", group: "Computer Science" },
  { id: "cs.DC", label: "Distributed Computing", group: "Computer Science" },
  { id: "cs.DB", label: "Databases", group: "Computer Science" },
  { id: "stat.ML", label: "Machine Learning", group: "Statistics" },
  { id: "math.ST", label: "Statistics Theory", group: "Mathematics" },
  {
    id: "eess.IV",
    label: "Image & Video Processing",
    group: "Electrical Engineering",
  },
  {
    id: "eess.SP",
    label: "Signal Processing",
    group: "Electrical Engineering",
  },
  { id: "q-bio.BM", label: "Biomolecules", group: "Quantitative Biology" },
  {
    id: "q-bio.NC",
    label: "Neurons & Cognition",
    group: "Quantitative Biology",
  },
  { id: "physics.data-an", label: "Data Analysis", group: "Physics" },
  { id: "astro-ph", label: "Astrophysics", group: "Physics" },
  { id: "quant-ph", label: "Quantum Physics", group: "Physics" },
];

const categoryGroups = computed(() => {
  const groups: Record<string, typeof ARXIV_CATEGORIES> = {};
  for (const cat of ARXIV_CATEGORIES) {
    const bucket = groups[cat.group] ?? [];
    bucket.push(cat);
    groups[cat.group] = bucket;
  }
  return groups;
});

const selectedCategories = ref<string[]>([]);
const keywords = ref<string[]>([]);
const trackedAuthors = ref<string[]>([]);
const selectedResearchFacets = ref<ResearchFacetPreferences>({
  ...EMPTY_RESEARCH_FACETS,
});
const keywordInput = ref("");
const authorInput = ref("");
const researchFacetFilter = ref("");
const researchFacetCatalog = ref<ResearchFacetGroup[]>([]);
const isLoading = ref(true);
const saving = ref(false);
const loadError = ref("");
const saveError = ref("");
const researchFacetLoadError = ref("");

let saveTimer: ReturnType<typeof setTimeout> | null = null;

const selectedResearchFacetCount = computed(() =>
  getResearchFacetSelectionCount(selectedResearchFacets.value),
);

const selectedResearchFacetSummary = computed(() =>
  getResearchFacetSummary(selectedResearchFacets.value, 4),
);

const visibleResearchFacetCatalog = computed(() => {
  const query = researchFacetFilter.value.trim().toLocaleLowerCase();
  if (!query) return researchFacetCatalog.value;

  return researchFacetCatalog.value
    .map((group) => ({
      ...group,
      buckets: group.buckets
        .map((bucket) => ({
          ...bucket,
          options: bucket.options.filter((option) =>
            option.toLocaleLowerCase().includes(query),
          ),
        }))
        .filter((bucket) => bucket.options.length > 0),
    }))
    .filter((group) => group.buckets.length > 0);
});

async function loadResearchFacetCatalog() {
  const taxonomy =
    await $fetch<Parameters<typeof buildResearchFacetCatalog>[0]>(
      "/labels.json",
    );
  researchFacetCatalog.value = buildResearchFacetCatalog(taxonomy);
}

async function persistPreferences() {
  saveError.value = "";
  saving.value = true;
  try {
    await savePreferences({
      subscribed_categories: selectedCategories.value,
      keywords: keywords.value,
      tracked_authors: trackedAuthors.value,
      research_facets: selectedResearchFacets.value,
      interests_set: true,
    });
  } catch {
    saveError.value = "Could not save subscription changes.";
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  const [preferencesResult, facetsResult] = await Promise.allSettled([
    loadPreferences(),
    loadResearchFacetCatalog(),
  ]);

  if (preferencesResult.status === "fulfilled") {
    selectedCategories.value = [...preferences.value.subscribed_categories];
    keywords.value = [...preferences.value.keywords];
    trackedAuthors.value = [...preferences.value.tracked_authors];
    selectedResearchFacets.value = normalizeResearchFacetPreferences(
      preferences.value.research_facets,
    );
  } else {
    loadError.value =
      "Failed to load your subscriptions. Refresh and try again.";
  }

  if (facetsResult.status === "rejected") {
    researchFacetLoadError.value =
      "Could not load research facets right now. Your saved preferences are still available.";
  }

  isLoading.value = false;
});

onBeforeUnmount(() => {
  if (saveTimer) clearTimeout(saveTimer);
});

onBeforeRouteLeave(async () => {
  if (!saveTimer) return;
  clearTimeout(saveTimer);
  saveTimer = null;
  await persistPreferences();
});

function toggleCategory(id: string) {
  const idx = selectedCategories.value.indexOf(id);
  if (idx >= 0) {
    selectedCategories.value.splice(idx, 1);
  } else {
    selectedCategories.value.push(id);
  }
  scheduleSave();
}

function isResearchFacetSelected(key: ResearchFacetKey, value: string) {
  return selectedResearchFacets.value[key].includes(value);
}

function toggleResearchFacet(key: ResearchFacetKey, value: string) {
  const current = selectedResearchFacets.value[key];
  const next = current.includes(value)
    ? current.filter((item) => item !== value)
    : [...current, value];

  selectedResearchFacets.value = normalizeResearchFacetPreferences({
    ...selectedResearchFacets.value,
    [key]: next,
  });
  scheduleSave();
}

function addKeyword() {
  const kw = keywordInput.value.trim();
  if (
    kw &&
    !keywords.value.some(
      (existing) => existing.toLocaleLowerCase() === kw.toLocaleLowerCase(),
    )
  ) {
    keywords.value.push(kw);
    scheduleSave();
  }
  keywordInput.value = "";
}

function handleKeywordKeydown(event: KeyboardEvent) {
  if (event.key !== "Enter" && event.key !== ",") return;
  event.preventDefault();
  addKeyword();
}

function removeKeyword(kw: string) {
  keywords.value = keywords.value.filter((k) => k !== kw);
  scheduleSave();
}

function addAuthor() {
  const a = authorInput.value.trim();
  if (
    a &&
    !trackedAuthors.value.some(
      (existing) => existing.toLocaleLowerCase() === a.toLocaleLowerCase(),
    )
  ) {
    trackedAuthors.value.push(a);
    scheduleSave();
  }
  authorInput.value = "";
}

function removeAuthor(a: string) {
  trackedAuthors.value = trackedAuthors.value.filter((x) => x !== a);
  scheduleSave();
}

function scheduleSave() {
  if (saveTimer) clearTimeout(saveTimer);
  saving.value = true;
  saveTimer = setTimeout(async () => {
    saveTimer = null;
    await persistPreferences();
  }, 800);
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
          Personalize your dashboard and alert feed by selecting what you
          follow.
        </p>
      </div>
      <Transition name="ks-fade">
        <span v-if="saving" class="ks-sub__saving">Saving…</span>
        <span v-else-if="saveError" class="ks-sub__error">{{ saveError }}</span>
        <span v-else-if="preferences.interests_set" class="ks-sub__saved"
          >Saved ✓</span
        >
      </Transition>
    </div>

    <p v-if="loadError" class="ks-sub__error ks-sub__error--block">
      {{ loadError }}
    </p>

    <!-- arXiv categories -->
    <section class="ks-sub__section">
      <h2 class="ks-sub__section-title">
        <Tag :size="14" :stroke-width="2" /> arXiv Categories
      </h2>
      <p class="ks-sub__section-desc">
        Selected categories appear as personalized paper feeds on your
        dashboard.
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
            :disabled="isLoading"
            :class="[
              'ks-chip',
              { 'ks-chip--active': selectedCategories.includes(cat.id) },
            ]"
            @click="toggleCategory(cat.id)"
          >
            <Check
              v-if="selectedCategories.includes(cat.id)"
              :size="11"
              :stroke-width="3"
            />
            <span class="ks-chip__label">{{ cat.label }}</span>
            <span class="ks-chip__id">{{ cat.id }}</span>
          </button>
        </div>
      </div>
    </section>

    <section class="ks-sub__section">
      <h2 class="ks-sub__section-title">
        <Layers3 :size="14" :stroke-width="2" /> Research Facets
      </h2>
      <p class="ks-sub__section-desc">
        Use the shared paper-label taxonomy to refine dashboard recommendations
        beyond broad arXiv subjects.
      </p>

      <div class="ks-sub__facet-toolbar">
        <input
          v-model="researchFacetFilter"
          type="text"
          class="ks-sub__input"
          placeholder="Filter facets, e.g. controlled generation, chemistry, ablation…"
          :disabled="isLoading || researchFacetCatalog.length === 0"
        >
        <span class="ks-sub__facet-count"
          >{{ selectedResearchFacetCount }} selected</span
        >
      </div>

      <p
        v-if="selectedResearchFacetSummary.length > 0"
        class="ks-sub__facet-summary"
      >
        Active facets: {{ selectedResearchFacetSummary.join(" · ") }}
      </p>
      <p v-if="researchFacetLoadError" class="ks-sub__error">
        {{ researchFacetLoadError }}
      </p>

      <template v-if="visibleResearchFacetCatalog.length > 0">
        <div
          v-for="group in visibleResearchFacetCatalog"
          :key="group.key"
          class="ks-sub__group ks-sub__group--facet"
        >
          <div class="ks-sub__facet-group-head">
            <h3 class="ks-sub__group-label">{{ group.label }}</h3>
            <span class="ks-sub__facet-pill">{{
              selectedResearchFacets[group.key].length
            }}</span>
          </div>
          <p class="ks-sub__facet-desc">{{ group.description }}</p>

          <div
            v-for="bucket in group.buckets"
            :key="`${group.key}:${bucket.id}`"
            class="ks-sub__facet-bucket"
          >
            <h4 class="ks-sub__facet-bucket-label">{{ bucket.label }}</h4>
            <div class="ks-sub__chips">
              <button
                v-for="option in bucket.options"
                :key="`${group.key}:${option}`"
                type="button"
                :disabled="isLoading"
                :class="[
                  'ks-chip',
                  'ks-chip--facet',
                  {
                    'ks-chip--active': isResearchFacetSelected(
                      group.key,
                      option,
                    ),
                  },
                ]"
                @click="toggleResearchFacet(group.key, option)"
              >
                <Check
                  v-if="isResearchFacetSelected(group.key, option)"
                  :size="11"
                  :stroke-width="3"
                />
                <span class="ks-chip__label">{{ option }}</span>
              </button>
            </div>
          </div>
        </div>
      </template>
      <p
        v-else-if="researchFacetFilter.trim()"
        class="ks-sub__empty-hint ks-sub__empty-hint--block"
      >
        No research facets match “{{ researchFacetFilter.trim() }}”.
      </p>
    </section>

    <!-- Keywords -->
    <section class="ks-sub__section">
      <h2 class="ks-sub__section-title">
        <Tag :size="14" :stroke-width="2" /> Keyword Alerts
      </h2>
      <p class="ks-sub__section-desc">
        Papers mentioning these keywords surface in your "For You" feed and
        create live alert rules.
      </p>

      <div class="ks-sub__tag-input-row">
        <input
          v-model="keywordInput"
          type="text"
          class="ks-sub__input"
          placeholder="e.g. diffusion models, retrieval-augmented generation…"
          :disabled="isLoading"
          @keydown="handleKeywordKeydown"
        >
        <button
          type="button"
          class="ks-sub__add-btn"
          :disabled="isLoading || !keywordInput.trim()"
          @click="addKeyword"
        >
          Add
        </button>
      </div>
      <div class="ks-sub__tags">
        <span v-for="kw in keywords" :key="kw" class="ks-tag">
          {{ kw }}
          <button
            type="button"
            class="ks-tag__remove"
            :aria-label="`Remove ${kw}`"
            @click="removeKeyword(kw)"
          >
            ×
          </button>
        </span>
        <span v-if="keywords.length === 0" class="ks-sub__empty-hint"
          >No keywords yet. Type one above and press Enter.</span
        >
      </div>
    </section>

    <!-- Author tracking -->
    <section class="ks-sub__section">
      <h2 class="ks-sub__section-title">
        <Users :size="14" :stroke-width="2" /> Author Tracking
      </h2>
      <p class="ks-sub__section-desc">
        Tracked authors are synced into live alert rules and notify you on new
        matches.
      </p>

      <div class="ks-sub__tag-input-row">
        <input
          v-model="authorInput"
          type="text"
          class="ks-sub__input"
          placeholder="e.g. Yann LeCun, Andrej Karpathy…"
          :disabled="isLoading"
          @keydown.enter.prevent="addAuthor"
        >
        <button
          type="button"
          class="ks-sub__add-btn"
          :disabled="isLoading || !authorInput.trim()"
          @click="addAuthor"
        >
          Add
        </button>
      </div>
      <div class="ks-sub__tags">
        <span
          v-for="author in trackedAuthors"
          :key="author"
          class="ks-tag ks-tag--author"
        >
          {{ author }}
          <button
            type="button"
            class="ks-tag__remove"
            :aria-label="`Remove ${author}`"
            @click="removeAuthor(author)"
          >
            ×
          </button>
        </span>
        <span v-if="trackedAuthors.length === 0" class="ks-sub__empty-hint"
          >No tracked authors. Type a name above and press Enter.</span
        >
      </div>
    </section>
  </div>
</template>

<style scoped>
.ks-sub {
  max-width: 980px;
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

.ks-sub__error {
  font: 500 0.8125rem / 1.3 var(--font-sans);
  color: var(--color-danger, #c23b22);
}

.ks-sub__error--block {
  margin: -20px 0 0;
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

.ks-sub__group--facet {
  gap: 14px;
  padding-top: 4px;
}

.ks-sub__group-label {
  font: 600 0.7rem / 1 var(--font-sans);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-secondary);
  margin: 0;
}

.ks-sub__facet-group-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.ks-sub__facet-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ks-sub__facet-count {
  font: 600 0.75rem / 1 var(--font-sans);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-secondary);
  white-space: nowrap;
}

.ks-sub__facet-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  background: rgba(13, 115, 119, 0.08);
  color: var(--color-primary);
  font: 600 0.75rem / 1 var(--font-sans);
}

.ks-sub__facet-summary {
  margin: -4px 0 0;
  font: 500 0.8125rem / 1.5 var(--font-sans);
  color: var(--color-text);
}

.ks-sub__facet-desc {
  margin: -8px 0 0;
  font: 400 0.8125rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
}

.ks-sub__facet-bucket {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ks-sub__facet-bucket-label {
  margin: 0;
  font: 600 0.75rem / 1.2 var(--font-sans);
  color: var(--color-text);
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
  transition:
    border-color 0.15s,
    background-color 0.15s,
    color 0.15s;
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

.ks-chip--facet {
  align-items: flex-start;
  padding: 7px 11px;
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

.ks-sub__empty-hint--block {
  display: block;
}

@media (max-width: 720px) {
  .ks-sub__header,
  .ks-sub__facet-toolbar,
  .ks-sub__tag-input-row {
    flex-direction: column;
    align-items: stretch;
  }

  .ks-sub__facet-count {
    white-space: normal;
  }
}
</style>
