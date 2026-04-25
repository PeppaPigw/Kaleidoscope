<script setup lang="ts">
/**
 * Design System Showcase — Visual gallery of all Ks components.
 * DEV-ONLY page for verifying component rendering and interactions.
 */
import {
  Search,
  Download,
  Filter,
  Star,
  BookOpen,
  Sparkles,
} from "lucide-vue-next";
import type { EvidenceCard } from "~~/types/paper";

useHead({
  title: "Design System — Kaleidoscope",
  meta: [{ name: "robots", content: "noindex" }],
});

// ─── Demo data ────────────────────────────────────────
const demoEvidence: EvidenceCard = {
  id: "ev-1",
  text: "Our approach outperforms all baselines by at least 3.2% on the MMLU benchmark, with particularly strong gains on reasoning-heavy subtasks.",
  source_paper_id: "paper-42",
  page: 7,
  section: "Results",
  claim_type: "result",
  confidence: 0.92,
  provenance: {
    source: "gpt-4o",
    confidence: 0.92,
    timestamp: "2026-03-20T14:30:00Z",
  },
  timestamp: "2026-03-20T14:30:00Z",
};

const demoSubQuestions = [
  {
    id: "rq-1",
    text: "How does attention scaling affect performance?",
    status: "active" as const,
  },
  {
    id: "rq-2",
    text: "Is the improvement consistent across model sizes?",
    status: "answered" as const,
  },
  {
    id: "rq-3",
    text: "What is the computational overhead?",
    status: "parked" as const,
  },
];

const showProvenance = ref(false);
const draftActive = ref(false);

function handleQuoteToDraft(ev: EvidenceCard) {
  console.log("Quote to draft:", ev.text.slice(0, 40));
}
</script>

