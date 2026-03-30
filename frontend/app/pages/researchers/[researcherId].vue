<script setup lang="ts">
import type { TopicPeriod } from '~/components/researcher/TopicEvolution.vue'
import type { Collaborator } from '~/components/researcher/CollaborationAtlas.vue'
import type { SignaturePaper } from '~/components/researcher/SignatureShelf.vue'
import type { ResearcherHeroProps } from '~/components/researcher/ResearcherHero.vue'
definePageMeta({ layout: 'default' })
const route = useRoute()
const researcherId = computed(() => route.params.researcherId as string)
const { rawFetch } = useApi()
useHead({ title: 'Researcher Profile — Kaleidoscope', meta: [{ name: 'description', content: 'Researcher intelligence: topics, collaborations, and signature papers.' }] })
type ResearcherProfile = { display_name?: string; affiliation?: string | null; raw_affiliation?: string | null; orcid?: string | null; h_index?: number | null; paper_count_in_library?: number; total_citations_in_library?: number; co_authors?: Array<Record<string, unknown>>; top_papers?: Array<Record<string, unknown>> }
const { data: profile } = await useFetch<ResearcherProfile>(() => `/api/v1/researchers/${researcherId.value}/profile`, { $fetch: rawFetch as typeof $fetch, retry: 0 })
const topics: TopicPeriod[] = [
  { id: 't1', label: 'Information Extraction', years: '2016–2019', paperCount: 8, active: false },
  { id: 't2', label: 'Knowledge Graphs', years: '2018–2021', paperCount: 12, active: false },
  { id: 't3', label: 'Claim Verification', years: '2020–2023', paperCount: 6, active: true },
  { id: 't4', label: 'Retrieval-Augmented Gen', years: '2022–2025', paperCount: 14, active: true },
  { id: 't5', label: 'Atomic Claims', years: '2024–2025', paperCount: 5, active: true },
]
const heroFallback: ResearcherHeroProps = {
  name: 'Jiawei Liu',
  affiliation: 'Tsinghua University',
  title: 'Associate Professor, Department of Computer Science',
  hIndex: 32,
  totalPapers: 45,
  totalCitations: 4820,
  orcid: '0000-0002-1234-5678',
  homepage: 'https://example.com/jiawei-liu',
  scholarUrl: 'https://scholar.google.com/citations?user=example',
}
const mockCollaborators: Collaborator[] = [
  { id: 'c1', name: 'Xiaoming Wang', affiliation: 'Stanford University', sharedPapers: 8, lastCollabYear: 2025, intensity: 'high' },
  { id: 'c2', name: 'Hui Chen', affiliation: 'Google DeepMind', sharedPapers: 5, lastCollabYear: 2025, intensity: 'high' },
  { id: 'c3', name: 'Sarah Mitchell', affiliation: 'Allen AI', sharedPapers: 3, lastCollabYear: 2024, intensity: 'medium' },
  { id: 'c4', name: 'Takeshi Yamamoto', affiliation: 'University of Tokyo', sharedPapers: 4, lastCollabYear: 2023, intensity: 'medium' },
  { id: 'c5', name: 'Anna Kowalski', affiliation: 'ETH Zurich', sharedPapers: 2, lastCollabYear: 2022, intensity: 'low' },
  { id: 'c6', name: 'David Park', affiliation: 'KAIST', sharedPapers: 2, lastCollabYear: 2024, intensity: 'low' },
]
const mockSignaturePapers: SignaturePaper[] = [
  { id: 'sp1', title: 'ClaimMiner: Atomic Claim Extraction for Biomedical Papers with Evidence Alignment', venue: 'EMNLP', year: 2025, citations: 42, highlight: 'Flagship work on claim-level document decomposition' },
  { id: 'sp2', title: 'KnowledgeWeave: Temporal Knowledge Graph Construction from Scientific Literature', venue: 'ACL', year: 2023, citations: 187, highlight: 'Most-cited paper — automated KG construction pipeline' },
  { id: 'sp3', title: 'FactNet: A Benchmark for Scientific Claim Verification', venue: 'NeurIPS', year: 2022, citations: 134 },
  { id: 'sp4', title: 'Retrieval-Augmented Reasoning for Multi-Hop Scientific Questions', venue: 'ICLR', year: 2024, citations: 89 },
  { id: 'sp5', title: 'Cross-Document Entity Resolution in Biomedical Corpora', venue: 'NAACL', year: 2021, citations: 156 },
]
const hero = computed<ResearcherHeroProps>(() => !profile.value ? heroFallback : {
  ...heroFallback,
  name: profile.value.display_name || heroFallback.name,
  affiliation: profile.value.affiliation || profile.value.raw_affiliation || heroFallback.affiliation,
  title: profile.value.affiliation || profile.value.raw_affiliation ? 'Researcher' : heroFallback.title,
  hIndex: profile.value.h_index ?? heroFallback.hIndex,
  totalPapers: profile.value.paper_count_in_library ?? heroFallback.totalPapers,
  totalCitations: profile.value.total_citations_in_library ?? heroFallback.totalCitations,
  orcid: profile.value.orcid ?? heroFallback.orcid,
})
const collaborators = computed<Collaborator[]>(() =>
  profile.value?.co_authors?.length
    ? profile.value.co_authors.map((co, i) => {
        const sharedPapers = Number(co.paper_count ?? 1)
        return {
          id: String(co.id ?? `co-${i}`),
          name: String(co.display_name ?? 'Unknown collaborator'),
          affiliation: String(co.affiliation ?? hero.value.affiliation),
          sharedPapers,
          lastCollabYear: Number(co.last_collab_year ?? new Date().getFullYear()),
          intensity: sharedPapers >= 5 ? 'high' : sharedPapers >= 3 ? 'medium' : 'low',
        }
      })
    : mockCollaborators,
)
const signaturePapers = computed<SignaturePaper[]>(() =>
  profile.value?.top_papers?.length
    ? profile.value.top_papers.map((paper, i) => ({
        id: String(paper.id ?? `paper-${i}`),
        title: String(paper.title ?? 'Untitled paper'),
        venue: Boolean(paper.is_corresponding) ? 'Corresponding author' : 'Library paper',
        year: new Date(String(paper.published_at ?? new Date().toISOString())).getFullYear(),
        citations: Number(paper.citation_count ?? 0),
        highlight: paper.author_position ? `Author #${paper.author_position}` : undefined,
      }))
    : mockSignaturePapers,
)
function handleFollow() { console.log('Follow researcher:', researcherId.value) }
function handleTopicClick(topic: TopicPeriod) { navigateTo({ path: '/search', query: { q: topic.label, mode: 'semantic' } }) }
function handleCollaboratorClick(collab: Collaborator) { navigateTo(`/researchers/${collab.id}`) }
function handlePaperClick(paper: SignaturePaper) { navigateTo(`/papers/${paper.id}`) }
</script>

<template>
  <div class="ks-researcher-profile">
    <KsPageHeader title="Researcher Intelligence" :subtitle="`RESEARCHER ${researcherId}`" />

    <div class="ks-researcher-profile__content">
      <ResearcherHero v-bind="hero" @follow="handleFollow" />

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
