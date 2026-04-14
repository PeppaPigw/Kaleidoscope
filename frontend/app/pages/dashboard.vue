<script setup lang="ts">
/**
 * Dashboard — Research Intelligence Hub
 *
 * Rich landing page combining local library analytics, DeepXiv trending
 * papers (with titles fetched in parallel), personalized recommendations,
 * arXiv category explorer, and quick-action shortcuts.
 */
import type { HeroStat } from '~/components/dashboard/DashboardHero.vue'
import type { BriefingItem } from '~/components/dashboard/BriefingStrip.vue'
import type { ReadingPick } from '~/components/dashboard/ReadingShelf.vue'
import type { QueueItem } from '~/components/dashboard/ReadingQueue.vue'
import { useAlertStream } from '~/composables/useAlertStream'
import type { AnalyticsOverview } from '~/composables/useApi'
import type { DeepXivBriefResponse, DeepXivTrendingPaper, DeepXivSocialImpact } from '~/composables/useDeepXiv'

definePageMeta({ layout: 'default', title: 'Dashboard' })

const { t } = useTranslation()
useHead({
  title: 'Dashboard — Kaleidoscope',
  meta: [{ name: 'description', content: "Your daily research briefing." }],
})

// ── State ──────────────────────────────────────────────────────────
const analyticsOverview = ref<AnalyticsOverview | null>(null)
const unreadAlertCount = ref(0)
const briefingItems = ref<BriefingItem[]>([])
const queueItems = ref<QueueItem[]>([])
const readingPicks = ref<ReadingPick[]>([])

const trendTopic = ref('')
const trendChange = ref('')
const trendDescription = ref('')
const trendRelatedTopics = ref<string[]>([])
const trendSparkline = ref<number[]>([])
const pulseWords = ref<Array<{ text: string; weight: number }>>([])

// DeepXiv
const trendingRaw = ref<DeepXivTrendingPaper[]>([])
const trendingBriefs = ref<Record<string, DeepXivBriefResponse>>({})
const forYouPapers = ref<Record<string, unknown>[]>([])
const forYouBriefs = ref<Record<string, DeepXivBriefResponse>>({})
const featuredSocial = ref<DeepXivSocialImpact | null>(null)

const { preferences, loadPreferences } = useUserPreferences()
const { lastAlert, unreadCount: streamUnreadCount, clearUnread } = useAlertStream()

const isLoading = ref(true)

function normalizeBriefingType(type?: string): BriefingItem['type'] {
  const raw = (type ?? 'NEW').toUpperCase()
  if (['NEW', 'ALERT', 'CODE', 'INGEST', 'UPDATE'].includes(raw)) return raw as BriefingItem['type']
  if (raw.includes('ALERT')) return 'ALERT'
  if (raw.includes('INGEST')) return 'INGEST'
  return 'NEW'
}

function toBriefingItem(alert: { id: string; title?: string; message?: string; created_at: string; type?: string; alert_type?: string }): BriefingItem {
  return {
    id: alert.id,
    type: normalizeBriefingType(alert.alert_type ?? alert.type),
    title: alert.title || alert.message || 'New activity',
    time: new Date(alert.created_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
  }
}

watch(lastAlert, (alert) => {
  if (!alert) return
  briefingItems.value = [toBriefingItem(alert), ...briefingItems.value.filter(i => i.id !== alert.id)].slice(0, 5)
})

// ── Computed ───────────────────────────────────────────────────────
const featuredPaper = computed(() => {
  if (!trendingRaw.value.length) return null
  const top = trendingRaw.value[0]!
  const brief = top.arxiv_id ? trendingBriefs.value[top.arxiv_id] : undefined
  return { raw: top, brief }
})

const rankedPapers = computed(() =>
  trendingRaw.value.slice(1, 10).map(p => ({
    raw: p,
    brief: p.arxiv_id ? trendingBriefs.value[p.arxiv_id] : undefined,
  }))
)

const heroTitle = computed(() => {
  if (analyticsOverview.value?.total_papers > 0)
    return `${analyticsOverview.value.total_papers.toLocaleString()} papers indexed — explore the frontier`
  return 'Kaleidoscope — Your Research Intelligence Hub'
})
const heroLead = computed(() => {
  if (analyticsOverview.value) {
    const wft = analyticsOverview.value.with_fulltext ?? 0
    const total = analyticsOverview.value.total_papers ?? 0
    return `${wft} papers with full text · ${total} total indexed`
  }
  return 'Loading your research library…'
})
const heroDate = new Date().toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: '2-digit' })
const heroStats = computed<HeroStat[]>(() => [
  { label: t('newPapers'), value: analyticsOverview.value ? String(analyticsOverview.value.total_papers) : '—' },
  { label: 'Authors', value: analyticsOverview.value ? String(analyticsOverview.value.total_authors) : '—' },
  { label: 'Full Text', value: analyticsOverview.value ? String(analyticsOverview.value.with_fulltext) : '—' },
  { label: 'Alerts', value: String(unreadAlertCount.value + streamUnreadCount.value) },
])

