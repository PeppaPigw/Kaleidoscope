<script setup lang="ts">
/**
 * Discovery Explorer — powered by DeepXiv hybrid search.
 *
 * TopicsWall    — 4 curated category searches (live paper counts)
 * QueryComposer — semantic/keyword query → searchPapers()
 * FacetWall     — category, year, citation filters wired to search
 * RecommendationStream — DeepXiv results with TLDR briefs
 */
import type { TopicCover } from "~/components/discover/TopicsWall.vue";
import type { FacetGroup } from "~/components/discover/FacetWall.vue";
import type { RecommendedPaper } from "~/components/discover/RecommendationStream.vue";
import type {
  DeepXivSearchResult,
  DeepXivBriefResponse,
} from "~/composables/useDeepXiv";
import {
  buildDiscoverFacetGroups,
  filterDiscoverResults,
  getDiscoverVenueLabel,
  normalizeDiscoverCategories,
} from "~/utils/discoverFacets";

definePageMeta({ layout: "default", title: "Discovery Explorer" });

const route = useRoute();
const router = useRouter();

useHead({
  title: "Discover — Kaleidoscope",
  meta: [
    {
      name: "description",
      content:
        "Explore curated research collections and discover papers with intelligent filtering.",
    },
  ],
});

// ── Tab state (from URL query) ────────────────────────────────
const activeTab = computed({
  get: () => (route.query.tab as string) || "search",
  set: (val: string) => {
    router.push({ query: { ...route.query, tab: val } });
  },
});

const routeQueryText = computed(() => {
  const q = route.query.q;
  return typeof q === "string" ? q.trim() : "";
});

// ── AI Assistant drawer state ──────────────────────────────────
const aiDrawerOpen = ref(false);

// Open drawer if ?agent=open in URL
watch(
  () => route.query.agent,
  (val) => {
    if (val === "open") {
      aiDrawerOpen.value = true;
      // Remove query param after opening
      router.replace({ query: { ...route.query, agent: undefined } });
    }
  },
  { immediate: true },
);

// ── Search state ──────────────────────────────────────────────
const queryText = ref("");
const searchResults = ref<DeepXivSearchResult[]>([]);
const briefCache = ref<Record<string, DeepXivBriefResponse>>({});
const resultTotal = ref(0);
const offset = ref(0);
const PAGE_SIZE = 50;
const DEFAULT_DISCOVER_QUERY = "large language model";
const discoverReady = ref(false);
const isSearching = ref(false);
const isLoadingMore = ref(false);
const { resolveLocalPaperRoutes, preferredPaperRoute, openPreferredPaper } =
  usePreferredPaperRoute();

// ── Topic covers ──────────────────────────────────────────────
const topicCovers = ref<TopicCover[]>([]);
const topicsLoading = ref(true);

// ── Bookmark target ───────────────────────────────────────────
const bookmarkTarget = ref<{ arxivId: string; title: string } | null>(null);

// ── Facets ────────────────────────────────────────────────────
const activeYears = ref<string[]>([]);
const activeVenues = ref<string[]>([]);
const activeCategories = ref<string[]>([]);
const impactMode = ref<"any" | "high">("any");
const searchMode = ref<"hybrid" | "bm25" | "vector">("hybrid");

const facetGroups = computed<FacetGroup[]>(() =>
  buildDiscoverFacetGroups(searchResults.value, {
    activeYears: activeYears.value,
    activeVenues: activeVenues.value,
    activeCategories: activeCategories.value,
    impactMode: impactMode.value,
    searchMode: searchMode.value,
  }),
);

// ── Curated topic definitions ─────────────────────────────────
const TOPIC_DEFS = [
  {
    id: "tc-ai",
    query: "reasoning large language model chain of thought",
    category: "cs.AI",
    label: "Trending in AI",
    accent: "teal" as const,
  },
  {
    id: "tc-cv",
    query: "multimodal vision language model image generation",
    category: "cs.CV",
    label: "Visual AI",
    accent: "gold" as const,
  },
  {
    id: "tc-bio",
    query: "protein structure drug discovery generative model",
    category: "q-bio.BM",
    label: "Life Sciences",
    accent: "teal" as const,
  },
  {
    id: "tc-bench",
    query: "benchmark evaluation leakage contamination",
    category: "cs.LG",
    label: "Methodology",
    accent: "gold" as const,
  },
];

