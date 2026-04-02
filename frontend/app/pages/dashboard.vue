<script setup lang="ts">
/**
 * Dashboard Page — Morning Briefing Cover
 *
 * The researcher's daily landing page, styled like a magazine cover.
 * Composes dashboard-scoped components into a responsive grid layout.
 * All data is fetched from the real backend API.
 */
import type { HeroStat } from '~/components/dashboard/DashboardHero.vue'
import type { BriefingItem } from '~/components/dashboard/BriefingStrip.vue'
import type { ReadingPick } from '~/components/dashboard/ReadingShelf.vue'
import type { WorkspaceSummary } from '~/components/dashboard/ActiveWorkspacePanel.vue'
import type { QueueItem } from '~/components/dashboard/ReadingQueue.vue'
import type { MonitorItem } from '~/components/dashboard/MonitorRibbon.vue'
import { useAlertStream } from '~/composables/useAlertStream'
import type {
  AnalyticsOverview,
  HealthResponse,
  SearchHealthResponse,
} from '~/composables/useApi'

definePageMeta({
  layout: 'default',
  title: 'Dashboard',
})

const { t } = useTranslation()

useHead({
  title: 'Dashboard — Kaleidoscope',
  meta: [
    { name: 'description', content: "Your daily research briefing — today's theme, recommended papers, workspace progress, and system health." },
  ],
})

const analyticsOverview = ref<AnalyticsOverview | null>(null)
const healthData = ref<HealthResponse | null>(null)
const searchHealth = ref<SearchHealthResponse | null>(null)
const unreadAlertCount = ref(0)
const briefingItems = ref<BriefingItem[]>([])
const queueItems = ref<QueueItem[]>([])
const readingPicks = ref<ReadingPick[]>([])
const workspaces = ref<WorkspaceSummary[]>([])

// TrendSnapshot — driven by real hot-keywords API
const trendTopic = ref('Loading…')
const trendChange = ref('')
const trendDescription = ref('')
const trendRelatedTopics = ref<string[]>([])
const trendSparkline = ref<number[]>([])

const { lastAlert, unreadCount: streamUnreadCount, clearUnread } = useAlertStream()

function normalizeBriefingType(type?: string): BriefingItem['type'] {
  const raw = (type ?? 'NEW').toUpperCase()
  if (['NEW', 'ALERT', 'CODE', 'INGEST', 'UPDATE'].includes(raw)) {
    return raw as BriefingItem['type']
  }
  if (raw.includes('ALERT')) return 'ALERT'
  if (raw.includes('INGEST')) return 'INGEST'
  return 'NEW'
}

function toBriefingItem(alert: {
  id: string
  title?: string
  message?: string
  created_at: string
  type?: string
  alert_type?: string
}): BriefingItem {
  return {
    id: alert.id,
    type: normalizeBriefingType(alert.alert_type ?? alert.type),
    title: alert.title || alert.message || 'New activity',
    time: new Date(alert.created_at).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    }),
  }
}

watch(lastAlert, (alert) => {
  if (!alert) return
  briefingItems.value = [toBriefingItem(alert), ...briefingItems.value.filter(item => item.id !== alert.id)].slice(0, 5)
})

