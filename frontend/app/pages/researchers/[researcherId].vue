<script setup lang="ts">
import type { TopicPeriod } from "~/components/researcher/TopicEvolution.vue";
import type { Collaborator } from "~/components/researcher/CollaborationAtlas.vue";
import type { SignaturePaper } from "~/components/researcher/SignatureShelf.vue";
import type { ResearcherHeroProps } from "~/components/researcher/ResearcherHero.vue";
import type { PaperEntry } from "~/components/researcher/PublicationList.vue";

definePageMeta({ layout: "default" });
const route = useRoute();
const researcherId = computed(() => route.params.researcherId as string);
const { apiFetch } = useApi();
useHead({
  title: "Researcher Profile — Kaleidoscope",
  meta: [
    {
      name: "description",
      content:
        "Researcher intelligence: topics, collaborations, and signature papers.",
    },
  ],
});

type ResearcherProfile = {
  display_name?: string;
  affiliation?: string | null;
  raw_affiliation?: string | null;
  orcid?: string | null;
  h_index?: number | null;
  citation_count?: number | null;
  paper_count?: number | null;
  paper_count_in_library?: number;
  total_citations_in_library?: number;
  semantic_scholar_id?: string | null;
  scholar_url?: string | null;
  homepage?: string | null;
  aliases?: string[];
  affiliations?: Array<{ name: string }>;
  enriched_at?: string | null;
  co_authors?: Array<Record<string, unknown>>;
  top_papers?: Array<Record<string, unknown>>;
  papers?: Array<Record<string, unknown>>;
  topics?: Array<Record<string, unknown>>;
  timeline?: Array<{ year: number; count: number }>;
};

const profile = ref<ResearcherProfile | null>(null);
const enriching = ref(false);
const enrichResult = ref<{
  status: string;
  changes?: string[];
  match_reason?: string;
} | null>(null);

const heroFallback: ResearcherHeroProps = {
  name: "Researcher",
  affiliation: "",
  title: "",
  hIndex: 0,
  totalPapers: 0,
  totalCitations: 0,
  orcid: undefined,
  homepage: undefined,
  scholarUrl: undefined,
};

const hero = computed<ResearcherHeroProps>(() => {
  if (!profile.value) return heroFallback;
  const p = profile.value;
  const affiliation =
    p.affiliations?.[0]?.name || p.affiliation || p.raw_affiliation || "";
  // Prefer S2 global counts for stats when available (richer signal)
  const totalPapers = p.paper_count ?? p.paper_count_in_library ?? 0;
  const totalCitations = p.citation_count ?? p.total_citations_in_library ?? 0;
  return {
    ...heroFallback,
    name: p.display_name || heroFallback.name,
    affiliation,
    title: affiliation ? "Researcher" : "",
    hIndex: p.h_index ?? heroFallback.hIndex,
    totalPapers,
    totalCitations,
    orcid: p.orcid ?? undefined,
    homepage: p.homepage ?? undefined,
    scholarUrl: p.scholar_url ?? undefined,
  };
});

const papers = computed<PaperEntry[]>(() =>
  (profile.value?.papers ?? []).map((p) => ({
    id: String(p.id ?? ""),
    title: String(p.title ?? "Untitled"),
    doi: p.doi as string | null,
    arxiv_id: p.arxiv_id as string | null,
    s2_paper_id: p.s2_paper_id as string | null,
    abstract: p.abstract as string | null,
    keywords: Array.isArray(p.keywords) ? (p.keywords as string[]) : [],
    published_at: p.published_at as string | null,
    year: p.year as number | null,
    citation_count: Number(p.citation_count ?? 0),
    venue: p.venue as string | null,
    in_library: Boolean(p.in_library),
    library_paper_id: p.library_paper_id as string | null,
    has_full_text: Boolean(p.has_full_text),
    author_position:
      p.author_position != null ? Number(p.author_position) : null,
    is_corresponding: Boolean(p.is_corresponding),
  })),
);

const signaturePapers = computed<SignaturePaper[]>(() =>
  (profile.value?.top_papers ?? []).map((paper, i) => ({
    id: String(paper.id ?? `paper-${i}`),
    title: String(paper.title ?? "Untitled paper"),
    venue: paper.is_corresponding ? "Corresponding author" : "Library paper",
    year: paper.year
      ? Number(paper.year)
      : new Date(
          String(paper.published_at ?? new Date().toISOString()),
        ).getFullYear(),
    citations: Number(paper.citation_count ?? 0),
    highlight:
      paper.author_position !== undefined
        ? `Author #${Number(paper.author_position) + 1}`
        : undefined,
  })),
);

const topics = computed<TopicPeriod[]>(() =>
  (profile.value?.topics ?? []).map((t) => ({
    id: String(t.id ?? ""),
    label: String(t.label ?? ""),
    years: String(t.years ?? ""),
    paperCount: Number(t.paperCount ?? 0),
    active: Boolean(t.active),
  })),
);