const TOPIC_SUBTITLES: Record<string, string> = {
  "tc-ai": "Chain-of-thought, planning, and multi-step reasoning in LLMs",
  "tc-cv": "Vision-language models, diffusion, and generative visual AI",
  "tc-bio": "Protein folding, drug design, and biomedical AI",
  "tc-bench": "Evaluation methodology, data contamination, and robustness",
};

// ── Derived search params from facets ─────────────────────────
const searchParams = computed(() => {
  let dateFrom: string | undefined;
  let dateTo: string | undefined;
  if (activeYears.value.length > 0) {
    const years = activeYears.value.map(Number).sort();
    dateFrom = `${years[0]!}-01-01`;
    dateTo = `${years[years.length - 1]!}-12-31`;
  }

  return {
    dateFrom,
    dateTo,
    categories: activeCategories.value,
    minCitation: impactMode.value === "high" ? 50 : undefined,
    searchMode: searchMode.value,
  };
});

// ── Recommendation list for display ───────────────────────────
const visibleResults = computed(() =>
  filterDiscoverResults(searchResults.value, {
    activeYears: activeYears.value,
    activeVenues: activeVenues.value,
    activeCategories: activeCategories.value,
    impactMode: impactMode.value,
  }),
);

const recommendations = computed<RecommendedPaper[]>(() =>
  visibleResults.value.map((r) => {
    const normalizedCategories = normalizeDiscoverCategories(r.categories);

    return {
      id: r.arxiv_id,
      href: preferredPaperRoute(r.arxiv_id),
      eyebrow: normalizedCategories[0] ?? "arXiv",
      title: r.title,
      abstract: r.abstract ?? "",
      tldr: briefCache.value[r.arxiv_id]?.tldr ?? undefined,
      venue: getDiscoverVenueLabel(r),
      score: r.score,
      tags: normalizedCategories.slice(0, 2),
      strong: r.citations > 50,
    };
  }),
);

async function fetchBriefs(ids: string[]) {
  const { getPaperBrief } = useDeepXiv();
  const uncached = ids.filter((id) => !briefCache.value[id]);
  if (!uncached.length) return;
  const results = await Promise.allSettled(
    uncached.map((id) => getPaperBrief(id)),
  );
  results.forEach((r, i) => {
    if (r.status === "fulfilled" && r.value) {
      briefCache.value[uncached[i]!] = r.value;
    }
  });
}

// ── Core search ───────────────────────────────────────────────
async function doSearch(append = false) {
  const { searchPapers } = useDeepXiv();
  if (!append) {
    isSearching.value = true;
    offset.value = 0;
  } else {
    isLoadingMore.value = true;
  }

  const params = searchParams.value;
  try {
    const res = await searchPapers(
      queryText.value.trim() || DEFAULT_DISCOVER_QUERY,
      {
        size: PAGE_SIZE,
        offset: offset.value,
        categories: params.categories.length ? params.categories : undefined,
        date_from: params.dateFrom,
        date_to: params.dateTo,
        min_citation: params.minCitation,
        search_mode: params.searchMode,
      },
    );

    if (append) {
      searchResults.value = [...searchResults.value, ...(res.results ?? [])];
    } else {
      searchResults.value = res.results ?? [];
    }
    resultTotal.value = res.total ?? 0;

    // Fetch briefs for first page top 8
    const ids = searchResults.value.slice(0, 8).map((r) => r.arxiv_id);
    await fetchBriefs(ids);
    await resolveLocalPaperRoutes(
      searchResults.value.map((result) => result.arxiv_id),
    );
  } catch (e) {
    console.error("[Discover] search error", e);
    if (!append) searchResults.value = [];
  } finally {
    isSearching.value = false;
    isLoadingMore.value = false;
  }
}

const suppressFacetSearch = ref(false);

function resetSearchFilters() {
  suppressFacetSearch.value = true;
  if (searchDebounceTimer) {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = null;
  }
  activeYears.value = [];
  activeVenues.value = [];
  activeCategories.value = [];
  impactMode.value = "any";
  searchMode.value = "hybrid";
  nextTick(() => {
    suppressFacetSearch.value = false;
  });
}

