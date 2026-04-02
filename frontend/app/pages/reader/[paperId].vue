<script setup lang="ts">
/**
 * Smart Reader Page — reader/[paperId]
 *
 * Two-panel layout: main reading canvas (markdown) + sidebar with outline,
 * annotations, AI highlights, and Q&A.
 *
 * Fetches paper content as markdown from the backend API and renders
 * it in a styled, scrollable reading view.
 */
import type { PaperContent, PaperHighlights, PaperLabels } from '~/composables/useApi'
import type { OutlineSection } from '~/components/reader/OutlineSpine.vue'
import type { Annotation } from '~/components/reader/Marginalia.vue'
import type { SemanticHighlight } from '~/components/reader/SemanticHighlights.vue'
import type { ParagraphQuestion } from '~/components/reader/ParagraphQA.vue'
import type { RenderedMarkdownHeading } from '../../utils/markdown'

definePageMeta({
  layout: 'default',
  hideTopbar: true,
  flushContent: true,
})

const route = useRoute()
const { apiFetch, getPaperHighlights, askAboutPaper } = useApi()
const paperId = computed(() => {
  const p = route.params.paperId
  return Array.isArray(p) ? p[0] ?? '' : p ?? ''
})
const uid = useId()

useHead({
  title: 'Smart Reader — Kaleidoscope',
  meta: [{ name: 'description', content: 'Read and annotate papers with AI-powered analysis.' }],
})

const activeTab = ref<'outline' | 'labels' | 'annotations' | 'highlights' | 'ragflow'>('outline')

const paperContent = ref<PaperContent | null>(null)
const contentPending = ref(true)
const contentError = ref<string | null>(null)
const markdownOutline = ref<RenderedMarkdownHeading[]>([])

// Dynamic paper title
const paperTitle = computed(() =>
  paperContent.value?.title || 'Loading paper...'
)

// Original paper links for navigation
const originalLinks = computed(() => {
  const urls = paperContent.value?.remote_urls || []
  return urls.map(u => ({
    url: u.url,
    label: u.source === 'arxiv'
      ? (u.type === 'pdf' ? '📄 arXiv PDF' : u.type === 'html' ? '🌐 ar5iv HTML' : '📋 arXiv Abstract')
      : u.source === 'ar5iv' ? '🌐 ar5iv HTML'
      : u.source === 'doi' ? '🔗 DOI Link'
      : `🔗 ${u.source}`,
    type: u.type,
  }))
})

// Build outline from sections
const outlineSections = computed<OutlineSection[]>(() => {
  if (markdownOutline.value.length > 0) {
    return markdownOutline.value.map((heading, index) => ({
      id: heading.id,
      title: heading.title,
      level: heading.level,
      page: index + 1,
    }))
  }

  if (!paperContent.value?.sections)
    return []

  return paperContent.value.sections.map((section, index) => ({
    id: `section-${index}`,
    title: section.title,
    level: section.level,
    page: index + 1,
  }))
})

const activeSectionId = ref('section-0')

// Static demo data (will be replaced by API calls later)
const annotations: Annotation[] = []
const highlights = ref<SemanticHighlight[]>([])
const questions = ref<ParagraphQuestion[]>([])
const qaQuestion = ref('')
const qaLoading = ref(false)
// Note: QA tab removed from sidebar. State kept for future use.

const sidebarTabs = [
  { key: 'outline' as const, label: 'Outline' },
  { key: 'labels' as const, label: 'Labels' },
  { key: 'annotations' as const, label: 'Notes' },
  { key: 'highlights' as const, label: 'AI' },
  { key: 'ragflow' as const, label: 'Ask AI' },
]

// ── Labels ────────────────────────────────────────────────────
const paperLabels = ref<PaperLabels | null>(null)
const labelsLoading = ref(false)

