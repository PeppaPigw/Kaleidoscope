<script setup lang="ts">
/**
 * DeepXiv Trending — browse trending arXiv papers with configurable time range.
 * Enriches each paper with a brief (title, TLDR, keywords) fetched in parallel.
 */
import { Loader2, TrendingUp, RefreshCw } from 'lucide-vue-next'
import type { DeepXivTrendingPaper, DeepXivBriefResponse } from '~/composables/useDeepXiv'

definePageMeta({ layout: 'default', title: 'Trending Papers' })
useHead({ title: 'Trending Papers — DeepXiv' })

const { getTrending, getPaperBrief } = useDeepXiv()
const { apiFetch } = useApi()

// ── State ────────────────────────────────────────────────────
const days = ref(7)
const papers = ref<DeepXivTrendingPaper[]>([])
const briefs = ref<Record<string, DeepXivBriefResponse>>({})
const totalPapers = ref(0)
const isLoading = ref(true)
const isEnriching = ref(false)
const loadError = ref<string | null>(null)
const ingestStatus = ref<{ queued: number; skipped: number } | null>(null)
const isIngesting = ref(false)

// ── Load ─────────────────────────────────────────────────────
async function loadTrending() {
  isLoading.value = true
  loadError.value = null
  papers.value = []
  briefs.value = {}

  try {
    const res = await getTrending(days.value, 30)
    papers.value = res.papers ?? []
    totalPapers.value = res.total ?? papers.value.length
  }
  catch (err) {
    loadError.value = err instanceof Error ? err.message : 'Failed to load trending papers'
    papers.value = []
    totalPapers.value = 0
  }
  finally {
    isLoading.value = false
  }

  // Auto-ingest: queue new papers for local processing (fire-and-forget)
  if (papers.value.length > 0 && !loadError.value) {
    isIngesting.value = true
    ingestStatus.value = null
    apiFetch<{ queued: number; skipped: number; total: number }>(
      `/deepxiv/trending/ingest?days=${days.value}&limit=30`,
      { method: 'POST' },
    ).then((res) => {
      ingestStatus.value = { queued: res.queued, skipped: res.skipped }
    }).catch(() => {
      // Ingest failure is non-critical — silently ignore
    }).finally(() => {
      isIngesting.value = false
    })
  }

  // Enrich: fetch briefs for all papers in parallel batches
  if (papers.value.length > 0) {
    isEnriching.value = true
    const ids = papers.value.map(p => p.arxiv_id).filter(Boolean) as string[]
    // Batch into groups of 8 to avoid overwhelming the API
    const BATCH = 8
    for (let i = 0; i < ids.length; i += BATCH) {
      const batch = ids.slice(i, i + BATCH)
      const results = await Promise.allSettled(batch.map(id => getPaperBrief(id)))
      results.forEach((r, j) => {
        if (r.status === 'fulfilled' && r.value) {
          briefs.value[batch[j]!] = r.value
        }
      })
    }
    isEnriching.value = false
  }
}

function handleCardClick(paper: DeepXivTrendingPaper) {
  navigateTo(`/deepxiv/papers/${paper.arxiv_id}`)
}

watch(days, () => { void loadTrending() })
onMounted(() => { void loadTrending() })
</script>

