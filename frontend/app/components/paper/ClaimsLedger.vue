<script setup lang="ts">
/**
 * ClaimsLedger — List of atomic claims extracted from the paper.
 *
 * Each claim shows the claim text, category, confidence,
 * evidence linkage, and verification status.
 */

export interface PaperClaim {
  id: string;
  text: string;
  category: string;
  confidence: number;
  evidenceCount: number;
  status: "verified" | "unverified" | "disputed";
}

export interface ClaimsLedgerProps {
  claims: PaperClaim[];
}

defineProps<ClaimsLedgerProps>();
defineEmits<{ "claim-click": [claim: PaperClaim] }>();

const uid = useId();

function statusIcon(s: PaperClaim["status"]): string {
  switch (s) {
    case "verified":
      return "✓";
    case "disputed":
      return "✗";
    case "unverified":
      return "?";
  }
}
</script>

<template>
  <section
    class="ks-claims-ledger ks-motion-paper-reveal"
    :aria-labelledby="`${uid}-title`"
  >
    <h2 :id="`${uid}-title`" class="ks-type-section-title">Claims Ledger</h2>
    <p
      class="ks-type-body-sm"
      style="color: var(--color-secondary); margin-bottom: 16px"
    >
      {{ claims.length }} atomic claims extracted
    </p>

    <ol class="ks-claims-ledger__list">
      <li
        v-for="(claim, i) in claims"
        :key="claim.id"
        class="ks-claims-ledger__item"
      >
        <div class="ks-claims-ledger__index" aria-hidden="true">
          {{ i + 1 }}
        </div>
        <div class="ks-claims-ledger__body">
          <button
            type="button"
            class="ks-claims-ledger__text"
            :aria-label="`Claim ${i + 1}: ${claim.text}`"
            @click="$emit('claim-click', claim)"
          >
            {{ claim.text }}
          </button>
          <div class="ks-claims-ledger__meta">
            <KsTag
              :variant="
                claim.status === 'verified'
                  ? 'primary'
                  : claim.status === 'disputed'
                    ? 'danger'
                    : 'neutral'
              "
            >
              <span aria-hidden="true">{{ statusIcon(claim.status) }}</span>
              {{ claim.status }}
            </KsTag>
            <span class="ks-type-data" style="color: var(--color-accent)">{{
              claim.category
            }}</span>
            <span class="ks-type-data"
              >{{ (claim.confidence * 100).toFixed(0) }}%</span
            >
            <span class="ks-type-data">{{ claim.evidenceCount }} evidence</span>
          </div>
        </div>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.ks-claims-ledger__list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  list-style: none;
  padding: 0;
  margin: 0;
  counter-reset: claim;
}

.ks-claims-ledger__item {
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 2px;
  transition: background-color var(--duration-fast) var(--ease-smooth);
}

.ks-claims-ledger__item:hover {
  background: rgba(250, 250, 247, 0.8);
}

.ks-claims-ledger__index {
  flex-shrink: 0;
  width: 24px;
  font: 700 0.75rem / 24px var(--font-mono);
  text-align: center;
  color: var(--color-secondary);
  border: 1px solid var(--color-border);
  border-radius: 2px;
  height: 24px;
}

.ks-claims-ledger__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ks-claims-ledger__text {
  font: 400 0.9375rem / 1.5 var(--font-serif);
  color: var(--color-text);
  text-align: left;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}

.ks-claims-ledger__text:hover {
  color: var(--color-primary);
}

.ks-claims-ledger__text:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-claims-ledger__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