const collaborators = computed<Collaborator[]>(() =>
  (profile.value?.co_authors ?? []).map((co, i) => {
    const sharedPapers = Number(co.paper_count ?? 1);
    return {
      id: String(co.id ?? `co-${i}`),
      name: String(co.display_name ?? "Unknown collaborator"),
      affiliation: String(co.affiliation ?? ""),
      sharedPapers,
      lastCollabYear: Number(co.last_collab_year ?? new Date().getFullYear()),
      intensity:
        sharedPapers >= 5 ? "high" : sharedPapers >= 3 ? "medium" : "low",
    };
  }),
);

const timeline = computed(() => profile.value?.timeline ?? []);

const hasS2Stats = computed(
  () => !!(profile.value?.citation_count || profile.value?.paper_count),
);
const hasLibraryStats = computed(() => !!profile.value?.paper_count_in_library);

async function loadProfile() {
  try {
    profile.value = await apiFetch<ResearcherProfile>(
      `/researchers/${researcherId.value}/profile`,
    );
  } catch {
    profile.value = null;
  }
}

async function enrichFromS2() {
  enriching.value = true;
  enrichResult.value = null;
  try {
    const result = await apiFetch<{
      status: string;
      changes?: string[];
      match_reason?: string;
    }>(`/researchers/${researcherId.value}/enrich`, { method: "POST" });
    enrichResult.value = result;
    if (result.status === "ok") await loadProfile();
  } catch {
    enrichResult.value = { status: "error" };
  } finally {
    enriching.value = false;
  }
}

function handleFollow() {
  console.log("Follow researcher:", researcherId.value);
}
function handleTopicClick(topic: TopicPeriod) {
  navigateTo({ path: "/search", query: { q: topic.label, mode: "semantic" } });
}
function handleCollaboratorClick(collab: Collaborator) {
  navigateTo(`/researchers/${collab.id}`);
}
function handlePaperClick(paper: SignaturePaper | PaperEntry) {
  // For full PaperEntry from PublicationList, prefer library_paper_id for navigation
  const navId =
    "library_paper_id" in paper && paper.library_paper_id
      ? paper.library_paper_id
      : paper.id;
  navigateTo(`/papers/${navId}`);
}

onMounted(loadProfile);
</script>

<template>
  <div class="ks-researcher-profile">
    <KsPageHeader
      title="Researcher Profile"
      :subtitle="profile?.display_name ?? `ID ${researcherId}`"
    />

    <div class="ks-researcher-profile__content">
      <!-- ── Hero ── -->
      <ResearcherHero v-bind="hero" @follow="handleFollow" />

      <!-- ── S2 Enrichment bar ── -->
      <div class="ks-enrich-bar">
        <div class="ks-enrich-bar__meta">
          <span
            v-if="profile?.enriched_at"
            class="ks-enrich-bar__status ks-enrich-bar__status--ok"
          >
            ✓ Synced from Semantic Scholar ·
            {{ new Date(profile.enriched_at).toLocaleDateString() }}
          </span>
          <span v-else class="ks-enrich-bar__status"
            >Profile not yet enriched from Semantic Scholar</span
          >
          <span v-if="profile?.semantic_scholar_id" class="ks-enrich-bar__s2id">
            S2 ID: {{ profile.semantic_scholar_id }}
          </span>
          <a
            v-if="profile?.scholar_url"
            :href="profile.scholar_url"
            target="_blank"
            rel="noopener"
            class="ks-enrich-bar__s2link"
            >View on Semantic Scholar ↗</a
          >
        </div>

        <div class="ks-enrich-bar__actions">
          <span
            v-if="enrichResult?.status === 'no_match'"
            class="ks-enrich-bar__feedback ks-enrich-bar__feedback--warn"
          >
            No match found on Semantic Scholar
          </span>
          <span
            v-else-if="enrichResult?.status === 'ok'"
            class="ks-enrich-bar__feedback ks-enrich-bar__feedback--ok"
          >
            ✓ Updated: {{ enrichResult.changes?.join(", ") }}
          </span>
          <span
            v-else-if="enrichResult?.status === 'error'"
            class="ks-enrich-bar__feedback ks-enrich-bar__feedback--warn"
          >
            Enrichment failed
          </span>

          <button
            class="ks-enrich-bar__btn"
            :disabled="enriching"
            @click="enrichFromS2"
          >
            {{ enriching ? "⏳ Syncing…" : "🔍 Sync from Semantic Scholar" }}
          </button>
        </div>
      </div>

      <!-- ── Stats grid ── -->
      <div class="ks-stats-grid">
        <!-- Library stats -->
        <div class="ks-stats-grid__group">
          <span class="ks-stats-grid__label">In this library</span>
          <div class="ks-stats-grid__row">
            <div class="ks-stats-grid__stat">
              <span class="ks-stats-grid__val">{{
                profile?.paper_count_in_library ?? 0
              }}</span>
              <span class="ks-stats-grid__key">papers</span>
            </div>
            <div class="ks-stats-grid__stat">
              <span class="ks-stats-grid__val">{{
                (profile?.total_citations_in_library ?? 0).toLocaleString()
              }}</span>
              <span class="ks-stats-grid__key">citations</span>
            </div>
          </div>
        </div>

        <!-- S2 global stats (only when enriched) -->
        <div
          v-if="hasS2Stats"
          class="ks-stats-grid__group ks-stats-grid__group--s2"
        >
          <span class="ks-stats-grid__label">Semantic Scholar global</span>
          <div class="ks-stats-grid__row">
            <div v-if="profile?.paper_count" class="ks-stats-grid__stat">
              <span class="ks-stats-grid__val">{{
                profile.paper_count.toLocaleString()
              }}</span>
              <span class="ks-stats-grid__key">papers</span>
            </div>
            <div v-if="profile?.citation_count" class="ks-stats-grid__stat">
              <span class="ks-stats-grid__val">{{
                profile.citation_count.toLocaleString()
              }}</span>
              <span class="ks-stats-grid__key">citations</span>
            </div>
            <div v-if="profile?.h_index" class="ks-stats-grid__stat">
              <span class="ks-stats-grid__val">{{ profile.h_index }}</span>
              <span class="ks-stats-grid__key">h-index</span>
            </div>
          </div>
        </div>

        <!-- Aliases -->
        <div v-if="profile?.aliases?.length" class="ks-stats-grid__group">
          <span class="ks-stats-grid__label">Also known as</span>
          <div class="ks-stats-grid__aliases">
            <span
              v-for="alias in profile.aliases.slice(0, 5)"
              :key="alias"
              class="ks-stats-grid__alias"
              >{{ alias }}</span
            >
          </div>
        </div>
      </div>

      <!-- ── Publication Timeline ── -->
      <ResearcherPublicationTimeline :timeline="timeline" />

      <!-- ── Full Publication List ── -->
      <ResearcherPublicationList
        v-if="papers.length"
        :papers="papers"
        @paper-click="handlePaperClick"
      />

      <!-- ── Top Papers (Signature) ── -->
      <ResearcherSignatureShelf
        v-if="signaturePapers.length"
        :papers="signaturePapers"
        @paper-click="handlePaperClick"
      />

      <!-- ── Collaboration Atlas ── -->
      <ResearcherCollaborationAtlas
        v-if="collaborators.length"
        :collaborators="collaborators"
        @collaborator-click="handleCollaboratorClick"
      />

      <!-- ── Topic Evolution (from keywords) ── -->
      <ResearcherTopicEvolution
        v-if="topics.length"
        :topics="topics"
        @topic-click="handleTopicClick"
      />
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

