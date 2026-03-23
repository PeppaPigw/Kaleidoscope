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
import type { OutlineSection } from '~/components/reader/OutlineSpine.vue'
import type { Annotation } from '~/components/reader/Marginalia.vue'
import type { SemanticHighlight } from '~/components/reader/SemanticHighlights.vue'
import type { ParagraphQuestion } from '~/components/reader/ParagraphQA.vue'

definePageMeta({ layout: 'default' })

const route = useRoute()
const paperId = computed(() => {
  const p = route.params.paperId
  return Array.isArray(p) ? p[0] ?? '' : p ?? ''
})
const uid = useId()

useHead({
  title: 'Smart Reader — Kaleidoscope',
  meta: [{ name: 'description', content: 'Read and annotate papers with AI-powered analysis.' }],
})

const activeTab = ref<'outline' | 'annotations' | 'highlights' | 'qa'>('outline')

// Fetch paper content from API
const apiUrl = useRuntimeConfig().public.apiUrl
const { data: paperContent, pending: contentPending } = useFetch<{
  title: string | null
  abstract: string | null
  has_full_text: boolean
  sections: Array<{ title: string; level: number; paragraphs: string[] }>
  format: string
}>(() => `${apiUrl}/api/v1/papers/${paperId.value}/content`)

// Dynamic paper title
const paperTitle = computed(() =>
  paperContent.value?.title || 'Loading paper...'
)

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
const highlights: SemanticHighlight[] = []
const questions: ParagraphQuestion[] = []

const sidebarTabs = [
  { key: 'outline' as const, label: 'Outline' },
  { key: 'annotations' as const, label: 'Notes' },
  { key: 'highlights' as const, label: 'AI' },
  { key: 'qa' as const, label: 'Q&A' },
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
</script>

<template>
  <div class="ks-reader">
    <KsPageHeader :title="paperTitle" subtitle="SMART READER" />

    <div class="ks-reader__layout">
      <div class="ks-reader__main">
        <ReaderMarkdownCanvas
          :paper-id="paperId"
          :title="paperTitle"
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

          <ReaderParagraphQA
            v-if="activeTab === 'qa'"
            :questions="questions"
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
</style>