async function syncSearchFromRoute(query: string) {
  const trimmed = query.trim();

  if (trimmed) {
    resetSearchFilters();
    activeTab.value = "search";
    queryText.value = trimmed;
  } else {
    queryText.value = "";
  }

  offset.value = 0;
  await doSearch();
}

// ── Mount ─────────────────────────────────────────────────────
onMounted(async () => {
  const { searchPapers } = useDeepXiv();

  // 1. Load topic covers in parallel
  const topicResults = await Promise.allSettled(
    TOPIC_DEFS.map((td) =>
      searchPapers(td.query, { categories: [td.category], size: 1 }),
    ),
  );
  topicCovers.value = TOPIC_DEFS.map((td, i) => {
    const res = topicResults[i];
    const total = res?.status === "fulfilled" ? (res.value.total ?? 0) : 0;
    const topPaper =
      res?.status === "fulfilled" ? res.value.results[0] : undefined;
    return {
      id: td.id,
      label: td.label,
      title: topPaper?.title ?? td.query,
      subtitle: TOPIC_SUBTITLES[td.id] ?? "",
      count: total,
      accent: td.accent,
    };
  });
  topicsLoading.value = false;

  // 2. Load route-driven or default recommendation feed
  if (routeQueryText.value) {
    await syncSearchFromRoute(routeQueryText.value);
  } else {
    await doSearch();
  }
  discoverReady.value = true;
});

onUnmounted(() => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
});

// ── Unified watch — re-search when query or filters change ────
// Debounced to prevent double-firing when both query & facets change together
let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null;

function scheduleSearch() {
  if (suppressFacetSearch.value) return;
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {
    offset.value = 0;
    doSearch();
  }, 60);
}

watch(
  () =>
    JSON.stringify({
      years: activeYears.value,
      categories: activeCategories.value,
      impact: impactMode.value,
      mode: searchMode.value,
    }),
  scheduleSearch,
);

watch(routeQueryText, (query, previous) => {
  if (!discoverReady.value || query === previous) return;
  void syncSearchFromRoute(query);
});

watch(searchResults, (results) => {
  const availableVenues = new Set(
    results.map((result) => getDiscoverVenueLabel(result)),
  );
  activeVenues.value = activeVenues.value.filter((venue) =>
    availableVenues.has(venue),
  );
});

// ── Handlers ──────────────────────────────────────────────────
function handleTopicClick(topic: TopicCover) {
  const def = TOPIC_DEFS.find((td) => td.id === topic.id);
  if (def) {
    queryText.value = def.query;
    activeCategories.value = [def.category];
    activeVenues.value = [];
    scheduleSearch();
    return;
  } else {
    queryText.value = topic.title;
  }
  // If no facet changed, kick off search directly
  scheduleSearch();
}

function handleFacetToggle(group: string, option: string, active: boolean) {
  if (group === "Search Mode") {
    if (!active) return;
    searchMode.value =
      option === "Semantic"
        ? "vector"
        : option === "Keyword"
          ? "bm25"
          : "hybrid";
  } else if (group === "Impact") {
    impactMode.value = option.startsWith("High") && active ? "high" : "any";
  } else if (group === "Year") {
    activeYears.value = active
      ? [...new Set([...activeYears.value, option])]
      : activeYears.value.filter((value) => value !== option);
  } else if (group === "Venue") {
    activeVenues.value = active
      ? [...new Set([...activeVenues.value, option])]
      : activeVenues.value.filter((value) => value !== option);
  } else if (group === "Category") {
    activeCategories.value = active
      ? [...new Set([...activeCategories.value, option])]
      : activeCategories.value.filter((value) => value !== option);
  }
}

async function handlePaperClick(paper: RecommendedPaper) {
  await openPreferredPaper(paper.id);
}

function handlePaperSave(paper: RecommendedPaper) {
  bookmarkTarget.value = { arxivId: paper.id, title: paper.title };
}

function handleQuerySubmit(q: string) {
  const trimmed = q.trim();
  if (!trimmed) return;

  if (trimmed === routeQueryText.value && activeTab.value === "search") {
    void syncSearchFromRoute(trimmed);
    return;
  }

  router.push({ query: { ...route.query, tab: "search", q: trimmed } });
}