const LABEL_DIMS = [
  { key: 'domain', label: 'Domain', color: '#6366f1' },
  { key: 'task', label: 'Task', color: '#0ea5e9' },
  { key: 'method', label: 'Method', color: '#10b981' },
  { key: 'data_object', label: 'Data / Object', color: '#f59e0b' },
  { key: 'application', label: 'Application', color: '#ec4899' },
] as const

const META_DIMS = [
  { key: 'paper_type', label: 'Paper Type', color: '#8b5cf6' },
  { key: 'evaluation_quality', label: 'Evaluation', color: '#64748b' },
  { key: 'resource_constraint', label: 'Resource', color: '#78716c' },
] as const

async function loadLabels() {
  if (!paperId.value) return
  labelsLoading.value = true
  try {
    const config = useRuntimeConfig()
    const apiBase = config.public.apiUrl as string
    const data = await $fetch<{ labels: PaperLabels }>(`${apiBase}/api/v1/papers/${paperId.value}/labels`)
    paperLabels.value = data.labels
  }
  catch {
    paperLabels.value = null
  }
  finally {
    labelsLoading.value = false
  }
}

function handleSectionClick(section: OutlineSection) {
  activeSectionId.value = section.id
  const el = document.getElementById(section.id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function handleOutlineChange(headings: RenderedMarkdownHeading[]) {
  markdownOutline.value = headings

  if (headings.length === 0) {
    activeSectionId.value = 'section-0'
    return
  }

  const hasActiveHeading = headings.some(heading => heading.id === activeSectionId.value)
  if (!hasActiveHeading && headings[0]?.id) {
    activeSectionId.value = headings[0].id
  }
}

function handleActiveHeadingChange(headingId: string | null) {
  if (headingId)
    activeSectionId.value = headingId
}

function handleAnnotationClick(_annotation: Annotation) {
  // TODO: scroll to annotation location
}

function handleHighlightClick(_highlight: SemanticHighlight) {
  // TODO: scroll to highlight location
}

function toSemanticHighlightItems(
  items: string[],
  category: SemanticHighlight['category'],
  prefix: string,
  confidence: number,
): SemanticHighlight[] {
  return items.map((text, index) => ({
    id: `${prefix}-${index}`,
    text,
    category,
    confidence,
    page: 1,
  }))
}

function mapPaperHighlights(payload: PaperHighlights): SemanticHighlight[] {
  return [
    ...toSemanticHighlightItems(payload.highlights, 'result', 'highlight', 0.86),
    ...toSemanticHighlightItems(payload.contributions, 'contribution', 'contribution', 0.92),
    ...toSemanticHighlightItems(payload.limitations, 'limitation', 'limitation', 0.78),
  ]
}

watch(
  paperId,
  async currentPaperId => {
    if (!currentPaperId) {
      highlights.value = []
      return
    }

    try {
      const payload = await getPaperHighlights(currentPaperId)
      highlights.value = mapPaperHighlights(payload)
    }
    catch {
      highlights.value = []
    }
  },
  { immediate: true },
)

async function loadPaperContent() {
  if (!paperId.value) {
    paperContent.value = null
    contentPending.value = false
    contentError.value = null
    return
  }

  contentPending.value = true
  contentError.value = null

  try {
    paperContent.value = await apiFetch<PaperContent>(`/papers/${paperId.value}/content`)
    markdownOutline.value = []
  } catch (error) {
    paperContent.value = null
    markdownOutline.value = []
    contentError.value = error instanceof Error ? error.message : 'Failed to load paper content'
  } finally {
    contentPending.value = false
  }
}

// Content quality state
const contentFormat = computed(() => paperContent.value?.format ?? 'unknown')
const isAbstractOnly = computed(() => contentFormat.value === 'abstract_only' || contentFormat.value === 'metadata_only')
const reprocessing = ref(false)
const reprocessError = ref<string | null>(null)

async function triggerReprocess() {
  if (!paperId.value || reprocessing.value) return
  reprocessing.value = true
  reprocessError.value = null
  try {
    const config = useRuntimeConfig()
    const apiBase = config.public.apiUrl as string
    await $fetch(`${apiBase}/api/v1/papers/${paperId.value}/reparse`, {
      method: 'POST',
      body: { url: null, is_html: false },
    })
    // Reload content after ~5s to give server time to process
    await new Promise(r => setTimeout(r, 5000))
    await loadPaperContent()
  } catch (error: unknown) {
    const detail = typeof error === 'object'
      && error !== null
      && 'data' in error
      && typeof (error as { data?: { detail?: unknown } }).data?.detail === 'string'
      ? (error as { data?: { detail?: string } }).data?.detail
      : null

    reprocessError.value = detail || 'Reprocessing failed — please try again later.'
  } finally {
    reprocessing.value = false
  }
}

onMounted(() => {
  void loadPaperContent()
  void loadLabels()
})

watch(paperId, (currentPaperId, previousPaperId) => {
  if (previousPaperId && currentPaperId !== previousPaperId) {
    void loadPaperContent()
  }
})

async function handleAskQuestion() {
  const q = qaQuestion.value.trim()
  if (!q || qaLoading.value) return

  qaLoading.value = true

  try {
    const result = await askAboutPaper(paperId.value, q)
    questions.value.unshift({
      id: `qa-${Date.now()}`,
      question: q,
      answer: result.answer,
      paragraph: 0,
      source: 'AI',
    })
    qaQuestion.value = ''
  }
  catch {
    questions.value.unshift({
      id: `qa-err-${Date.now()}`,
      question: q,
      answer: 'Sorry, could not get an answer. Please try again.',
      paragraph: 0,
      source: 'Error',
    })
  }
  finally {
    qaLoading.value = false
  }
}
</script>

<template>
  <div class="ks-reader">
    <!-- Original paper link bar -->
    <div v-if="originalLinks.length" class="ks-reader__links">
      <span class="ks-reader__links-label">View Original:</span>
      <a
        v-for="link in originalLinks"
        :key="link.url"
        :href="link.url"
        target="_blank"
        rel="noopener noreferrer"
        class="ks-reader__link-btn"
      >
        {{ link.label }}
        <svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor" style="margin-left:4px">
          <path d="M11 3a1 1 0 110-2h6a1 1 0 011 1v6a1 1 0 01-2 0V4.414l-7.293 7.293a1 1 0 01-1.414-1.414L14.586 3H11z"/>
          <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z"/>
        </svg>
      </a>
    </div>

    <!-- Abstract-only content warning banner -->
    <div v-if="isAbstractOnly && !contentPending" class="ks-reader__quality-banner">
      <div class="ks-reader__quality-banner-icon">⚠️</div>
      <div class="ks-reader__quality-banner-body">
        <strong>Full text not yet available.</strong>
        This paper's PDF is still being processed by MinerU. Currently showing the abstract only.
        <span v-if="reprocessError" class="ks-reader__quality-banner-error"> {{ reprocessError }}</span>
      </div>
      <button
        class="ks-reader__quality-reprocess-btn"
        :disabled="reprocessing"
        @click="triggerReprocess"
      >
        {{ reprocessing ? '⏳ Processing…' : '🔄 Re-process PDF' }}
      </button>
    </div>

    <div class="ks-reader__layout">
      <div class="ks-reader__main">
        <ReaderMarkdownCanvas
          :title="paperTitle"
          :content="paperContent"
          :pending="contentPending"
          :error="contentError"
          @outline-change="handleOutlineChange"
          @active-heading-change="handleActiveHeadingChange"
        />
      </div>

      <aside class="ks-reader__sidebar" aria-label="Reader tools">
        <div class="ks-reader__tabs" role="tablist">
          <button
            v-for="tab in sidebarTabs"
            :id="`${uid}-tab-${tab.key}`"
            :key="tab.key"
            type="button"
            role="tab"
            :aria-selected="activeTab === tab.key"
            :aria-controls="`${uid}-panel-${tab.key}`"
            :tabindex="activeTab === tab.key ? 0 : -1"
            :class="['ks-reader__tab', { 'ks-reader__tab--active': activeTab === tab.key }]"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>

        <div
          :id="`${uid}-panel-${activeTab}`"
          class="ks-reader__panel"
          role="tabpanel"
          :aria-labelledby="`${uid}-tab-${activeTab}`"
        >
          <ReaderOutlineSpine
            v-if="activeTab === 'outline'"
            :sections="outlineSections"
            :active-section-id="activeSectionId"
            @section-click="handleSectionClick"
          />

          <ReaderMarginalia
            v-if="activeTab === 'annotations'"
            :annotations="annotations"
            @annotation-click="handleAnnotationClick"
          />

          <ReaderSemanticHighlights
            v-if="activeTab === 'highlights'"
            :highlights="highlights"
            @highlight-click="handleHighlightClick"
          />

          <!-- Labels panel -->
          <div v-if="activeTab === 'labels'" class="ks-reader__labels">
            <div v-if="labelsLoading" class="ks-reader__labels-loading">Loading labels…</div>
            <div v-else-if="!paperLabels" class="ks-reader__labels-empty">Labels not yet generated for this paper.</div>
            <template v-else>
              <div v-for="dim in LABEL_DIMS" :key="dim.key" class="ks-reader__label-group">
                <span class="ks-reader__label-dim-name" :style="{ color: dim.color }">{{ dim.label }}</span>
                <div class="ks-reader__label-chips">
                  <span
                    v-for="tag in (paperLabels[dim.key] as string[])"
                    :key="tag"
                    class="ks-reader__label-chip"
                    :style="{ borderColor: dim.color, color: dim.color }"
                  >{{ tag }}</span>
                  <span v-if="!(paperLabels[dim.key] as string[]).length" class="ks-reader__label-none">—</span>
                </div>
              </div>
              <div class="ks-reader__label-divider" />
              <div v-for="dim in META_DIMS" :key="dim.key" class="ks-reader__label-group">
                <span class="ks-reader__label-dim-name" :style="{ color: dim.color }">{{ dim.label }}</span>
                <div class="ks-reader__label-chips">
                  <span
                    v-for="tag in (paperLabels.meta[dim.key] as string[])"
                    :key="tag"
                    class="ks-reader__label-chip"
                    :style="{ borderColor: dim.color, color: dim.color }"
                  >{{ tag }}</span>
                  <span v-if="!(paperLabels.meta[dim.key] as string[]).length" class="ks-reader__label-none">—</span>
                </div>
              </div>
            </template>
          </div>

          <RagflowQAPanel
            v-if="activeTab === 'ragflow'"
            :paper-id="paperId"
            placeholder="Ask this paper with RAGFlow..."
          />
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.ks-reader {
  height: 100%;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.ks-reader__layout {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 12px;
  align-items: stretch;
}

.ks-reader__main {
  display: flex;
  min-width: 0;
  min-height: 0;
}

.ks-reader__sidebar {
  position: sticky;
  top: 10px;
  min-height: 0;
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding: 8px 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-bg);
}

.ks-reader__tabs {
  display: flex;
  gap: 2px;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 12px;
}

.ks-reader__tab {
  flex: 1;
  padding: 8px 4px;
  border: none;
  background: none;
  font: 600 0.75rem / 1 var(--font-mono);
  color: var(--color-secondary);
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  transition: color var(--duration-fast) var(--ease-smooth),
              border-color var(--duration-fast) var(--ease-smooth);
  border-bottom: 2px solid transparent;
}

.ks-reader__tab:hover {
  color: var(--color-text);
}

.ks-reader__tab--active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.ks-reader__tab:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}

.ks-reader__panel {
  flex: 1;
  overflow-y: auto;
}

@media (max-width: 960px) {
  .ks-reader__layout {
    grid-template-columns: 1fr;
  }
  .ks-reader__sidebar {
    position: static;
    height: min(38dvh, 420px);
    margin-top: 8px;
  }
}

/* ── Original paper link bar ──────────────────── */
.ks-reader__links {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 10px;
  padding: 8px 12px;
  background: var(--color-surface, rgba(30, 41, 59, 0.6));
  border: 1px solid var(--color-border, #334155);
  border-radius: 8px;
  backdrop-filter: blur(8px);
  flex-wrap: wrap;
}

.ks-reader__links-label {
  font: 600 0.75rem / 1 var(--font-mono, monospace);
  color: var(--color-secondary, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}

.ks-reader__link-btn {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border: 1px solid var(--color-primary, #8b5cf6);
  border-radius: 6px;
  color: var(--color-primary, #8b5cf6);
  text-decoration: none;
  font: 500 0.8rem / 1 var(--font-sans, 'Inter', sans-serif);
  transition: background 0.2s, color 0.2s, transform 0.15s;
  white-space: nowrap;
}

.ks-reader__link-btn:hover {
  background: var(--color-primary, #8b5cf6);
  color: #fff;
  transform: translateY(-1px);
}

.ks-reader__qa-wrap {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ks-reader__qa-form {
  display: flex;
  gap: 6px;
}

.ks-reader__qa-input {
  flex: 1;
  padding: 8px 12px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font: 400 0.875rem / 1.4 var(--font-serif);
  color: var(--color-text);
  transition: border-color var(--duration-fast) var(--ease-smooth);
}

.ks-reader__qa-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.ks-reader__qa-input:disabled {
  opacity: 0.5;
}

.ks-reader__qa-btn {
  padding: 8px 14px;
  background: var(--color-primary);
  color: var(--color-bg);
  border: none;
  border-radius: 6px;
  font: 600 0.8125rem / 1 var(--font-sans);
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-smooth),
              opacity var(--duration-fast) var(--ease-smooth);
}

.ks-reader__qa-btn:hover:not(:disabled) {
  background: var(--color-primary-dark, #0a8a8e);
}

.ks-reader__qa-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ── Content quality warning banner ───────────── */
.ks-reader__quality-banner {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 0 0 10px;
  padding: 10px 12px;
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.4);
  border-radius: 8px;
  backdrop-filter: blur(6px);
}

.ks-reader__quality-banner-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.ks-reader__quality-banner-body {
  flex: 1;
  font: 400 0.875rem / 1.5 var(--font-sans, 'Inter', sans-serif);
  color: var(--color-text);
}

.ks-reader__quality-banner-error {
  color: #f87171;
  font-weight: 500;
}

.ks-reader__quality-reprocess-btn {
  flex-shrink: 0;
  padding: 8px 18px;
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.5);
  border-radius: 8px;
  color: #f59e0b;
  font: 600 0.8125rem / 1 var(--font-sans, 'Inter', sans-serif);
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
  white-space: nowrap;
}

.ks-reader__quality-reprocess-btn:hover:not(:disabled) {
  background: rgba(245, 158, 11, 0.25);
  border-color: rgba(245, 158, 11, 0.8);
}

.ks-reader__quality-reprocess-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ── Labels sidebar panel ─────────────────────── */
.ks-reader__labels {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px 2px;
}

.ks-reader__labels-loading,
.ks-reader__labels-empty {
  font: 400 0.8125rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  text-align: center;
  padding: 24px 0;
}

.ks-reader__label-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.ks-reader__label-dim-name {
  font: 600 0.6875rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.07em;
}

.ks-reader__label-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.ks-reader__label-chip {
  display: inline-block;
  padding: 2px 7px;
  border: 1px solid;
  border-radius: 3px;
  font: 400 0.75rem / 1.5 var(--font-sans);
  background: transparent;
}

.ks-reader__label-none {
  font: 400 0.75rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
}

.ks-reader__label-divider {
  height: 1px;
  background: var(--color-border);
  margin: 2px 0;
}

</style>