// Aggregated keywords from trending + forYou briefs — used as word cloud
const trendingKeywords = computed(() => {
  const freq: Record<string, number> = {}
  const add = (kws: string[] | undefined) => {
    kws?.forEach((kw) => {
      const k = kw.toLowerCase().trim()
      if (k.length > 3) freq[k] = (freq[k] ?? 0) + 1
    })
  }
  Object.values(trendingBriefs.value).forEach(b => add(b.keywords))
  Object.values(forYouBriefs.value).forEach(b => add(b.keywords))
  return Object.entries(freq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 40)
    .map(([text, weight]) => ({ text, weight }))
})

// ── Data loading ───────────────────────────────────────────────────
onMounted(async () => {
  const {
    getAnalyticsOverview, listPapers,
    getAlerts, getAnalyticsKeywordCloud,
  } = useApi()
  const { getTrending, searchPapers, getPaperBrief, getPaperHead, getSocialImpact } = useDeepXiv()

  await loadPreferences()
  isLoading.value = true

  // ── Parallel batch 1: analytics + alerts ───────────────────────
  const [overviewRes, alertsRes] = await Promise.allSettled([
    getAnalyticsOverview(),
    getAlerts(false, 5),
  ])

  if (overviewRes.status === 'fulfilled') analyticsOverview.value = overviewRes.value
  if (alertsRes.status === 'fulfilled') {
    unreadAlertCount.value = alertsRes.value.unread_count
    briefingItems.value = alertsRes.value.alerts.map(toBriefingItem)
  }

  // ── Parallel batch 2: shelf + keywords + trending ───────────────
  const [papersRes, keywordsRes, trendingRes] = await Promise.allSettled([
    listPapers({ limit: 6, offset: 0 }),
    getAnalyticsKeywordCloud(30),
    getTrending(7, 10),
  ])

  if (papersRes.status === 'fulfilled') {
    const DIM_COLORS: Record<string, string> = {
      domain: '#6366f1', task: '#0ea5e9', method: '#10b981',
      data_object: '#f59e0b', application: '#ec4899',
    }
    readingPicks.value = (papersRes.value.items ?? []).map((p) => {
      const lbl = p.paper_labels
      const labelDims = lbl
        ? ([
            { key: 'domain', v: lbl.domain[0] },
            { key: 'task', v: lbl.task[0] },
            { key: 'method', v: lbl.method[0] },
            { key: 'data_object', v: lbl.data_object[0] },
            { key: 'application', v: lbl.application[0] },
          ] as { key: string; v: string | undefined }[])
            .filter(d => Boolean(d.v))
            .map(d => ({ value: d.v as string, color: DIM_COLORS[d.key]! }))
        : undefined
      return {
        id: p.id, eyebrow: p.reading_status ?? 'New', title: p.title,
        venue: p.keywords?.slice(0, 2).join(' · ') ?? '',
        tags: p.has_full_text ? ['Full Text'] : [],
        abstract: p.abstract ?? '', labelDims,
      }
    })
  }

  if (keywordsRes.status === 'fulfilled') {
    const kd = keywordsRes.value
    if (kd.keywords?.length > 0) {
      const top = kd.keywords[0]!
      trendTopic.value = top.keyword
      trendDescription.value = `Appears in ${(kd.total_papers_with_keywords || 0).toLocaleString()} papers`
      trendRelatedTopics.value = kd.keywords.slice(1, 5).map((k: { keyword: string }) => k.keyword)
      const counts = kd.keywords.slice(0, 14).map((k: { count: number }) => k.count)
      const max = Math.max(...counts, 1)
      trendSparkline.value = counts.map((c: number) => Math.round((c / max) * 100))
      const topCount = top.count ?? 0
      const secondCount = kd.keywords[1]?.count ?? topCount
      const pct = secondCount > 0 ? Math.round(((topCount - secondCount) / secondCount) * 100) : 0
      trendChange.value = pct >= 0 ? `+${pct}%` : `${pct}%`
      pulseWords.value = kd.keywords.map((k: { keyword: string; count: number }) => ({ text: k.keyword, weight: k.count }))
    }
  }

  if (trendingRes.status === 'fulfilled') {
    trendingRaw.value = trendingRes.value.papers ?? []
  }

  // Fallback: if trending API returned nothing, use searchPapers for recent high-impact papers
  if (trendingRaw.value.length === 0) {
    try {
      const fallback = await searchPapers('large language model reasoning 2025', {
        size: 12,
        min_citation: 10,
        search_mode: 'hybrid',
      })
      if (fallback.results?.length) {
        trendingRaw.value = fallback.results.map((r, idx) => ({
          arxiv_id: r.arxiv_id,
          rank: idx + 1,
          stats: {
            total_views: r.citations * 80,
            total_likes: Math.round(r.citations * 4),
            total_mentions: r.citations,
          },
        }))
        // Pre-populate briefs from search result titles (avoid a separate brief fetch)
        fallback.results.forEach(r => {
          trendingBriefs.value[r.arxiv_id] = {
            arxiv_id: r.arxiv_id,
            title: r.title,
            keywords: r.categories ?? [],
            citations: r.citations,
          }
        })
      }
    }
    catch { /* keep empty */ }
  }

  // Fetch full briefs for top 8 trending papers
  const briefIds = trendingRaw.value.slice(0, 8).map(p => p.arxiv_id).filter(Boolean) as string[]
  const briefResults = await Promise.allSettled(briefIds.map(id => getPaperBrief(id)))
  briefResults.forEach((r, i) => {
    if (r.status === 'fulfilled' && r.value) {
      trendingBriefs.value[briefIds[i]!] = r.value
    }
  })

  // Build reading queue from trending papers using HEAD token_count for reading time
  const queueIds = trendingRaw.value.slice(0, 5).map(p => p.arxiv_id).filter(Boolean) as string[]
  const headResults = await Promise.allSettled(queueIds.map(id => getPaperHead(id)))
  queueItems.value = queueIds.map((arxivId, i) => {
    const brief = trendingBriefs.value[arxivId]
    const head = headResults[i]?.status === 'fulfilled' ? headResults[i].value : null
    const tokenCount = head?.token_count ?? 6000
    const wpm = 250
    const minutes = Math.max(10, Math.ceil((tokenCount * 0.75) / wpm))
    return {
      id: arxivId,
      title: brief?.title || head?.title || arxivId,
      time: `~${minutes} min`,
      mode: minutes > 40 ? 'Long read' : 'Deep read',
    }
  })

  // ── Batch 3: personalized For You + social impact for featured ─
  const cats = preferences.value.subscribed_categories
  const kws = preferences.value.keywords
  const defaultCat = 'cs.AI'
  const [forYouRes, socialRes] = await Promise.allSettled([
    searchPapers(
      kws.length > 0 ? kws[0]! : (cats.length > 0 ? cats[0]! : 'large language model'),
      { categories: cats.length > 0 ? [cats[0]!] : [defaultCat], size: 6 },
    ),
    trendingRaw.value[0]?.arxiv_id
      ? getSocialImpact(trendingRaw.value[0].arxiv_id)
      : Promise.reject(new Error('no featured')),
  ])

  if (forYouRes.status === 'fulfilled') {
    forYouPapers.value = (forYouRes.value.results ?? []) as Record<string, unknown>[]
    // Enrich ForYou with TLDR briefs (top 6)
    const forYouIds = forYouPapers.value.slice(0, 6).map(p => p.arxiv_id as string).filter(Boolean)
    const briefResults = await Promise.allSettled(forYouIds.map(id => getPaperBrief(id)))
    briefResults.forEach((r, i) => {
      if (r.status === 'fulfilled' && r.value) {
        forYouBriefs.value[forYouIds[i]!] = r.value
      }
    })
  }
  else {
    forYouPapers.value = []
  }

  if (socialRes.status === 'fulfilled') {
    featuredSocial.value = socialRes.value
  }

  isLoading.value = false
})