function handleLoadMore() {
  offset.value += PAGE_SIZE;
  doSearch(true);
}

const queryPlaceholder =
  "e.g. citation-grounded agents with human evaluation, biomedical evidence extraction, benchmark leakage detection…";
const querySuggestions = [
  "LLM reasoning chain of thought",
  "Multimodal clinical VLM",
  "Efficient long-context attention",
  "Diffusion model image generation",
];

const hasMore = computed(() => offset.value + PAGE_SIZE < resultTotal.value);
const isClientFiltered = computed(
  () => visibleResults.value.length !== searchResults.value.length,
);
</script>

<template>
  <div class="ks-discover">
    <!-- ═══ Row 1: Topics Wall + Query Composer ═══ -->
    <div class="ks-discover__row ks-discover__row--top">
      <DiscoverTopicsWall
        :topics="topicsLoading ? [] : topicCovers"
        @topic-click="handleTopicClick"
      />
      <DiscoverQueryComposer
        v-model="queryText"
        :placeholder="queryPlaceholder"
        :suggestions="querySuggestions"
        @suggestion-click="handleQuerySubmit"
        @submit="handleQuerySubmit"
      />
    </div>

    <!-- ═══ Tab Navigation ═══ -->
    <div class="ks-discover__tabs">
      <button
        type="button"
        :class="[
          'ks-discover__tab',
          activeTab === 'search' && 'ks-discover__tab--active',
        ]"
        @click="activeTab = 'search'"
      >
        Search Results
      </button>
      <button
        type="button"
        :class="[
          'ks-discover__tab',
          activeTab === 'trending' && 'ks-discover__tab--active',
        ]"
        @click="activeTab = 'trending'"
      >
        Trending Papers
      </button>
    </div>

    <!-- ═══ Row 2+: Facets + Stream ═══ -->
    <div
      v-if="activeTab === 'search'"
      class="ks-discover__row ks-discover__row--main"
    >
      <DiscoverFacetWall
        :groups="facetGroups"
        @facet-toggle="handleFacetToggle"
      />

      <div class="ks-discover__stream-col">
        <!-- Results header -->
        <div
          v-if="!isSearching && searchResults.length > 0"
          class="ks-discover__results-header"
        >
          <span class="ks-discover__results-count">
            {{ resultTotal.toLocaleString() }} results
            <span v-if="queryText">
              for "<strong>{{ queryText }}</strong
              >"</span
            >
            <span v-if="isClientFiltered">
              · showing {{ recommendations.length }} in loaded results</span
            >
          </span>
        </div>

        <!-- Loading skeleton -->
        <div v-if="isSearching" class="ks-discover__skeleton-grid">
          <div v-for="n in 4" :key="n" class="ks-discover__skeleton-card">
            <div class="ks-discover__skeleton-eyebrow" />
            <div class="ks-discover__skeleton-title" />
            <div class="ks-discover__skeleton-text" />
            <div
              class="ks-discover__skeleton-text ks-discover__skeleton-text--short"
            />
          </div>
        </div>

        <DiscoverRecommendationStream
          v-else
          :papers="recommendations"
          @paper-click="handlePaperClick"
          @save="handlePaperSave"
          @compare="handlePaperClick"
        />

        <!-- Load more -->
        <div v-if="hasMore && !isSearching" class="ks-discover__load-more">
          <button
            type="button"
            class="ks-discover__load-more-btn"
            :disabled="isLoadingMore"
            @click="handleLoadMore"
          >
            {{
              isLoadingMore
                ? "Loading…"
                : `Load more (${resultTotal - searchResults.length} remaining)`
            }}
          </button>
        </div>

        <!-- Empty state -->
        <div
          v-if="!isSearching && searchResults.length === 0"
          class="ks-discover__empty"
        >
          <p class="ks-discover__empty-title">No results found</p>
          <p class="ks-discover__empty-desc">
            Try a different query or clear some filters.
          </p>
        </div>
      </div>
    </div>

    <!-- ═══ Trending Tab Content ═══ -->
    <div
      v-else-if="activeTab === 'trending'"
      class="ks-discover__trending-container"
    >
      <DiscoverTrendingTab />
    </div>

    <!-- Bookmark modal -->
    <CollectionsGroupPickerModal
      v-if="bookmarkTarget"
      :arxiv-id="bookmarkTarget.arxivId"
      :title="bookmarkTarget.title"
      @close="bookmarkTarget = null"
      @saved="bookmarkTarget = null"
    />

    <!-- AI Assistant Drawer -->
    <DiscoverAiAssistantDrawer
      :open="aiDrawerOpen"
      @close="aiDrawerOpen = false"
    />

    <!-- Floating AI Button -->
    <DiscoverFloatingAiButton @click="aiDrawerOpen = true" />
  </div>
