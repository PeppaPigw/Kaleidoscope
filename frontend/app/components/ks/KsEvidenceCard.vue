<script setup lang="ts">
/**
 * KsEvidenceCard — Cross-page evidence card for claims, methods, results.
 *
 * Displays a single piece of extracted evidence from a paper with provenance
 * information, confidence score, and actions (send to draft, dispute, etc.).
 * Appears in Paper Profile, Synthesis, Writing Studio, and Evidence Lab.
 *
 * @slot actions — Optional action buttons (defaults to "Quote to Draft")
 */
import type { EvidenceCard } from "~~/types/paper";
import { Quote, ExternalLink, ShieldCheck } from "lucide-vue-next";

export interface KsEvidenceCardProps {
  evidence: EvidenceCard;
  /** Show the source paper title link */
  showSource?: boolean;
  /** Compact mode (less padding, no border-left) */
  compact?: boolean;
}

withDefaults(defineProps<KsEvidenceCardProps>(), {
  showSource: true,
  compact: false,
});

defineEmits<{
  "quote-to-draft": [evidence: EvidenceCard];
  "view-source": [paperId: string];
}>();

const typeLabels: Record<string, string> = {
  claim: "Claim",
  method: "Method",
  result: "Result",
  limitation: "Limitation",
  dataset: "Dataset",
  metric: "Metric",
};

const typeColors: Record<string, string> = {
  claim: "var(--color-primary)",
  method: "#6B5CE7",
  result: "#0F7B3F",
  limitation: "#CC4444",
  dataset: "var(--color-accent)",
  metric: "#2D7FD3",
};

function formatConfidence(c: number): string {
  return `${Math.round(c * 100)}%`;
}
</script>

<template>
  <div
    :class="['ks-evidence-card', { 'ks-evidence-card--compact': compact }]"
    :style="{
      '--evidence-color':
        typeColors[evidence.claim_type] || 'var(--color-primary)',
    }"
  >
    <!-- Header: type + confidence -->
    <div class="ks-evidence-card__head">
      <span class="ks-evidence-card__type ks-type-eyebrow">
        {{ typeLabels[evidence.claim_type] || evidence.claim_type }}
      </span>
      <span
        class="ks-evidence-card__confidence ks-type-data"
        :title="`Confidence: ${formatConfidence(evidence.confidence)}`"
      >
        <ShieldCheck :size="12" aria-hidden="true" />
        {{ formatConfidence(evidence.confidence) }}
      </span>
    </div>

    <!-- Quote text -->
    <p class="ks-evidence-card__text ks-type-body-sm">
      <Quote
        :size="14"
        class="ks-evidence-card__quote-icon"
        aria-hidden="true"
      />
      {{ evidence.text }}
    </p>

    <!-- Source + section -->
    <div v-if="showSource" class="ks-evidence-card__source">
      <button
        type="button"
        class="ks-evidence-card__source-link"
        @click="$emit('view-source', evidence.source_paper_id)"
      >
        <ExternalLink :size="12" aria-hidden="true" />
        <span>Page {{ evidence.page }} · {{ evidence.section }}</span>
      </button>
      <span class="ks-evidence-card__provenance ks-type-data">
        {{ evidence.provenance.source }}
      </span>
    </div>

    <!-- Actions -->
    <div class="ks-evidence-card__actions">
      <slot name="actions" :evidence="evidence">
        <button
          type="button"
          class="ks-btn ks-btn--ghost ks-btn--sm ks-evidence-card__action"
          @click="$emit('quote-to-draft', evidence)"
        >
          Quote to Draft
        </button>
      </slot>
    </div>
  </div>
</template>

<style scoped>
.ks-evidence-card {
  padding: 16px 20px;
  border: 1px solid var(--color-border);
  border-left: 3px solid var(--evidence-color, var(--color-primary));
  border-radius: var(--radius-card);
  background: var(--color-surface);
  transition:
    box-shadow var(--duration-normal) var(--ease-smooth),
    border-color var(--duration-fast) var(--ease-smooth);
}

.ks-evidence-card:hover {
  box-shadow: var(--shadow-card-hover);
}

.ks-evidence-card--compact {
  padding: 10px 14px;
  border-left-width: 2px;
}

/* ─── Head ─────────────────────────────────────────── */
.ks-evidence-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.ks-evidence-card__type {
  color: var(--evidence-color);
}

.ks-evidence-card__confidence {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--color-secondary);
}

/* ─── Quote ────────────────────────────────────────── */
.ks-evidence-card__text {
  position: relative;
  margin-bottom: 10px;
}

.ks-evidence-card__quote-icon {
  color: var(--color-accent);
  opacity: 0.5;
  margin-right: 4px;
  vertical-align: middle;
}

/* ─── Source ────────────────────────────────────────── */
.ks-evidence-card__source {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.ks-evidence-card__source-link {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0;
  border: none;
  background: none;
  font: 500 0.75rem / 1.3 var(--font-sans);
  color: var(--color-primary);
  cursor: pointer;
  transition: color var(--duration-fast) var(--ease-smooth);
}

.ks-evidence-card__source-link:hover {
  color: var(--color-primary-hover);
  text-decoration: underline;
  text-underline-offset: 3px;
}

.ks-evidence-card__provenance {
  opacity: 0.7;
}

/* ─── Actions ──────────────────────────────────────── */
.ks-evidence-card__actions {
  display: flex;
  gap: 6px;
  padding-top: 8px;
  border-top: 1px solid var(--color-border);
  opacity: 0;
  transition: opacity var(--duration-fast) var(--ease-smooth);
}

.ks-evidence-card:hover .ks-evidence-card__actions,
.ks-evidence-card:focus-within .ks-evidence-card__actions {
  opacity: 1;
}

.ks-evidence-card__action {
  font-size: 0.75rem;
  height: 28px;
  padding: 0 10px;
}
</style>