<template>
  <div class="ks-dxt">
    <!-- Header -->
    <header class="ks-dxt__header">
      <div class="ks-dxt__header-left">
        <TrendingUp :size="22" class="ks-dxt__header-icon" />
        <div>
          <h1 class="ks-dxt__title">Trending Papers</h1>
          <p class="ks-dxt__subtitle">
            Popular arXiv papers over the last <strong>{{ days }} days</strong>
            <span v-if="!isLoading && papers.length > 0" class="ks-dxt__count-inline">
              · {{ totalPapers }} papers
            </span>
          </p>
        </div>
      </div>
      <div class="ks-dxt__controls">
        <DeepxivDayRangeSelector v-model="days" />
        <button
          type="button"
          class="ks-dxt__refresh"
          :disabled="isLoading"
          :aria-label="isLoading ? 'Loading…' : 'Refresh'"
          @click="loadTrending"
        >
          <RefreshCw :size="15" :class="{ 'ks-dxt__spinning': isLoading }" />
        </button>
      </div>
    </header>

    <!-- Error -->
    <div v-if="loadError" class="ks-dxt__error">
      <strong>Error:</strong> {{ loadError }}
    </div>

    <!-- Loading skeleton -->
    <div v-if="isLoading" class="ks-dxt__grid">
      <div v-for="n in 12" :key="n" class="ks-dxt__skeleton">
        <div class="ks-dxt__sk-rank" />
        <div class="ks-dxt__sk-body">
          <div class="ks-dxt__sk-title" />
          <div class="ks-dxt__sk-text" />
          <div class="ks-dxt__sk-meta" />
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="papers.length === 0 && !loadError" class="ks-dxt__empty">
      <TrendingUp :size="40" :stroke-width="1.2" class="ks-dxt__empty-icon" />
      <p class="ks-dxt__empty-title">No trending papers found</p>
      <p class="ks-dxt__empty-hint">Try a different time range or check back later.</p>
    </div>

    <!-- Paper grid -->
    <template v-else>
      <!-- Enriching progress hint -->
      <div v-if="isEnriching" class="ks-dxt__enriching">
        <Loader2 :size="14" class="ks-dxt__spinning" />
        Fetching paper details…
      </div>

      <!-- Ingest status -->
      <div v-if="isIngesting" class="ks-dxt__ingest-status ks-dxt__ingest-status--loading">
        <Loader2 :size="13" class="ks-dxt__spinning" />
        Queuing papers for local processing…
      </div>
      <div v-else-if="ingestStatus" class="ks-dxt__ingest-status">
        <span v-if="ingestStatus.queued > 0">
          {{ ingestStatus.queued }} new paper{{ ingestStatus.queued !== 1 ? 's' : '' }} added to processing queue
        </span>
        <span v-else>All papers already in local library</span>
      </div>

      <div class="ks-dxt__grid">
        <DeepxivTrendingCard
          v-for="(paper, i) in papers"
          :key="paper.arxiv_id"
          :paper="paper"
          :brief="briefs[paper.arxiv_id]"
          :rank="i + 1"
          @click="handleCardClick(paper)"
        />
      </div>

      <div class="ks-dxt__footer">
        <span class="ks-dxt__footer-count">
          Showing {{ papers.length }} of {{ totalPapers }} trending papers
        </span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.ks-dxt {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ─── Header ────────────────────────────────────────── */
.ks-dxt__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.ks-dxt__header-left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.ks-dxt__header-icon {
  flex-shrink: 0;
  color: var(--color-primary);
  margin-top: 3px;
}

.ks-dxt__title {
  font: 700 1.625rem / 1.1 var(--font-display);
  color: var(--color-text);
  margin: 0 0 4px;
  letter-spacing: -0.03em;
}

.ks-dxt__subtitle {
  font: 400 0.8125rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
}

.ks-dxt__count-inline {
  opacity: 0.7;
}

.ks-dxt__controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.ks-dxt__refresh {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  background: none;
  border: 1.5px solid var(--color-border);
  border-radius: 6px;
  color: var(--color-secondary);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.ks-dxt__refresh:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.ks-dxt__refresh:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ─── Enriching notice ──────────────────────────────── */
.ks-dxt__enriching {
  display: flex;
  align-items: center;
  gap: 8px;
  font: 400 0.8125rem / 1 var(--font-sans);
  color: var(--color-secondary);
  opacity: 0.75;
}

/* ─── Ingest status ─────────────────────────────────── */
.ks-dxt__ingest-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font: 400 0.75rem / 1 var(--font-mono);
  color: var(--color-secondary);
  opacity: 0.6;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.ks-dxt__ingest-status--loading {
  opacity: 0.45;
}

/* ─── Error ─────────────────────────────────────────── */
.ks-dxt__error {
  padding: 12px 16px;
  border-left: 3px solid #dc2626;
  background: rgba(220, 38, 38, 0.06);
  border-radius: 0 6px 6px 0;
  font: 400 0.875rem / 1.4 var(--font-sans);
  color: #dc2626;
}

/* ─── Grid ──────────────────────────────────────────── */
.ks-dxt__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 12px;
}

/* ─── Skeleton ──────────────────────────────────────── */
@keyframes ks-dxt-shimmer {
  0% { background-position: -200% center; }
  100% { background-position: 200% center; }
}

.ks-dxt__skeleton {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

.ks-dxt__sk-rank {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(90deg, var(--color-border) 25%, rgba(255,255,255,0.08) 50%, var(--color-border) 75%);
  background-size: 200% 100%;
  animation: ks-dxt-shimmer 1.4s infinite;
}

.ks-dxt__sk-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ks-dxt__sk-title,
.ks-dxt__sk-text,
.ks-dxt__sk-meta {
  border-radius: 4px;
  background: linear-gradient(90deg, var(--color-border) 25%, rgba(255,255,255,0.08) 50%, var(--color-border) 75%);
  background-size: 200% 100%;
  animation: ks-dxt-shimmer 1.4s infinite;
}

.ks-dxt__sk-title { height: 18px; width: 88%; }
.ks-dxt__sk-text { height: 14px; width: 100%; }
.ks-dxt__sk-meta { height: 12px; width: 55%; }

/* ─── Spinner ───────────────────────────────────────── */
.ks-dxt__spinning {
  animation: ks-dxt-spin 0.8s linear infinite;
}

@keyframes ks-dxt-spin {
  to { transform: rotate(360deg); }
}

/* ─── Empty state ───────────────────────────────────── */
.ks-dxt__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 80px 40px;
  text-align: center;
  background: var(--color-surface);
  border: 1px dashed var(--color-border);
  border-radius: 10px;
}

.ks-dxt__empty-icon {
  color: var(--color-secondary);
  opacity: 0.35;
}

.ks-dxt__empty-title {
  font: 600 1.125rem / 1 var(--font-display);
  color: var(--color-text);
  margin: 0;
}

.ks-dxt__empty-hint {
  font: 400 0.875rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
}

/* ─── Footer ────────────────────────────────────────── */
.ks-dxt__footer {
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
  text-align: center;
}

.ks-dxt__footer-count {
  font: 400 0.75rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-secondary);
}

/* ─── Responsive ────────────────────────────────────── */
@media (max-width: 768px) {
  .ks-dxt__grid {
    grid-template-columns: 1fr;
  }
  .ks-dxt__header {
    flex-direction: column;
  }
}
</style>