<template>
  <div class="ds-page">
    <KsPageHeader title="Design System" section="Dev" :heading-level="1">
      <template #meta>Kaleidoscope Ks Components</template>
    </KsPageHeader>

    <div class="ds-content">
      <!-- ════════════════════════════════════════════════════ -->
      <!--  SECTION 1: Buttons                                 -->
      <!-- ════════════════════════════════════════════════════ -->
      <section class="ds-section">
        <h2 class="ks-type-section-title">KsButton</h2>
        <p class="ks-type-lead ds-desc">
          Three variants × three sizes, with loading and disabled states.
        </p>

        <div class="ds-grid ds-grid--buttons">
          <!-- Variants -->
          <div class="ds-row">
            <KsButton variant="primary">Primary</KsButton>
            <KsButton variant="secondary">Secondary</KsButton>
            <KsButton variant="ghost">Ghost</KsButton>
          </div>

          <!-- Sizes -->
          <div class="ds-row">
            <KsButton size="sm">Small</KsButton>
            <KsButton size="md">Medium</KsButton>
            <KsButton size="lg">Large</KsButton>
          </div>

          <!-- With icons -->
          <div class="ds-row">
            <KsButton variant="primary">
              <template #icon-left><Search :size="16" /></template>
              Search Papers
            </KsButton>
            <KsButton variant="secondary">
              <template #icon-left><Download :size="16" /></template>
              Export BibTeX
            </KsButton>
            <KsButton variant="ghost">
              <template #icon-left><Filter :size="16" /></template>
              Filter
            </KsButton>
          </div>

          <!-- States -->
          <div class="ds-row">
            <KsButton :loading="true">Loading…</KsButton>
            <KsButton :disabled="true">Disabled</KsButton>
            <KsButton variant="secondary" :loading="true" size="sm"
              >Saving</KsButton
            >
          </div>
        </div>
      </section>

      <KsSectionDivider label="§" />

      <!-- ════════════════════════════════════════════════════ -->
      <!--  SECTION 2: Cards                                   -->
      <!-- ════════════════════════════════════════════════════ -->
      <section class="ds-section">
        <h2 class="ks-type-section-title">KsCard</h2>
        <p class="ks-type-lead ds-desc">
          Editorial card surface with accent top variants.
        </p>

        <div class="ds-grid ds-grid--cards">
          <KsCard>
            <h3 class="ks-type-label">Default Card</h3>
            <p class="ks-type-body-sm">
              Hovers with a subtle lift and shadow. The foundation for every
              content surface in Kaleidoscope.
            </p>
          </KsCard>

          <KsCard variant="teal-top">
            <h3 class="ks-type-label">Teal Top</h3>
            <p class="ks-type-body-sm">
              Used for primary research intent cards and active workspace
              elements.
            </p>
          </KsCard>

          <KsCard variant="gold-top">
            <h3 class="ks-type-label">Gold Top</h3>
            <p class="ks-type-body-sm">
              Used for highlighted insights, trending topics, and editorial
              picks.
            </p>
          </KsCard>

          <KsCard variant="flat" :static="true">
            <h3 class="ks-type-label">Flat + Static</h3>
            <p class="ks-type-body-sm">
              No border, no hover lift. For nested card contexts where elevation
              isn't needed.
            </p>
          </KsCard>

          <KsCard padding="lg">
            <template #header>
              <span class="ks-type-eyebrow">Card with Header</span>
            </template>
            <p class="ks-type-body-sm">
              This card has header and footer slots with divider lines.
            </p>
            <template #footer>
              <div style="display: flex; gap: 8px">
                <KsButton variant="ghost" size="sm">Cancel</KsButton>
                <KsButton size="sm">Save</KsButton>
              </div>
            </template>
          </KsCard>
        </div>
      </section>

      <KsSectionDivider label="02" />

      <!-- ════════════════════════════════════════════════════ -->
      <!--  SECTION 3: Tags                                    -->
      <!-- ════════════════════════════════════════════════════ -->
      <section class="ds-section">
        <h2 class="ks-type-section-title">KsTag</h2>
        <p class="ks-type-lead ds-desc">
          Small label badges for metadata, with interactive and removable modes.
        </p>

        <div class="ds-grid">
          <div class="ds-row">
            <KsTag>Default</KsTag>
            <KsTag variant="primary">Primary</KsTag>
            <KsTag variant="accent">Accent</KsTag>
            <KsTag variant="success">Success</KsTag>
            <KsTag variant="warning">Warning</KsTag>
          </div>

          <div class="ds-row">
            <KsTag variant="primary" :interactive="true">
              <template #icon><Star :size="12" /></template>
              Interactive Pill
            </KsTag>
            <KsTag :removable="true">Removable ×</KsTag>
            <KsTag variant="accent">
              <template #icon><BookOpen :size="12" /></template>
              With Icon
            </KsTag>
          </div>
        </div>
      </section>

      <KsSectionDivider />

      <!-- ════════════════════════════════════════════════════ -->
      <!--  SECTION 4: Skeleton Loading                        -->
      <!-- ════════════════════════════════════════════════════ -->
      <section class="ds-section">
        <h2 class="ks-type-section-title">KsSkeleton</h2>
        <p class="ks-type-lead ds-desc">
          Warm-toned loading placeholders — no spinners for content areas.
        </p>

        <div class="ds-grid ds-grid--skeletons">
          <div>
            <span
              class="ks-type-eyebrow"
              style="margin-bottom: 8px; display: block"
              >Line</span
            >
            <KsSkeleton variant="line" />
          </div>

          <div>
            <span
              class="ks-type-eyebrow"
              style="margin-bottom: 8px; display: block"
              >Circle</span
            >
            <KsSkeleton variant="circle" />
          </div>

          <div>
            <span
              class="ks-type-eyebrow"
              style="margin-bottom: 8px; display: block"
              >Paragraph (4 lines)</span
            >
            <KsSkeleton variant="paragraph" />
          </div>

          <div>
            <span
              class="ks-type-eyebrow"
              style="margin-bottom: 8px; display: block"
              >Card</span
            >
            <KsSkeleton variant="card" />
          </div>

          <div>
            <span
              class="ks-type-eyebrow"
              style="margin-bottom: 8px; display: block"
              >Custom (200×80)</span
            >
            <KsSkeleton width="200px" height="80px" />
          </div>
        </div>
      </section>

      <KsSectionDivider label="✦" />

      <!-- ════════════════════════════════════════════════════ -->
      <!--  SECTION 5: Editorial Typography                    -->
      <!-- ════════════════════════════════════════════════════ -->
      <section class="ds-section">
        <h2 class="ks-type-section-title">Editorial Components</h2>

        <div class="ds-editorial">
          <!-- Drop Cap -->
          <div class="ds-subsection">
            <span class="ks-type-eyebrow">KsDropCap</span>
            <KsDropCap>
              Language models have fundamentally changed how we approach natural
              language processing. The transformer architecture, introduced in
              2017, enabled unprecedented parallelization and attention
              mechanisms that capture long-range dependencies with remarkable
              efficiency.
            </KsDropCap>
          </div>

          <!-- Pull Quote -->
          <div class="ds-subsection">
            <span class="ks-type-eyebrow">KsPullQuote</span>
            <KsPullQuote>
              "The most profound impact of large language models may not be in
              their answers, but in the new questions they enable researchers to
              ask."
              <template #cite>Chen et al., Nature 2026</template>
            </KsPullQuote>
          </div>

          <!-- Margin Note -->
          <div class="ds-subsection" style="position: relative">
            <span class="ks-type-eyebrow">KsMarginNote</span>
            <p class="ks-type-body" style="max-width: 55ch">
              Recent work in multi-modal foundation models has extended the
              transformer paradigm beyond text to images, audio, and structured
              data. This cross-modal transfer learning opens fascinating
              directions for scientific discovery.
            </p>
            <KsMarginNote label="AI Note">
              This summary was generated by GPT-4o with 94% confidence from the
              paper's abstract and introduction.
            </KsMarginNote>
          </div>
        </div>
      </section>

      <KsSectionDivider label="03" />

      <!-- ════════════════════════════════════════════════════ -->
      <!--  SECTION 6: Page Header                             -->
      <!-- ════════════════════════════════════════════════════ -->
      <section class="ds-section">
        <h2 class="ks-type-section-title">KsPageHeader</h2>
        <p class="ks-type-lead ds-desc">
          Sticky running page header (the one at the top of this page is a live
          example).
        </p>

        <KsCard padding="none" :static="true">
          <KsPageHeader
            title="Paper Profile"
            section="Papers"
            :heading-level="2"
          >
            <template #meta>Issue 42 · March 2026</template>
            <template #actions>
              <KsButton variant="ghost" size="sm">
                <template #icon-left><Star :size="14" /></template>
                Bookmark
              </KsButton>
            </template>
          </KsPageHeader>
        </KsCard>
      </section>

      <KsSectionDivider />

      <!-- ════════════════════════════════════════════════════ -->
      <!--  SECTION 7: Error & Empty States                    -->
      <!-- ════════════════════════════════════════════════════ -->
      <section class="ds-section">
        <h2 class="ks-type-section-title">State Components</h2>

        <div class="ds-grid ds-grid--states">
          <div>
            <span
              class="ks-type-eyebrow"
              style="margin-bottom: 12px; display: block"
              >KsErrorAlert</span
            >
            <KsErrorAlert
              message="Failed to fetch paper metadata from CrossRef."
              :retryable="true"
            />
          </div>

          <div>
            <span
              class="ks-type-eyebrow"
              style="margin-bottom: 12px; display: block"
              >KsEmptyState</span
            >
            <KsCard :static="true">
              <KsEmptyState
                title="No papers found"
                description="Try adjusting your search filters or browsing trending topics."
              >
                <template #action>
                  <KsButton variant="secondary" size="sm"
                    >Clear Filters</KsButton
                  >
                </template>
              </KsEmptyState>
            </KsCard>
          </div>
        </div>
      </section>

      <KsSectionDivider label="04" />

      <!-- ════════════════════════════════════════════════════ -->
      <!--  SECTION 8: Cross-Page Components                   -->
      <!-- ════════════════════════════════════════════════════ -->
      <section class="ds-section">
        <h2 class="ks-type-section-title">Cross-Page Components</h2>

        <div class="ds-grid ds-grid--cross">
          <!-- Research Intent Card -->
          <div>
            <span
              class="ks-type-eyebrow"
              style="margin-bottom: 12px; display: block"
              >KsResearchIntent</span
            >
            <KsResearchIntent
              title="How does attention scaling affect LLM reasoning?"
              :sub-questions="demoSubQuestions"
              :paper-count="47"
              :progress="62"
            >
              <template #actions>
                <KsButton variant="ghost" size="sm">Edit</KsButton>
              </template>
            </KsResearchIntent>
          </div>

          <!-- Evidence Card -->
          <div>
            <span
              class="ks-type-eyebrow"
              style="margin-bottom: 12px; display: block"
              >KsEvidenceCard</span
            >
            <KsEvidenceCard
              :evidence="demoEvidence"
              @quote-to-draft="handleQuoteToDraft"
            />
          </div>

          <!-- Draft Target -->
          <div>
            <span
              class="ks-type-eyebrow"
              style="margin-bottom: 12px; display: block"
              >KsDraftTarget</span
            >
            <KsDraftTarget
              label="Drop evidence here"
              section="Introduction"
              :active="draftActive"
              @drop="draftActive = false"
            />
            <div style="margin-top: 8px; text-align: center">
              <KsButton
                variant="ghost"
                size="sm"
                @click="draftActive = !draftActive"
              >
                Toggle Active State
              </KsButton>
            </div>
          </div>
        </div>
      </section>

      <KsSectionDivider label="05" />

      <!-- ════════════════════════════════════════════════════ -->
      <!--  SECTION 9: Provenance Drawer                       -->
      <!-- ════════════════════════════════════════════════════ -->
      <section class="ds-section">
        <h2 class="ks-type-section-title">KsProvenanceDrawer</h2>
        <p class="ks-type-lead ds-desc">
          Global slide-out drawer for AI field provenance. Click below to open.
        </p>

        <KsButton variant="secondary" @click="showProvenance = true">
          <template #icon-left><Sparkles :size="16" /></template>
          Open Provenance Drawer
        </KsButton>

        <KsProvenanceDrawer
          :open="showProvenance"
          field-label="Paper Summary"
          field-value="This paper introduces a novel attention scaling mechanism that improves reasoning performance of large language models by 3.2% on MMLU."
          :provenance="{
            source: 'gpt-4o',
            confidence: 0.94,
            timestamp: '2026-03-20T14:30:00Z',
          }"
          :chain="[
            {
              source: 'CrossRef',
              action: 'Metadata fetch',
              timestamp: '2026-03-19T10:00:00Z',
              detail: 'Retrieved DOI, title, authors.',
            },
            {
              source: 'GROBID',
              action: 'PDF parsing',
              timestamp: '2026-03-19T10:05:00Z',
              detail: 'Extracted full text and section structure.',
            },
            {
              source: 'GPT-4o',
              action: 'Summary generation',
              timestamp: '2026-03-20T14:30:00Z',
              detail: 'Generated abstract summary from introduction + results.',
            },
          ]"
          @close="showProvenance = false"
        />
      </section>

      <KsSectionDivider label="◆" />

      <!-- ════════════════════════════════════════════════════ -->
      <!--  SECTION 10: Full Bleed                             -->
      <!-- ════════════════════════════════════════════════════ -->
      <section class="ds-section">
        <h2 class="ks-type-section-title">KsFullBleed</h2>
        <p class="ks-type-lead ds-desc">
          Full-viewport-width image container with caption.
        </p>

        <KsFullBleed
          src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=1600&h=500&fit=crop"
          alt="Abstract geometric research visualization"
          aspect-ratio="16 / 5"
        >
          <template #caption
            >Figure 1 — Attention patterns in a multi-head transformer (Unsplash
            demo image)</template
          >
        </KsFullBleed>
      </section>
    </div>
  </div>
</template>

<style scoped>
.ds-page {
  max-width: 100%;
}

.ds-content {
  max-width: 960px;
  margin: 0 auto;
  padding-bottom: 80px;
}

.ds-section {
  margin-top: 8px;
}

.ds-desc {
  margin: 4px 0 24px;
}

.ds-subsection {
  margin-bottom: 32px;
}

/* ─── Grid layouts ─────────────────────────────────── */
.ds-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ds-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.ds-grid--cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 20px;
}

.ds-grid--skeletons {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 24px;
}

.ds-grid--states {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.ds-grid--cross {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.ds-editorial {
  max-width: 680px;
}
</style>
