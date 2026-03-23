<script setup lang="ts">
/**
 * Researcher Profile Page — [researcherId]
 *
 * Composes ResearcherHero, TopicEvolution, CollaborationAtlas, SignatureShelf.
 */
import type { TopicPeriod } from '~/components/researcher/TopicEvolution.vue'
import type { Collaborator } from '~/components/researcher/CollaborationAtlas.vue'
import type { SignaturePaper } from '~/components/researcher/SignatureShelf.vue'

definePageMeta({ layout: 'default' })

const route = useRoute()
const researcherId = computed(() => route.params.researcherId as string)

useHead({
  title: 'Researcher Profile — Kaleidoscope',
  meta: [
    { name: 'description', content: 'Researcher intelligence: topics, collaborations, and signature papers.' },
  ],
})

// ─── Mock data ───────────────────────────────────────────────
const topics: TopicPeriod[] = [
  { id: 't1', label: 'Information Extraction', years: '2016–2019', paperCount: 8, active: false },
  { id: 't2', label: 'Knowledge Graphs', years: '2018–2021', paperCount: 12, active: false },
  { id: 't3', label: 'Claim Verification', years: '2020–2023', paperCount: 6, active: true },
  { id: 't4', label: 'Retrieval-Augmented Gen', years: '2022–2025', paperCount: 14, active: true },
  { id: 't5', label: 'Atomic Claims', years: '2024–2025', paperCount: 5, active: true },
]

const collaborators: Collaborator[] = [
  { id: 'c1', name: 'Xiaoming Wang', affiliation: 'Stanford University', sharedPapers: 8, lastCollabYear: 2025, intensity: 'high' },
  { id: 'c2', name: 'Hui Chen', affiliation: 'Google DeepMind', sharedPapers: 5, lastCollabYear: 2025, intensity: 'high' },
  { id: 'c3', name: 'Sarah Mitchell', affiliation: 'Allen AI', sharedPapers: 3, lastCollabYear: 2024, intensity: 'medium' },
  { id: 'c4', name: 'Takeshi Yamamoto', affiliation: 'University of Tokyo', sharedPapers: 4, lastCollabYear: 2023, intensity: 'medium' },
  { id: 'c5', name: 'Anna Kowalski', affiliation: 'ETH Zurich', sharedPapers: 2, lastCollabYear: 2022, intensity: 'low' },
  { id: 'c6', name: 'David Park', affiliation: 'KAIST', sharedPapers: 2, lastCollabYear: 2024, intensity: 'low' },
]

const signaturePapers: SignaturePaper[] = [
  { id: 'sp1', title: 'ClaimMiner: Atomic Claim Extraction for Biomedical Papers with Evidence Alignment', venue: 'EMNLP', year: 2025, citations: 42, highlight: 'Flagship work on claim-level document decomposition' },
  { id: 'sp2', title: 'KnowledgeWeave: Temporal Knowledge Graph Construction from Scientific Literature', venue: 'ACL', year: 2023, citations: 187, highlight: 'Most-cited paper — automated KG construction pipeline' },
  { id: 'sp3', title: 'FactNet: A Benchmark for Scientific Claim Verification', venue: 'NeurIPS', year: 2022, citations: 134 },
  { id: 'sp4', title: 'Retrieval-Augmented Reasoning for Multi-Hop Scientific Questions', venue: 'ICLR', year: 2024, citations: 89 },
  { id: 'sp5', title: 'Cross-Document Entity Resolution in Biomedical Corpora', venue: 'NAACL', year: 2021, citations: 156 },
]

// ─── Handlers ────────────────────────────────────────────────
function handleFollow() {
  console.log('Follow researcher:', researcherId.value)
}

function handleTopicClick(topic: TopicPeriod) {
  navigateTo({ path: '/search', query: { q: topic.label, mode: 'semantic' } })
}

function handleCollaboratorClick(collab: Collaborator) {
  navigateTo(`/researchers/${collab.id}`)
}

function handlePaperClick(paper: SignaturePaper) {
  navigateTo(`/papers/${paper.id}`)
}
</script>

<template>
  <div class="ks-researcher-profile">
    <KsPageHeader title="Researcher Intelligence" :subtitle="`RESEARCHER ${researcherId}`" />

    <div class="ks-researcher-profile__content">
      <ResearcherHero
        name="Jiawei Liu"
        affiliation="Tsinghua University"
        title="Associate Professor, Department of Computer Science"
        :h-index="32"
        :total-papers="45"
        :total-citations="4820"
        orcid="0000-0002-1234-5678"
        homepage="https://example.com/jiawei-liu"
        scholar-url="https://scholar.google.com/citations?user=example"
        @follow="handleFollow"
      />

      <ResearcherTopicEvolution :topics="topics" @topic-click="handleTopicClick" />

      <ResearcherSignatureShelf :papers="signaturePapers" @paper-click="handlePaperClick" />

      <ResearcherCollaborationAtlas :collaborators="collaborators" @collaborator-click="handleCollaboratorClick" />
    </div>
  </div>
</template>

<style scoped>
.ks-researcher-profile {
  min-height: 100vh;
  padding-bottom: 80px;
}

.ks-researcher-profile__content {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}
</style>
