<script setup lang="ts">
/**
 * Dashboard Page — Morning Briefing Cover
 *
 * The researcher's daily landing page, styled like a magazine cover.
 * Composes dashboard-scoped components into a responsive grid layout.
 * Uses mock data until backend API is connected.
 */
import type { HeroStat } from '~/components/dashboard/DashboardHero.vue'
import type { BriefingItem } from '~/components/dashboard/BriefingStrip.vue'
import type { ReadingPick } from '~/components/dashboard/ReadingShelf.vue'
import type { WorkspaceSummary } from '~/components/dashboard/ActiveWorkspacePanel.vue'
import type { QueueItem } from '~/components/dashboard/ReadingQueue.vue'
import type { MonitorItem } from '~/components/dashboard/MonitorRibbon.vue'

definePageMeta({
  layout: 'default',
  title: 'Dashboard',
})

useHead({
  title: 'Dashboard — Kaleidoscope',
  meta: [
    { name: 'description', content: "Your daily research briefing — today's theme, recommended papers, workspace progress, and system health." },
  ],
})

// ─── Mock data (will be replaced by API composables) ──────
const heroDate = 'MON 2026-03-22'
const heroTitle = 'Clinical Multimodal Reasoning Enters the Verification Era'
const heroLead = '27 篇新论文已入库，6 条 leaderboard claim 与既有证据冲突，今日重点转向 "可复现临床推理" 而非更高分数。'
const heroStats: HeroStat[] = [
  { label: 'NEW PAPERS', value: '27' },
  { label: 'CONFLICTS', value: '6' },
  { label: 'CODE RELEASES', value: '3' },
]

const briefingItems: BriefingItem[] = [
  { id: 'b-1', type: 'NEW', title: 'GraphRAG for Literature Reviews', time: '08:12' },
  { id: 'b-2', type: 'ALERT', title: '3 papers claim MedQA SOTA without external validation', time: '08:16' },
  { id: 'b-3', type: 'CODE', title: 'BenchLab-128K GitHub linked', time: '08:20' },
  { id: 'b-4', type: 'INGEST', title: 'Nature Machine Intelligence RSS synced', time: '08:24' },
]

const readingPicks: ReadingPick[] = [
  {
    id: 'pick-1',
    eyebrow: 'Controversial',
    title: 'MedReasoner-VL: Grounded Clinical Reasoning with Patient Timelines',
    venue: 'ICLR 2026 · 4 authors',
    tags: ['Code'],
    abstract: 'A multimodal approach to clinical reasoning that grounds decisions in patient timeline data, achieving state-of-the-art on 3 benchmarks.',
  },
  {
    id: 'pick-2',
    eyebrow: 'Survey',
    title: 'GraphRAG for Literature Reviews: Citation-Aware Retrieval with Evidence Tracing',
    venue: 'ACL 2025 · 38 cites',
    tags: [],
    abstract: 'Comprehensive survey of graph-augmented retrieval methods for scientific document analysis with novel evidence tracing framework.',
  },
  {
    id: 'pick-3',
    eyebrow: 'Benchmark',
    title: 'BenchLab-128K: Stress Testing Long-Context Scientific QA',
    venue: 'NeurIPS 2025',
    tags: ['Open weights'],
    abstract: 'A challenging benchmark for evaluating long-context reasoning in scientific question answering across 12 domains.',
  },
]

const workspaces: WorkspaceSummary[] = [
  { id: 'ws-1', name: 'Clinical Reasoning Review', progress: 43, detail: '12/28 papers annotated' },
  { id: 'ws-2', name: 'Citation-Aware Agent Survey', progress: 68, detail: 'evidence matrix 68% complete' },
  { id: 'ws-3', name: 'Long-Context Benchmark Audit', progress: 22, detail: '3 unresolved metric conflicts' },
]

const queueItems: QueueItem[] = [
  { id: 'q-1', title: 'ClaimMiner', time: '18 min', mode: 'evidence-heavy' },
  { id: 'q-2', title: 'BenchLab-128K', time: '12 min', mode: 'skim' },
  { id: 'q-3', title: 'MedReasoner-VL', time: '24 min', mode: 'methods focus' },
  { id: 'q-4', title: 'RAGBench-Sci', time: '15 min', mode: 'compare' },
]

const monitors: MonitorItem[] = [
  { system: 'GROBID', value: '2.8s', detail: 'avg parse latency', status: 'ok' },
  { system: 'Neo4j Sync', value: '14m', detail: 'delayed', status: 'warning' },
  { system: 'CrossRef', value: '429', detail: 'spikes in last hour', status: 'warning' },
]

// ─── Event handlers ────────────────────────────────────────
function handleBriefingClick(item: BriefingItem) {
  if (item.type === 'NEW' || item.type === 'INGEST') {
    navigateTo(`/discover`)
  } else if (item.type === 'ALERT') {
    navigateTo(`/analysis/evidence`)
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
        topic="Citation-grounded scientific agents"
        change="+36%"
        period="30 天趋势"
        description="30 天内出现于 112 篇新论文，峰值发生在 Mar 18"
        :related-topics="['RRF', 'Evidence tracing', 'Toolformer']"
        :sparkline-data="[10, 15, 22, 18, 35, 42, 38, 55, 62, 58, 72, 78, 82, 88]"
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
