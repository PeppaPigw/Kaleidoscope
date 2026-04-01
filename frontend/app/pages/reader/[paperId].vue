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
import type { PaperContent, PaperHighlights } from '~/composables/useApi'
import type { OutlineSection } from '~/components/reader/OutlineSpine.vue'
import type { Annotation } from '~/components/reader/Marginalia.vue'
import type { SemanticHighlight } from '~/components/reader/SemanticHighlights.vue'
import type { ParagraphQuestion } from '~/components/reader/ParagraphQA.vue'

definePageMeta({ layout: 'default' })

const route = useRoute()
const { apiFetch, getPaperHighlights, askAboutPaper } = useApi()
const paperId = computed(() => {
  const p = route.params.paperId
  return Array.isArray(p) ? p[0] ?? '' : p ?? ''
})
const uid = useId()
const { t } = useTranslation()

useHead({
  title: 'Smart Reader — Kaleidoscope',
  meta: [{ name: 'description', content: 'Read and annotate papers with AI-powered analysis.' }],
})

const activeTab = ref<'outline' | 'annotations' | 'highlights' | 'qa' | 'ragflow'>('outline')

const paperContent = ref<PaperContent | null>(null)
const contentPending = ref(true)
const contentError = ref<string | null>(null)

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
  if (!paperContent.value?.sections) return []
  return paperContent.value.sections.map((s, i) => ({
    id: `section-${i}`,
    title: s.title,
    level: s.level,
    page: i + 1, // section index as "page"
  }))
})

const activeSectionId = ref('section-0')

// Static demo data (will be replaced by API calls later)
const annotations: Annotation[] = []
const highlights = ref<SemanticHighlight[]>([])
const questions = ref<ParagraphQuestion[]>([])
const qaQuestion = ref('')
const qaLoading = ref(false)

const sidebarTabs = [
  { key: 'outline' as const, label: 'Outline' },
  { key: 'annotations' as const, label: 'Notes' },
  { key: 'highlights' as const, label: 'AI' },
  { key: 'qa' as const, label: 'Q&A' },
  { key: 'ragflow' as const, label: 'Ask AI' },
]

function handleSectionClick(section: OutlineSection) {
  activeSectionId.value = section.id
  const el = document.getElementById(section.id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function handleAnnotationClick(annotation: Annotation) {
  // TODO: scroll to annotation location
}

function handleHighlightClick(highlight: SemanticHighlight) {
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
  } catch (error) {
    paperContent.value = null
    contentError.value = error instanceof Error ? error.message : 'Failed to load paper content'
  } finally {
    contentPending.value = false
  }
}

onMounted(() => {
  void loadPaperContent()
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
    <KsPageHeader :title="paperTitle" :subtitle="t('readerSubtitle')" />

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

    <div class="ks-reader__layout">
      <div class="ks-reader__main">
        <ReaderMarkdownCanvas
          :title="paperTitle"
          :content="paperContent"
          :pending="contentPending"
          :error="contentError"
        />
      </div>

      <aside class="ks-reader__sidebar" aria-label="Reader tools">
        <div class="ks-reader__tabs" role="tablist">
          <button
            v-for="tab in sidebarTabs"
            :key="tab.key"
            :id="`${uid}-tab-${tab.key}`"
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

          <div v-if="activeTab === 'qa'" class="ks-reader__qa-wrap">
            <form class="ks-reader__qa-form" @submit.prevent="handleAskQuestion">
              <input
                v-model="qaQuestion"
                type="text"
                class="ks-reader__qa-input"
                placeholder="Ask a question about this paper..."
                :disabled="qaLoading"
                aria-label="Ask a question about this paper"
              />
              <button
                type="submit"
                class="ks-reader__qa-btn"
                :disabled="qaLoading || !qaQuestion.trim()"
              >
                {{ qaLoading ? '...' : 'Ask' }}
              </button>
            </form>
            <ReaderParagraphQA :questions="questions" />
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
  min-height: 100vh;
  padding-bottom: 40px;
}

.ks-reader__layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
}

.ks-reader__sidebar {
  position: sticky;
  top: 96px;
  height: calc(100vh - 120px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.ks-reader__tabs {
  display: flex;
  gap: 2px;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 16px;
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
    height: auto;
  }
}

/* ── Original paper link bar ──────────────────── */
.ks-reader__links {
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 1400px;
  margin: 0 auto 16px;
  padding: 12px 24px;
  background: var(--color-surface, rgba(30, 41, 59, 0.6));
  border: 1px solid var(--color-border, #334155);
  border-radius: 10px;
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
  padding: 6px 14px;
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
</style>