onMounted(async () => {
  const {
    getAnalyticsOverview, getHealth, getSearchHealth,
    listRecentPapers, listPapers, getAlerts, getAnalyticsKeywordCloud,
  } = useApi()

  try {
    analyticsOverview.value = await getAnalyticsOverview()
  } catch {
    analyticsOverview.value = null
  }

  try {
    healthData.value = await getHealth()
  } catch {
    healthData.value = null
  }

  try {
    searchHealth.value = await getSearchHealth()
  } catch {
    searchHealth.value = null
  }

  try {
    const alertsResp = await getAlerts(false, 5)
    unreadAlertCount.value = alertsResp.unread_count
    briefingItems.value = alertsResp.alerts.map(toBriefingItem)
  } catch {
    briefingItems.value = []
  }

  // Wire reading queue to recent papers
  try {
    const recent = await listRecentPapers()
    queueItems.value = recent.slice(0, 5)
  } catch {
    queueItems.value = []
  }

  // Wire reading shelf picks to newest papers
  try {
    const papersResp = await listPapers({ limit: 6, offset: 0 })
    readingPicks.value = (papersResp.items ?? []).map(p => ({
      id: p.id,
      eyebrow: p.reading_status ?? 'New',
      title: p.title,
      venue: p.keywords?.slice(0, 2).join(' · ') ?? '',
      tags: p.has_full_text ? ['Full Text'] : [],
      abstract: p.abstract ?? '',
    }))
  } catch {
    readingPicks.value = []
  }

  // Wire TrendSnapshot to real keyword-cloud API
  try {
    const keywordsData = await getAnalyticsKeywordCloud(20)
    if (keywordsData.keywords && keywordsData.keywords.length > 0) {
      const top = keywordsData.keywords[0]!
      trendTopic.value = top.keyword
      const total = keywordsData.total_papers_with_keywords || 0
      trendDescription.value = `Appears in ${total.toLocaleString()} papers in your library`
      trendRelatedTopics.value = keywordsData.keywords.slice(1, 5).map((k: { keyword: string }) => k.keyword)
      // Build sparkline from keyword counts (normalized)
      const counts = keywordsData.keywords.slice(0, 14).map((k: { count: number }) => k.count)
      const max = Math.max(...counts, 1)
      trendSparkline.value = counts.map((c: number) => Math.round((c / max) * 100))
      const topCount = top.count ?? 0
      const secondCount = keywordsData.keywords[1]?.count ?? topCount
      const pct = secondCount > 0 ? Math.round(((topCount - secondCount) / secondCount) * 100) : 0
      trendChange.value = pct >= 0 ? `+${pct}%` : `${pct}%`
    }
  } catch {
    // leave defaults (empty — no mock data)
  }
})

// heroTitle driven from analytics
const heroTitle = computed(() => {
  if (analyticsOverview.value && analyticsOverview.value.total_papers > 0) {
    return `${analyticsOverview.value.total_papers.toLocaleString()} papers indexed — explore the frontier`
  }
  return 'Kaleidoscope — Your Research Intelligence Hub'
})
const heroLead = computed(() => {
  if (analyticsOverview.value) {
    const wft = analyticsOverview.value.with_fulltext ?? 0
    const total = analyticsOverview.value.total_papers ?? 0
    return `${wft} papers with full text · ${total} total indexed · powered by MinerU + Qwen3`
  }
  return 'Fetching your research library…'
})
const heroDate = new Date().toLocaleDateString('en-US', {
  weekday: 'short',
  year: 'numeric',
  month: 'short',
  day: '2-digit',
})
const heroStats = computed<HeroStat[]>(() => [
  {
    label: t('newPapers'),
    value: analyticsOverview.value ? String(analyticsOverview.value.total_papers) : '—',
  },
  {
    label: 'Authors',
    value: analyticsOverview.value ? String(analyticsOverview.value.total_authors) : '—',
  },
  {
    label: 'Full Text',
    value: analyticsOverview.value ? String(analyticsOverview.value.with_fulltext) : '—',
  },
  {
    label: 'Alerts',
    value: String(unreadAlertCount.value + streamUnreadCount.value),
  },
])


const monitors = computed<MonitorItem[]>(() => {
  const items: MonitorItem[] = []

  if (healthData.value) {
    items.push({
      system: 'API Server',
      value: healthData.value.status === 'ok' ? '✓' : '✗',
      detail: `v${healthData.value.version ?? '?'}`,
      status: healthData.value.status === 'ok' ? 'ok' : 'error',
    })
  }

  if (searchHealth.value) {
    items.push({
      system: 'Keyword Search',
      value: searchHealth.value.keyword === 'ok' ? '✓' : '✗',
      detail: searchHealth.value.keyword === 'ok' ? 'Meilisearch connected' : 'unavailable',
      status: searchHealth.value.keyword === 'ok' ? 'ok' : 'warning',
    })
    items.push({
      system: 'Semantic Search',
      value: searchHealth.value.semantic === 'ok' ? '✓' : '✗',
      detail: searchHealth.value.semantic === 'ok' ? 'Qdrant connected' : 'unavailable',
      status: searchHealth.value.semantic === 'ok' ? 'ok' : 'warning',
    })

    if (searchHealth.value.degraded_mode) {
      items.push({
        system: 'Search Mode',
        value: 'DEG',
        detail: 'running in degraded mode',
        status: 'warning',
      })
    }
  }

  if (items.length === 0) {
    items.push({ system: 'API', value: '...', detail: 'loading', status: 'ok' })
  }

  return items
})