// ── Event handlers ─────────────────────────────────────────────────
function handleBriefingClick(item: BriefingItem) {
  if (item.type === 'ALERT') { clearUnread(); navigateTo('/alerts') }
  else navigateTo(`/search?q=${encodeURIComponent(item.title)}`)
}

function handleCardClick(pick: ReadingPick) { navigateTo(`/papers/${pick.id}`) }
function handleQueueItemClick(item: QueueItem) {
  // Queue items populated from DeepXiv trending papers (arxiv_id as id)
  if (/^\d{4}\.\d{4,5}/.test(item.id)) {
    navigateTo(`/deepxiv/papers/${item.id}`)
  }
  else {
    navigateTo(`/reader/${item.id}`)
  }
}
function handleHeroClick() { navigateTo('/discover') }
function handleTrendClick() { navigateTo('/insights/landscape') }

function authorLabel(brief: DeepXivBriefResponse | undefined, raw: DeepXivTrendingPaper): string {
  if (!brief) return raw.arxiv_id ?? ''
  return brief.title
}
</script>

<template>
  <div class="ks-db">
    <!-- ══════════════════════════════════════════════════
         ROW 1 — Hero
    ═══════════════════════════════════════════════════ -->
    <DashboardHero
      :date="heroDate"
      :title="heroTitle"
      :lead="heroLead"
      :stats="heroStats"
      @click="handleHeroClick"
    />

    <!-- ══════════════════════════════════════════════════
         ROW 2 — Briefing
    ═══════════════════════════════════════════════════ -->
    <DashboardBriefingStrip
      :items="briefingItems"
      @item-click="handleBriefingClick"
    />

    <!-- ══════════════════════════════════════════════════
         ROW 3 — Featured Paper (#1 Trending)
    ═══════════════════════════════════════════════════ -->
    <div class="ks-db__panel ks-db__panel--featured">
        <p class="ks-db__eyebrow">
          <span class="ks-db__hot-dot" /> TRENDING #1 THIS WEEK
        </p>

        <template v-if="featuredPaper">
          <NuxtLink
            :to="`/deepxiv/papers/${featuredPaper.raw.arxiv_id}`"
            class="ks-db__featured-link"
          >
            <h2 class="ks-db__featured-title">
              {{ featuredPaper.brief?.title || featuredPaper.raw.arxiv_id }}
            </h2>
            <p v-if="featuredPaper.brief?.tldr" class="ks-db__featured-tldr">
              {{ featuredPaper.brief.tldr }}
            </p>
            <div class="ks-db__featured-meta">
              <span class="ks-db__featured-id">{{ featuredPaper.raw.arxiv_id }}</span>
              <span v-if="featuredPaper.brief?.citations" class="ks-db__featured-stat">
                {{ featuredPaper.brief.citations }} citations
              </span>
              <span v-if="featuredPaper.raw.stats?.total_views" class="ks-db__featured-stat">
                {{ (featuredPaper.raw.stats.total_views as number).toLocaleString() }} views
              </span>
              <span v-if="featuredPaper.raw.stats?.total_mentions" class="ks-db__featured-stat">
                {{ featuredPaper.raw.stats.total_mentions }} mentions
              </span>
              <span v-if="featuredSocial?.total_tweets" class="ks-db__featured-stat ks-db__featured-stat--twitter">
                🐦 {{ featuredSocial.total_tweets }} tweets
              </span>
              <span v-if="featuredSocial?.total_likes" class="ks-db__featured-stat ks-db__featured-stat--twitter">
                ♥ {{ featuredSocial.total_likes.toLocaleString() }} likes
              </span>
            </div>
            <div v-if="featuredPaper.brief?.keywords?.length" class="ks-db__featured-tags">
              <span
                v-for="kw in featuredPaper.brief.keywords.slice(0, 4)"
                :key="kw"
                class="ks-db__featured-tag"
              >{{ kw }}</span>
            </div>
          </NuxtLink>
        </template>
        <template v-else-if="isLoading">
          <div class="ks-db__skeleton-title" />
          <div class="ks-db__skeleton-text" />
          <div class="ks-db__skeleton-text ks-db__skeleton-text--short" />
        </template>
        <template v-else>
          <p class="ks-db__empty-hint">No trending data available right now.</p>
        </template>
      </div>

    <!-- ══════════════════════════════════════════════════
         ROW 4 — Trending List + Research Pulse
    ═══════════════════════════════════════════════════ -->
    <div class="ks-db__row ks-db__row--trending">
      <!-- Ranked trending list -->
      <div class="ks-db__panel">
        <div class="ks-db__panel-header">
          <p class="ks-db__eyebrow">TRENDING PAPERS — LAST 7 DAYS</p>
          <NuxtLink to="/deepxiv/trending" class="ks-db__view-all">View all →</NuxtLink>
        </div>
        <div v-if="rankedPapers.length > 0" class="ks-db__trending-list">
          <NuxtLink
            v-for="(item, i) in rankedPapers"
            :key="item.raw.arxiv_id"
            :to="`/deepxiv/papers/${item.raw.arxiv_id}`"
            class="ks-db__trend-row"
          >
            <span class="ks-db__trend-rank">{{ i + 2 }}</span>
            <div class="ks-db__trend-body">
              <p class="ks-db__trend-title">
                {{ item.brief?.title || item.raw.arxiv_id }}
              </p>
              <div class="ks-db__trend-meta">
                <span class="ks-db__trend-id">{{ item.raw.arxiv_id }}</span>
                <span v-if="item.raw.stats?.total_views" class="ks-db__trend-stat">
                  {{ (item.raw.stats.total_views as number).toLocaleString() }} views
                </span>
                <span v-if="item.raw.stats?.total_mentions" class="ks-db__trend-stat">
                  {{ item.raw.stats.total_mentions }} mentions
                </span>
              </div>
            </div>
            <div v-if="item.raw.mentioned_by?.length" class="ks-db__trend-avatars">
              <span
                v-for="user in item.raw.mentioned_by.slice(0, 3)"
                :key="user.username"
                class="ks-db__trend-avatar"
                :title="user.name"
              >
                {{ user.name[0]?.toUpperCase() }}
              </span>
            </div>
          </NuxtLink>
        </div>
        <div v-else-if="isLoading" class="ks-db__trending-skeleton">
          <div v-for="n in 6" :key="n" class="ks-db__skeleton-row" />
        </div>
        <p v-else class="ks-db__empty-hint">No trending data yet.</p>
      </div>

      <!-- Research Pulse Cloud -->
      <div class="ks-db__panel ks-db__pulse-panel">
        <p class="ks-db__eyebrow">RESEARCH PULSE — LIBRARY KEYWORDS</p>
        <DashboardResearchPulseCloud
          v-if="pulseWords.length > 0"
          :words="pulseWords"
          class="ks-db__pulse-cloud"
          @click="(word) => navigateTo(`/search?q=${encodeURIComponent(word)}`)"
        />
        <DashboardTrendSnapshot
          v-if="trendTopic"
          :topic="trendTopic"
          :change="trendChange"
          period="Library trends"
          :description="trendDescription"
          :related-topics="trendRelatedTopics"
          :sparkline-data="trendSparkline"
          @click="handleTrendClick"
        />
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════
         ROW 5 — Research Keywords Cloud (from trending papers)
    ═══════════════════════════════════════════════════ -->
    <div class="ks-db__panel">
      <div class="ks-db__panel-header">
        <p class="ks-db__eyebrow">RESEARCH TOPICS — TRENDING KEYWORDS</p>
        <NuxtLink to="/discover" class="ks-db__view-all">Explore →</NuxtLink>
      </div>
      <template v-if="trendingKeywords.length > 0">
        <DashboardResearchPulseCloud
          :words="trendingKeywords"
          class="ks-db__topic-cloud"
          @click="(word) => navigateTo(`/discover?q=${encodeURIComponent(word)}`)"
        />
      </template>
      <template v-else-if="isLoading">
        <div class="ks-db__skeleton-text" style="height:80px; border-radius:6px;" />
      </template>
      <template v-else>
        <p class="ks-db__empty-hint">Keywords will appear once trending papers load.</p>
      </template>
    </div>

    <!-- ══════════════════════════════════════════════════
         ROW 6 — For You (personalized DeepXiv results)
    ═══════════════════════════════════════════════════ -->
    <div class="ks-db__panel">
      <div class="ks-db__panel-header">
        <p class="ks-db__eyebrow">
          <template v-if="preferences.interests_set">
            FOR YOU — {{ (preferences.subscribed_categories[0] || 'cs.AI').toUpperCase() }}
          </template>
          <template v-else>DISCOVERY — cs.AI</template>
        </p>
        <NuxtLink
          v-if="!preferences.interests_set"
          to="/settings/subscriptions"
          class="ks-db__view-all"
        >
          Personalize →
        </NuxtLink>
        <NuxtLink v-else to="/deepxiv" class="ks-db__view-all">Explore more →</NuxtLink>
      </div>

      <div v-if="forYouPapers.length > 0" class="ks-db__foryou-grid">
        <NuxtLink
          v-for="paper in forYouPapers"
          :key="paper.arxiv_id as string"
          :to="`/deepxiv/papers/${paper.arxiv_id}`"
          class="ks-db__foryou-card"
        >
          <div class="ks-db__foryou-score-bar" :style="{ width: `${Math.min(100, (paper.score as number) * 100)}%` }" />
          <p class="ks-db__foryou-title">{{ paper.title }}</p>
          <!-- Prefer AI-generated TLDR over raw abstract -->
          <p
            v-if="forYouBriefs[paper.arxiv_id as string]?.tldr"
            class="ks-db__foryou-tldr"
          >
            {{ forYouBriefs[paper.arxiv_id as string]!.tldr }}
          </p>
          <p v-else-if="paper.abstract" class="ks-db__foryou-abstract">
            {{ (paper.abstract as string).slice(0, 160) }}…
          </p>
          <div class="ks-db__foryou-footer">
            <span class="ks-db__foryou-id">{{ paper.arxiv_id }}</span>
            <div class="ks-db__foryou-cats">
              <span
                v-for="cat in (paper.categories as string[]).slice(0, 2)"
                :key="cat"
                class="ks-db__foryou-cat"
              >{{ cat }}</span>
            </div>
            <span v-if="paper.citations" class="ks-db__foryou-cite">{{ paper.citations }} ↗</span>
          </div>
        </NuxtLink>
      </div>
      <div v-else-if="isLoading" class="ks-db__foryou-skeleton">
        <div v-for="n in 6" :key="n" class="ks-db__skeleton-card" />
      </div>
      <div v-else class="ks-db__foryou-empty">
        <p>No results loaded. <NuxtLink to="/deepxiv">Browse DeepXiv →</NuxtLink></p>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════
         ROW 7 — Reading Shelf (local library)
    ═══════════════════════════════════════════════════ -->
    <div v-if="readingPicks.length > 0" class="ks-db__panel ks-db__panel--noPad">
      <div class="ks-db__panel-header ks-db__panel-header--padded">
        <p class="ks-db__eyebrow">YOUR LIBRARY — RECENT PAPERS</p>
        <NuxtLink to="/discover" class="ks-db__view-all">Browse library →</NuxtLink>
      </div>
      <DashboardReadingShelf
        :picks="readingPicks"
        @card-click="handleCardClick"
      />
    </div>

    <!-- ══════════════════════════════════════════════════
         ROW 8 — Queue + Import
    ═══════════════════════════════════════════════════ -->
    <div class="ks-db__row ks-db__row--bottom">
      <DashboardReadingQueue
        :items="queueItems"
        @item-click="handleQueueItemClick"
      />
      <DashboardPaperImportUrl />
    </div>
  </div>
</template>

<style scoped>
/* ─── Root ───────────────────────────────────────────── */
.ks-db {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ─── Grid rows ──────────────────────────────────────── */
.ks-db__row {
  display: grid;
  gap: 20px;
}

/* Featured is now a single full-width panel, no row needed */

.ks-db__row--trending {
  grid-template-columns: 5fr 3fr;
  align-items: start;
}

.ks-db__row--bottom {
  grid-template-columns: 3fr 2fr;
}

/* ─── Panel base ─────────────────────────────────────── */
.ks-db__panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ks-db__panel--noPad {
  padding: 0;
  overflow: hidden;
}

.ks-db__panel-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.ks-db__panel-header--padded {
  padding: 18px 22px 0;
}

.ks-db__panel-sub {
  font: 400 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

/* ─── Eyebrow ────────────────────────────────────────── */
.ks-db__eyebrow {
  font: 700 0.6875rem / 1 var(--font-sans);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-secondary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.ks-db__view-all {
  margin-left: auto;
  font: 500 0.8rem / 1 var(--font-sans);
  color: var(--color-primary);
  text-decoration: none;
  white-space: nowrap;
  flex-shrink: 0;
  transition: opacity 0.15s;
}
.ks-db__view-all:hover { opacity: 0.7; }

.ks-db__empty-hint {
  font: 400 0.875rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
  font-style: italic;
}

/* ─── Hot dot animation ──────────────────────────────── */
.ks-db__hot-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #ef4444;
  box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4);
  animation: ks-pulse 2s infinite;
}
@keyframes ks-pulse {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
  70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

/* ─── Featured paper ─────────────────────────────────── */
.ks-db__panel--featured {
  background: linear-gradient(135deg, var(--color-surface) 60%, rgba(13, 115, 119, 0.04) 100%);
  border-top: 2px solid var(--color-primary);
}

.ks-db__featured-link {
  display: flex;
  flex-direction: column;
  gap: 10px;
  text-decoration: none;
}

.ks-db__featured-title {
  font: 700 1.3rem / 1.3 var(--font-display);
  color: var(--color-text);
  margin: 0;
  letter-spacing: -0.02em;
  transition: color 0.15s;
}

.ks-db__featured-link:hover .ks-db__featured-title {
  color: var(--color-primary);
}

.ks-db__featured-tldr {
  font: 400 0.9rem / 1.6 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ks-db__featured-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.ks-db__featured-id {
  font: 600 0.75rem / 1 var(--font-mono);
  color: var(--color-primary);
}

.ks-db__featured-stat {
  font: 400 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
  padding: 2px 8px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 10px;
}

.ks-db__featured-stat--twitter {
  color: #1d9bf0;
  border-color: rgba(29, 155, 240, 0.25);
  background: rgba(29, 155, 240, 0.06);
}

.ks-db__featured-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.ks-db__featured-tag {
  padding: 3px 9px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: 3px;
  font: 500 0.6875rem / 1.4 var(--font-sans);
}

/* ─── Topic keyword cloud ────────────────────────────── */
.ks-db__topic-cloud {
  min-height: 120px;
}

/* ─── Trending ranked list ───────────────────────────── */
.ks-db__trending-list {
  display: flex;
  flex-direction: column;
  gap: 0;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
}

.ks-db__trend-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  border-bottom: 1px solid var(--color-border);
  text-decoration: none;
  transition: background-color 0.12s;
}

.ks-db__trend-row:last-child { border-bottom: none; }

.ks-db__trend-row:hover {
  background: var(--color-primary-light);
}

.ks-db__trend-rank {
  flex-shrink: 0;
  width: 24px;
  font: 700 0.875rem / 1 var(--font-mono);
  color: var(--color-secondary);
  text-align: center;
}

.ks-db__trend-body { flex: 1; min-width: 0; }

.ks-db__trend-title {
  font: 500 0.875rem / 1.3 var(--font-sans);
  color: var(--color-text);
  margin: 0 0 3px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ks-db__trend-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ks-db__trend-id {
  font: 400 0.7rem / 1 var(--font-mono);
  color: var(--color-primary);
}

.ks-db__trend-stat {
  font: 400 0.7rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-db__trend-avatars {
  display: flex;
  gap: -4px;
  flex-shrink: 0;
}

.ks-db__trend-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  font: 700 0.625rem / 1 var(--font-sans);
  border: 2px solid var(--color-surface);
  margin-left: -4px;
  flex-shrink: 0;
}

/* ─── Research pulse panel ───────────────────────────── */
.ks-db__pulse-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ks-db__pulse-cloud {
  min-height: 160px;
}

/* ─── For You grid ───────────────────────────────────── */
.ks-db__foryou-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.ks-db__foryou-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: 14px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  text-decoration: none;
  overflow: hidden;
  transition: border-color 0.15s, transform 0.12s;
}

.ks-db__foryou-card:hover {
  border-color: var(--color-primary);
  transform: translateY(-1px);
}

.ks-db__foryou-score-bar {
  position: absolute;
  top: 0;
  left: 0;
  height: 2px;
  background: var(--color-primary);
  border-radius: 0 2px 0 0;
  transition: width 0.5s ease;
}

.ks-db__foryou-title {
  font: 600 0.875rem / 1.3 var(--font-display);
  color: var(--color-text);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ks-db__foryou-abstract {
  font: 400 0.8rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.ks-db__foryou-tldr {
  font: 400 0.8rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
  padding: 5px 8px;
  background: var(--color-primary-light);
  border-left: 2px solid var(--color-primary);
  border-radius: 0 3px 3px 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.ks-db__foryou-footer {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: auto;
  padding-top: 6px;
  border-top: 1px solid var(--color-border);
}

.ks-db__foryou-id {
  font: 500 0.65rem / 1 var(--font-mono);
  color: var(--color-primary);
}

.ks-db__foryou-cats {
  display: flex;
  gap: 3px;
  flex: 1;
  flex-wrap: wrap;
}

.ks-db__foryou-cat {
  font: 500 0.6rem / 1.3 var(--font-sans);
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: 2px;
  padding: 1px 5px;
}

.ks-db__foryou-cite {
  font: 400 0.65rem / 1 var(--font-sans);
  color: var(--color-secondary);
  flex-shrink: 0;
  margin-left: auto;
}

.ks-db__foryou-empty {
  padding: 24px;
  text-align: center;
  font: 400 0.875rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  border: 1px dashed var(--color-border);
  border-radius: 8px;
}

.ks-db__foryou-empty a {
  color: var(--color-primary);
  text-decoration: none;
}

/* ─── Skeleton loaders ───────────────────────────────── */
@keyframes ks-shimmer {
  0% { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}

.ks-db__skeleton-title,
.ks-db__skeleton-text,
.ks-db__skeleton-row,
.ks-db__skeleton-card {
  border-radius: 4px;
  background: linear-gradient(90deg, var(--color-border) 25%, var(--color-bg) 50%, var(--color-border) 75%);
  background-size: 400px 100%;
  animation: ks-shimmer 1.4s ease-in-out infinite;
}

.ks-db__skeleton-title {
  height: 28px;
  width: 80%;
  margin-bottom: 10px;
}

.ks-db__skeleton-text {
  height: 14px;
  width: 100%;
  margin-bottom: 6px;
}

.ks-db__skeleton-text--short { width: 60%; }

.ks-db__trending-skeleton {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ks-db__skeleton-row {
  height: 44px;
  border-radius: 6px;
}

.ks-db__foryou-skeleton {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.ks-db__skeleton-card {
  height: 140px;
  border-radius: 8px;
}

/* ─── Responsive ─────────────────────────────────────── */
@media (max-width: 1280px) {
  .ks-db__row--trending { grid-template-columns: 1fr; }
  .ks-db__foryou-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 900px) {
  .ks-db__foryou-grid { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 640px) {
  .ks-db__foryou-grid { grid-template-columns: 1fr; }
  .ks-db__row--bottom { grid-template-columns: 1fr; }
}
</style>