</template>

<style scoped>
.ks-discover {
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding-bottom: 96px;
}

/* ─── Grid rows ───────────────────────────────────────────── */
.ks-discover__row--top {
  display: grid;
  grid-template-columns: 5fr 2fr;
  gap: 24px;
  align-items: stretch;
}

.ks-discover__row--main {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

/* ─── Stream column ───────────────────────────────────────── */
.ks-discover__stream-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.ks-discover__results-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ks-discover__results-count {
  font: 400 0.8125rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-discover__results-count strong {
  color: var(--color-text);
  font-weight: 600;
}

/* ─── Skeleton loaders ────────────────────────────────────── */
@keyframes ks-discover-shimmer {
  0% {
    background-position: -200% center;
  }
  100% {
    background-position: 200% center;
  }
}

.ks-discover__skeleton-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.ks-discover__skeleton-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

.ks-discover__skeleton-eyebrow,
.ks-discover__skeleton-title,
.ks-discover__skeleton-text {
  border-radius: 4px;
  background: linear-gradient(
    90deg,
    var(--color-border) 25%,
    rgba(255, 255, 255, 0.06) 50%,
    var(--color-border) 75%
  );
  background-size: 200% 100%;
  animation: ks-discover-shimmer 1.5s infinite;
}

.ks-discover__skeleton-eyebrow {
  height: 10px;
  width: 60px;
}
.ks-discover__skeleton-title {
  height: 20px;
  width: 90%;
}
.ks-discover__skeleton-text {
  height: 14px;
  width: 100%;
}
.ks-discover__skeleton-text--short {
  width: 70%;
}

/* ─── Load more ───────────────────────────────────────────── */
.ks-discover__load-more {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}

.ks-discover__load-more-btn {
  padding: 10px 28px;
  background: var(--color-surface);
  border: 1.5px solid var(--color-border);
  border-radius: 6px;
  font: 500 0.875rem / 1 var(--font-sans);
  color: var(--color-text);
  cursor: pointer;
  transition:
    border-color 0.15s,
    color 0.15s;
}

.ks-discover__load-more-btn:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.ks-discover__load-more-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ─── Empty ───────────────────────────────────────────────── */
.ks-discover__empty {
  padding: 60px 40px;
  text-align: center;
  background: var(--color-surface);
  border: 1px dashed var(--color-border);
  border-radius: 8px;
}

.ks-discover__empty-title {
  font: 600 1.125rem / 1 var(--font-display);
  color: var(--color-text);
  margin: 0 0 8px;
}

.ks-discover__empty-desc {
  font: 400 0.875rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
}

/* ─── Tab Navigation ──────────────────────────────────────── */
.ks-discover__tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 24px;
}

.ks-discover__tab {
  padding: 12px 24px;
  border: none;
  background: none;
  font: 500 0.875rem / 1 var(--font-sans);
  color: var(--color-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition:
    color 0.15s,
    border-color 0.15s;
  position: relative;
  bottom: -1px;
}

.ks-discover__tab:hover {
  color: var(--color-text);
}

.ks-discover__tab--active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

/* ─── Trending Container ──────────────────────────────────── */
.ks-discover__trending-container {
  width: 100%;
}

/* ─── Responsive ──────────────────────────────────────────── */
@media (max-width: 1280px) {
  .ks-discover__row--main {
    grid-template-columns: 240px minmax(0, 1fr);
    gap: 16px;
  }
  .ks-discover__skeleton-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .ks-discover__row--top {
    grid-template-columns: 1fr;
  }
  .ks-discover__row--main {
    grid-template-columns: 1fr;
  }
  .ks-discover__skeleton-grid {
    grid-template-columns: 1fr;
  }
}
</style>
