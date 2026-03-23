<script setup lang="ts">
/**
 * Writing Studio — writing.vue
 */
import type { ManuscriptSection } from '~/components/writing/ManuscriptOverview.vue'

definePageMeta({ layout: 'default' })

useHead({
  title: 'Writing Studio — Kaleidoscope',
  meta: [{ name: 'description', content: 'Draft, revise, and cite in the manuscript editor.' }],
})

const sections: ManuscriptSection[] = [
  { id: 'ms1', title: 'Abstract', wordCount: 250, status: 'complete', order: 0 },
  { id: 'ms2', title: 'Introduction', wordCount: 1200, status: 'review', order: 1 },
  { id: 'ms3', title: 'Related Work', wordCount: 1800, status: 'draft', order: 2 },
  { id: 'ms4', title: 'Method', wordCount: 2100, status: 'draft', order: 3 },
  { id: 'ms5', title: 'Experiments', wordCount: 800, status: 'draft', order: 4 },
  { id: 'ms6', title: 'Results', wordCount: 0, status: 'empty', order: 5 },
  { id: 'ms7', title: 'Discussion', wordCount: 0, status: 'empty', order: 6 },
  { id: 'ms8', title: 'Conclusion', wordCount: 0, status: 'empty', order: 7 },
]

const totalWordCount = computed(() => sections.reduce((sum, s) => sum + s.wordCount, 0))

function handleSectionClick(section: ManuscriptSection) {
  console.log('Open section:', section.title)
}
</script>

<template>
  <div class="ks-writing">
    <KsPageHeader title="Writing Studio" subtitle="MANUSCRIPT" />

    <div class="ks-writing__content">
      <WritingManuscriptOverview
        title="ClaimMiner: Atomic Claim Extraction for Biomedical Papers with Evidence Alignment"
        target-venue="EMNLP 2025"
        :total-word-count="totalWordCount"
        :target-word-count="8000"
        :sections="sections"
        @section-click="handleSectionClick"
      />

      <div class="ks-card" style="padding: 32px; text-align: center;">
        <p class="ks-type-body-sm" style="color: var(--color-secondary);">
          Draft canvas with Tiptap editor will be available here. Select a section above to begin writing.
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ks-writing {
  min-height: 100vh;
  padding-bottom: 80px;
}

.ks-writing__content {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}
</style>
