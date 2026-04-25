<script setup lang="ts">
/**
 * Analytics Dashboard — analysis/index.vue
 *
 * Data-driven analytics page fetching from /api/v1/analytics/*.
 */
import type {
  AnalyticsOverview,
  AnalyticsTimeline,
  AnalyticsCategories,
  AnalyticsTopAuthors,
  AnalyticsKeywordCloud,
  AnalyticsCitationNetwork,
} from "~/composables/useApi";

definePageMeta({ layout: "default" });
const { t } = useTranslation();
const api = useApi();

useHead({
  title: "Analytics — Kaleidoscope",
  meta: [{ name: "description", content: "Paper library analytics." }],
});

const overview = ref<AnalyticsOverview | null>(null);
const timeline = ref<AnalyticsTimeline | null>(null);
const categories = ref<AnalyticsCategories | null>(null);
const topAuthors = ref<AnalyticsTopAuthors | null>(null);
const keywordCloud = ref<AnalyticsKeywordCloud | null>(null);
const citationNet = ref<AnalyticsCitationNetwork | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

async function loadData() {
  loading.value = true;
  error.value = null;
  try {
    const results = await Promise.allSettled([
      api.getAnalyticsOverview(),
      api.getAnalyticsTimeline(90),
      api.getAnalyticsCategories(15),
      api.getAnalyticsTopAuthors(10),
      api.getAnalyticsKeywordCloud(40),
      api.getAnalyticsCitationNetwork(),
    ]);
    const [ov, tl, cat, auth, kw, cn] = results;
    if (ov.status === "fulfilled") overview.value = ov.value;
    if (tl.status === "fulfilled") timeline.value = tl.value;
    if (cat.status === "fulfilled") categories.value = cat.value;
    if (auth.status === "fulfilled") topAuthors.value = auth.value;
    if (kw.status === "fulfilled") keywordCloud.value = kw.value;
    if (cn.status === "fulfilled") citationNet.value = cn.value;

    // If all failed, show error
    const allFailed = results.every((r) => r.status === "rejected");
    if (allFailed) {
      const firstError = results.find((r) => r.status === "rejected") as
        | PromiseRejectedResult
        | undefined;
      error.value =
        firstError?.reason?.message ||
        "Failed to load analytics — check backend connection";
    }
  } catch (e: any) {
    error.value = e?.message || "Failed to load analytics";
  } finally {
    loading.value = false;
  }
}
onMounted(loadData);

