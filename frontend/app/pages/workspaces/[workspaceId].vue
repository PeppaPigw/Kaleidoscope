<script setup lang="ts">
/**
 * Research Workspace Page — workspaces/[workspaceId]
 */
import type { CorpusPaper } from '~/components/workspace/CorpusShelf.vue'

definePageMeta({ layout: 'default' })

const { t } = useTranslation()

const route = useRoute()
const workspaceId = computed(() => {
  const p = route.params.workspaceId
  return Array.isArray(p) ? p[0] ?? '' : p ?? ''
})

useHead({
  title: 'Research Workspace — Kaleidoscope',
  meta: [{ name: 'description', content: 'Organize papers, research questions, and workflows.' }],
})

const corpusPapers: CorpusPaper[] = [
  { id: 'p1', title: 'ClaimMiner: Atomic Claim Extraction for Biomedical Papers', authors: 'Liu et al.', year: 2025, status: 'annotated' },
  { id: 'p2', title: 'Atomic Facts: Decomposing Knowledge for NLI', authors: 'Min et al.', year: 2024, status: 'read' },
  { id: 'p3', title: 'SciBERT: A Pretrained Language Model for Scientific Text', authors: 'Beltagy et al.', year: 2019, status: 'read' },
  { id: 'p4', title: 'RAGBench-Sci: Failure Modes of Citation-Grounded Retrieval', authors: 'Jones et al.', year: 2025, status: 'unread' },
  { id: 'p5', title: 'ContractNLI: Claim Verification for Legal Documents', authors: 'Koreeda et al.', year: 2023, status: 'unread' },
]

function handlePaperClick(paper: CorpusPaper) {
  navigateTo(`/papers/${paper.id}`)
}
</script>

<template>
  <div class="ks-workspace">
    <KsPageHeader :title="t('workspaces')" :subtitle="`WORKSPACE ${workspaceId}`" />

    <div class="ks-workspace__content">
      <WorkspaceProjectCover
        name="Claim-Level Scientific NLP"
        description="Investigating atomic claim extraction and evidence alignment for biomedical retrieval-augmented generation."
        :paper-count="5"
        :member-count="3"
        last-updated="2 hours ago"
        status="active"
      />

      <WorkspaceCorpusShelf :papers="corpusPapers" @paper-click="handlePaperClick" />
    </div>
  </div>
</template>

<style scoped>
.ks-workspace {
  min-height: 100vh;
  padding-bottom: 80px;
}

.ks-workspace__content {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}
</style>