/* ── Enrichment bar ── */
.ks-enrich-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 16px;
  background: var(--color-surface, #f8f8f8);
  border: 1px solid var(--color-border, #e0e0e0);
  border-radius: 8px;
  flex-wrap: wrap;
}

.ks-enrich-bar__meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.ks-enrich-bar__status {
  font-size: 13px;
  color: var(--color-secondary, #666);
}
.ks-enrich-bar__status--ok {
  color: var(--color-success, #2e7d32);
}

.ks-enrich-bar__s2id {
  font-size: 12px;
  font-family: monospace;
  color: var(--color-secondary, #666);
  background: var(--color-surface-alt, #eee);
  padding: 2px 6px;
  border-radius: 4px;
}

.ks-enrich-bar__s2link {
  font-size: 12px;
  color: var(--color-primary);
  text-decoration: none;
}
.ks-enrich-bar__s2link:hover {
  text-decoration: underline;
}

.ks-enrich-bar__actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ks-enrich-bar__feedback {
  font-size: 13px;
}
.ks-enrich-bar__feedback--ok {
  color: var(--color-success, #2e7d32);
}
.ks-enrich-bar__feedback--warn {
  color: var(--color-warning, #e65100);
}

.ks-enrich-bar__btn {
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 500;
  border: 1px solid var(--color-primary, #1a73e8);
  color: var(--color-primary, #1a73e8);
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
  white-space: nowrap;
}
.ks-enrich-bar__btn:hover:not(:disabled) {
  background: var(--color-primary-light, #e8f0fe);
}
.ks-enrich-bar__btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ── Stats grid ── */
.ks-stats-grid {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  padding: 16px 20px;
  background: var(--color-surface, #f8f8f6);
  border-radius: 10px;
  border: 1px solid var(--color-border);
}

.ks-stats-grid__group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-right: 24px;
  border-right: 1px solid var(--color-border);
}
.ks-stats-grid__group:last-child {
  border-right: none;
  padding-right: 0;
}

.ks-stats-grid__label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-secondary);
}

.ks-stats-grid__row {
  display: flex;
  gap: 20px;
  align-items: flex-end;
}

.ks-stats-grid__stat {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.ks-stats-grid__val {
  font: 700 1.5rem/1 var(--font-mono, monospace);
  color: var(--color-primary);
}

.ks-stats-grid__key {
  font-size: 11px;
  color: var(--color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.ks-stats-grid__group--s2 .ks-stats-grid__val {
  color: var(--color-accent-decorative, #c4a35a);
}

.ks-stats-grid__aliases {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.ks-stats-grid__alias {
  font-size: 12px;
  padding: 3px 8px;
  border: 1px solid var(--color-border);
  border-radius: 3px;
  color: var(--color-secondary);
}
</style>