const maxCatCount = computed(() => {
  if (!categories.value?.categories.length) return 1;
  return Math.max(...categories.value.categories.map((c) => c.count));
});
const maxKwCount = computed(() => {
  if (!keywordCloud.value?.keywords.length) return 1;
  return Math.max(...keywordCloud.value.keywords.map((k) => k.count));
});
const timelinePath = computed(() => {
  if (!timeline.value?.points.length) return "";
  const pts = timeline.value.points;
  const maxVal = Math.max(...pts.map((p) => p.count), 1);
  const w = 100 / (pts.length - 1 || 1);
  return pts
    .map((p, i) => {
      const x = i * w;
      const y = 100 - (p.count / maxVal) * 80;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
});
const statusColors: Record<string, string> = {
  parsed: "#22c55e",
  enriched: "#3b82f6",
  discovered: "#f59e0b",
  indexed: "#8b5cf6",
  failed: "#ef4444",
  parse_failed: "#ef4444",
};
function kwSize(count: number): string {
  const r = count / (maxKwCount.value || 1);
  return `${(0.75 + r * 1.5).toFixed(2)}rem`;
}
const kwColors = [
  "#8b5cf6",
  "#3b82f6",
  "#06b6d4",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#ec4899",
  "#6366f1",
  "#14b8a6",
  "#f97316",
];
</script>

<template>
  <div class="ks-analytics">
    <KsPageHeader title="Analytics" subtitle="Paper library insights" />

    <div v-if="loading" class="ks-analytics__loading">
      <div class="ks-analytics__spinner" />
      <p>Loading analytics…</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="ks-analytics__error">
      <p class="ks-analytics__error-text">⚠ {{ error }}</p>
      <button class="ks-analytics__retry-btn" @click="loadData">Retry</button>
    </div>

    <div v-else class="ks-analytics__grid">
      <!-- ═══ Row 1: Overview Metrics ═══ -->
      <section v-if="overview" class="ks-card ks-card--wide">
        <h2 class="ks-card__title">Library Overview</h2>
        <div class="ks-metrics">
          <div class="ks-metric">
            <span class="ks-metric__value">{{ overview.total_papers }}</span>
            <span class="ks-metric__label">Total Papers</span>
          </div>
          <div class="ks-metric">
            <span class="ks-metric__value">{{ overview.with_fulltext }}</span>
            <span class="ks-metric__label">With Full Text</span>
          </div>
          <div class="ks-metric">
            <span class="ks-metric__value">{{ overview.total_authors }}</span>
            <span class="ks-metric__label">Authors</span>
          </div>
          <div class="ks-metric">
            <span class="ks-metric__value">{{
              overview.total_references
            }}</span>
            <span class="ks-metric__label">References</span>
          </div>
          <div class="ks-metric">
            <span class="ks-metric__value">{{
              overview.avg_citation_count
            }}</span>
            <span class="ks-metric__label">Avg Citations</span>
          </div>
        </div>
        <!-- Status breakdown -->
        <div class="ks-status-bar">
          <div
            v-for="[status, count] in Object.entries(overview.by_status)"
            :key="status"
            class="ks-status-bar__segment"
            :style="{
              flex: count,
              backgroundColor: statusColors[status] || '#64748b',
            }"
            :title="`${status}: ${count}`"
          />
        </div>
        <div class="ks-status-legend">
          <span
            v-for="[status, count] in Object.entries(overview.by_status)"
            :key="status"
            class="ks-status-legend__item"
          >
            <span
              class="ks-status-legend__dot"
              :style="{ backgroundColor: statusColors[status] || '#64748b' }"
            />
            {{ status }} ({{ count }})
          </span>
        </div>
      </section>

      <!-- ═══ Row 2: Timeline ═══ -->
      <section v-if="timeline?.points.length" class="ks-card">
        <h2 class="ks-card__title">Papers Over Time</h2>
        <svg
          viewBox="0 0 100 100"
          class="ks-chart-svg"
          preserveAspectRatio="none"
        >
          <defs>
            <linearGradient id="tl-grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#8b5cf6" stop-opacity="0.3" />
              <stop offset="100%" stop-color="#8b5cf6" stop-opacity="0" />
            </linearGradient>
          </defs>
          <path
            v-if="timelinePath"
            :d="timelinePath + ' L100,100 L0,100 Z'"
            fill="url(#tl-grad)"
          />
          <path
            v-if="timelinePath"
            :d="timelinePath"
            fill="none"
            stroke="#8b5cf6"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <div class="ks-chart-labels">
          <span>{{ timeline.points[0]?.date }}</span>
          <span>{{ timeline.points[timeline.points.length - 1]?.date }}</span>
        </div>
      </section>

      <!-- ═══ Categories ═══ -->
      <section v-if="categories?.categories.length" class="ks-card">
        <h2 class="ks-card__title">Categories</h2>
        <div class="ks-bar-chart">
          <div
            v-for="cat in categories.categories"
            :key="cat.name"
            class="ks-bar-row"
          >
            <span class="ks-bar-row__label">{{ cat.name }}</span>
            <div class="ks-bar-row__track">
              <div
                class="ks-bar-row__fill"
                :style="{ width: (cat.count / maxCatCount) * 100 + '%' }"
              />
            </div>
            <span class="ks-bar-row__count">{{ cat.count }}</span>
          </div>
        </div>
      </section>

      <!-- ═══ Top Authors ═══ -->
      <section v-if="topAuthors?.authors.length" class="ks-card">
        <h2 class="ks-card__title">Top Authors</h2>
        <table class="ks-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Author</th>
              <th>Papers</th>
              <th>Citations</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(a, i) in topAuthors.authors" :key="a.id">
              <td>{{ i + 1 }}</td>
              <td>{{ a.name }}</td>
              <td>{{ a.paper_count }}</td>
              <td>{{ a.total_citations }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- ═══ Keyword Cloud ═══ -->
      <section v-if="keywordCloud?.keywords.length" class="ks-card">
        <h2 class="ks-card__title">Keyword Cloud</h2>
        <div class="ks-keyword-cloud">
          <span
            v-for="(kw, i) in keywordCloud.keywords"
            :key="kw.keyword"
            class="ks-keyword"
            :style="{
              fontSize: kwSize(kw.count),
              color: kwColors[i % kwColors.length],
            }"
            >{{ kw.keyword }}</span
          >
        </div>
      </section>

      <!-- ═══ Citation Network ═══ -->
      <section v-if="citationNet" class="ks-card">
        <h2 class="ks-card__title">Citation Network</h2>
        <div class="ks-metrics ks-metrics--small">
          <div class="ks-metric">
            <span class="ks-metric__value">{{ citationNet.total_nodes }}</span>
            <span class="ks-metric__label">Nodes</span>
          </div>
          <div class="ks-metric">
            <span class="ks-metric__value">{{ citationNet.total_edges }}</span>
            <span class="ks-metric__label">Edges</span>
          </div>
          <div class="ks-metric">
            <span class="ks-metric__value">{{
              citationNet.resolved_edges
            }}</span>
            <span class="ks-metric__label">Resolved</span>
          </div>
          <div class="ks-metric">
            <span class="ks-metric__value">{{
              citationNet.avg_references_per_paper
            }}</span>
            <span class="ks-metric__label">Avg Refs/Paper</span>
          </div>
        </div>
        <div v-if="citationNet.top_cited.length" class="ks-top-cited">
          <h3 class="ks-top-cited__heading">Most Cited (Internal)</h3>
          <div
            v-for="tc in citationNet.top_cited"
            :key="tc.paper_id"
            class="ks-top-cited__item"
          >
            <NuxtLink :to="`/papers/${tc.paper_id}`" class="ks-top-cited__link">
              {{ tc.title }}
            </NuxtLink>
            <span class="ks-top-cited__count"
              >{{ tc.internal_citations }} cites</span
            >
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.ks-analytics {
  min-height: 100vh;
  padding-bottom: 80px;
}
.ks-analytics__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 120px 0;
  color: var(--color-secondary, #94a3b8);
}
.ks-analytics__spinner {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 3px solid var(--color-border, #334155);
  border-top-color: var(--color-primary, #8b5cf6);
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.ks-analytics__error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 120px 0;
}
.ks-analytics__error-text {
  font: 500 1rem/1.4 var(--font-sans, "Inter", sans-serif);
  color: var(--color-danger, #ef4444);
}
.ks-analytics__retry-btn {
  padding: 8px 24px;
  border-radius: 6px;
  border: 1px solid var(--color-primary, #8b5cf6);
  background: transparent;
  color: var(--color-primary, #8b5cf6);
  cursor: pointer;
  font: 500 0.85rem/1 var(--font-sans, "Inter", sans-serif);
  transition:
    background 0.2s,
    color 0.2s;
}
.ks-analytics__retry-btn:hover {
  background: var(--color-primary, #8b5cf6);
  color: #fff;
}

.ks-analytics__grid {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.ks-card {
  background: var(--color-surface, #1e293b);
  border-radius: 12px;
  padding: 24px;
  border: 1px solid var(--color-border, #334155);
}
.ks-card--wide {
  grid-column: 1 / -1;
}
.ks-card__title {
  font: 600 1rem/1.4 var(--font-sans, "Inter", sans-serif);
  color: var(--color-text, #f1f5f9);
  margin: 0 0 16px;
  letter-spacing: -0.01em;
}

/* ── Metrics ──────────────────────────────────── */
.ks-metrics {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.ks-metrics--small {
  margin-bottom: 16px;
}
.ks-metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.ks-metric__value {
  font: 700 1.75rem/1 var(--font-sans, "Inter", sans-serif);
  color: var(--color-primary, #8b5cf6);
}
.ks-metrics--small .ks-metric__value {
  font-size: 1.25rem;
}
.ks-metric__label {
  font: 500 0.75rem/1 var(--font-sans, "Inter", sans-serif);
  color: var(--color-secondary, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* ── Status bar ───────────────────────────────── */
.ks-status-bar {
  display: flex;
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 12px;
}
.ks-status-bar__segment {
  transition: flex 0.3s ease;
}
.ks-status-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font: 400 0.75rem/1 var(--font-sans, "Inter", sans-serif);
  color: var(--color-secondary, #94a3b8);
}
.ks-status-legend__item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.ks-status-legend__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* ── SVG Chart ────────────────────────────────── */
.ks-chart-svg {
  width: 100%;
  height: 120px;
  display: block;
}
.ks-chart-labels {
  display: flex;
  justify-content: space-between;
  font: 400 0.7rem/1 var(--font-mono, monospace);
  color: var(--color-secondary, #94a3b8);
  margin-top: 8px;
}

/* ── Bar chart ────────────────────────────────── */
.ks-bar-chart {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ks-bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ks-bar-row__label {
  width: 100px;
  flex-shrink: 0;
  text-align: right;
  font: 500 0.75rem/1.2 var(--font-mono, monospace);
  color: var(--color-text, #f1f5f9);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ks-bar-row__track {
  flex: 1;
  height: 16px;
  border-radius: 4px;
  background: var(--color-border, #334155);
}
.ks-bar-row__fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #8b5cf6, #3b82f6);
  transition: width 0.6s ease;
}
.ks-bar-row__count {
  width: 32px;
  font: 600 0.75rem/1 var(--font-mono, monospace);
  color: var(--color-secondary, #94a3b8);
}

/* ── Table ─────────────────────────────────────── */
.ks-table {
  width: 100%;
  border-collapse: collapse;
  font: 400 0.85rem/1.5 var(--font-sans, "Inter", sans-serif);
}
.ks-table th {
  text-align: left;
  padding: 8px 12px;
  font-weight: 600;
  color: var(--color-secondary, #94a3b8);
  border-bottom: 1px solid var(--color-border, #334155);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.ks-table td {
  padding: 8px 12px;
  color: var(--color-text, #f1f5f9);
  border-bottom: 1px solid var(--color-border, #1e293b);
}
.ks-table tr:hover td {
  background: rgba(139, 92, 246, 0.05);
}

/* ── Keyword cloud ─────────────────────────────── */
.ks-keyword-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  align-items: center;
  justify-content: center;
  padding: 12px 0;
}
.ks-keyword {
  font-weight: 600;
  opacity: 0.85;
  transition:
    opacity 0.2s,
    transform 0.2s;
  cursor: default;
}
.ks-keyword:hover {
  opacity: 1;
  transform: scale(1.1);
}

/* ── Top cited ──────────────────────────────────── */
.ks-top-cited {
  margin-top: 12px;
}
.ks-top-cited__heading {
  font: 600 0.8rem/1 var(--font-sans, "Inter", sans-serif);
  color: var(--color-secondary, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 12px;
}
.ks-top-cited__item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border, #1e293b);
}
.ks-top-cited__link {
  color: var(--color-primary, #8b5cf6);
  text-decoration: none;
  font-size: 0.85rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 12px;
}
.ks-top-cited__link:hover {
  text-decoration: underline;
}
.ks-top-cited__count {
  font: 600 0.75rem/1 var(--font-mono, monospace);
  color: var(--color-secondary, #94a3b8);
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .ks-analytics__grid {
    grid-template-columns: 1fr;
  }
  .ks-metrics {
    gap: 16px;
  }
}
</style>