// ─── Event handlers ────────────────────────────────────────
function handleBriefingClick(item: BriefingItem) {
  if (item.type === 'NEW' || item.type === 'INGEST') {
    navigateTo(`/discover`)
  } else if (item.type === 'ALERT') {
    clearUnread()
    navigateTo(`/alerts`)
  } else if (item.type === 'CODE') {
    navigateTo(`/search?q=${encodeURIComponent(item.title)}`)
  } else {
    navigateTo(`/search?q=${encodeURIComponent(item.title)}`)
  }
}

function handleCardClick(pick: ReadingPick) {
  navigateTo(`/papers/${pick.id}`)
}

function handleWorkspaceClick(ws: WorkspaceSummary) {
  navigateTo(`/workspaces/${ws.id}`)
}

function handleQueueItemClick(item: QueueItem) {
  navigateTo(`/reader/${item.id}`)
}

function handleSaveNote(text: string) {
  console.log('Saved to notes:', text)
}

function handleSaveWorkspace(text: string) {
  console.log('Saved to workspace:', text)
}

function handleHeroClick() {
  navigateTo('/discover')
}

function handleTrendClick() {
  navigateTo('/insights/landscape')
}
</script>

<template>
  <div class="ks-dashboard">
    <!-- ═══ Row 1: Hero + Monitor ═══ -->
    <div class="ks-dashboard__row ks-dashboard__row--hero">
      <DashboardHero
        :date="heroDate"
        :title="heroTitle"
        :lead="heroLead"
        :stats="heroStats"
        @click="handleHeroClick"
      />
      <DashboardMonitorRibbon :monitors="monitors" />
    </div>

    <!-- ═══ Row 2: Briefing Strip ═══ -->
    <DashboardBriefingStrip
      :items="briefingItems"
      @item-click="handleBriefingClick"
    />

    <!-- ═══ Row 3: Reading Shelf + Trend Snapshot ═══ -->
    <div class="ks-dashboard__row ks-dashboard__row--shelf">
      <DashboardReadingShelf
        :picks="readingPicks"
        @card-click="handleCardClick"
      />
      <DashboardTrendSnapshot
        :topic="trendTopic"
        :change="trendChange"
        period="Library trends"
        :description="trendDescription"
        :related-topics="trendRelatedTopics"
        :sparkline-data="trendSparkline"
        @click="handleTrendClick"
      />
    </div>

    <!-- ═══ Row 4: Workspace + Queue + Import ═══ -->
    <div class="ks-dashboard__row ks-dashboard__row--bottom">
      <DashboardActiveWorkspacePanel
        :workspaces="workspaces"
        @workspace-click="handleWorkspaceClick"
      />
      <DashboardReadingQueue
        :items="queueItems"
        @item-click="handleQueueItemClick"
      />
      <DashboardPaperImportUrl />
    </div>
  </div>
</template>

<style scoped>
.ks-dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ─── Grid rows ────────────────────────────────────────── */
.ks-dashboard__row {
  display: grid;
  gap: 24px;
}

.ks-dashboard__row--hero {
  grid-template-columns: 5fr 2fr;
  align-items: stretch;
}

.ks-dashboard__row--shelf {
  grid-template-columns: 3fr 1fr;
}

.ks-dashboard__row--bottom {
  grid-template-columns: 5fr 4fr 3fr;
}

/* ─── Responsive ───────────────────────────────────────── */
@media (max-width: 1280px) {
  .ks-dashboard__row--bottom {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .ks-dashboard__row--hero,
  .ks-dashboard__row--shelf,
  .ks-dashboard__row--bottom {
    grid-template-columns: 1fr;
  }
}
</style>
