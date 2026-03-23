<script setup lang="ts">
/**
 * ClaimSearch — Claim-first search mode panel.
 *
 * When the search mode is "claim", this panel replaces the standard results.
 * Shows atomic claims extracted from papers with supporting/contradicting
 * evidence, confidence levels, and links back to source papers.
 */

export interface ClaimEvidence {
  paperId: string
  paperTitle: string
  stance: 'supports' | 'contradicts' | 'neutral'
  snippet: string
}

export interface ClaimResult {
  id: string
  claim: string
  confidence: number
  category: string
  evidence: ClaimEvidence[]
}

export interface ClaimSearchProps {
  claims: ClaimResult[]
  loading?: boolean
}

defineProps<ClaimSearchProps>()

defineEmits<{
  'claim-click': [claim: ClaimResult]
  'paper-click': [paperId: string]
}>()

const uid = useId()

function stanceColor(stance: ClaimEvidence['stance']): string {
  switch (stance) {
    case 'supports': return 'var(--color-primary)'
    case 'contradicts': return '#B54A4A'
    case 'neutral': return 'var(--color-secondary)'
  }
}

function stanceLabel(stance: ClaimEvidence['stance']): string {
  switch (stance) {
    case 'supports': return 'Supporting'
    case 'contradicts': return 'Contradicting'
    case 'neutral': return 'Neutral'
  }
}
</script>

<template>
  <section class="ks-claim-search" :aria-labelledby="`${uid}-title`">
    <h2 :id="`${uid}-title`" class="sr-only">Claim-based Search Results</h2>

    <!-- Loading -->
    <div v-if="loading" class="ks-claim-search__list">
      <div v-for="i in 3" :key="i" class="ks-card ks-claim-search__card">
        <KsSkeleton variant="paragraph" :lines="2" />
        <KsSkeleton variant="line" width="60%" />
      </div>
    </div>

    <!-- Claims -->
    <div v-else class="ks-claim-search__list">
      <article
        v-for="(claim, i) in claims"
        :key="claim.id"
        :class="[
          'ks-card ks-claim-search__card',
          'ks-motion-paper-reveal',
          `ks-motion-paper-reveal--delay-${(i % 3) + 1}`,
        ]"
      >
        <div class="ks-claim-search__card-header">
          <span class="ks-type-eyebrow" style="color: var(--color-accent);">
            {{ claim.category }}
          </span>
          <span class="ks-type-data" style="color: var(--color-primary); font-weight: 700;">
            {{ (claim.confidence * 100).toFixed(0) }}% confidence
          </span>
        </div>

        <button
          type="button"
          class="ks-claim-search__claim-text"
          @click="$emit('claim-click', claim)"
        >
          <span class="ks-claim-search__claim-quote">"</span>
          {{ claim.claim }}
          <span class="ks-claim-search__claim-quote">"</span>
        </button>

        <div class="ks-claim-search__evidence-list">
          <div
            v-for="ev in claim.evidence"
            :key="ev.paperId"
            class="ks-claim-search__evidence"
            :style="{ borderLeftColor: stanceColor(ev.stance) }"
          >
            <div class="ks-claim-search__evidence-header">
              <KsTag :variant="ev.stance === 'supports' ? 'primary' : ev.stance === 'contradicts' ? 'danger' : 'neutral'">
                {{ stanceLabel(ev.stance) }}
              </KsTag>
              <button
                type="button"
                class="ks-claim-search__evidence-link"
                @click="$emit('paper-click', ev.paperId)"
              >
                {{ ev.paperTitle }}
              </button>
            </div>
            <p class="ks-type-body-sm ks-claim-search__evidence-snippet">
              {{ ev.snippet }}
            </p>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.sr-only {
  position: absolute;
  width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border-width: 0;
}

.ks-claim-search__list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ks-claim-search__card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 24px;
}

.ks-claim-search__card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ks-claim-search__claim-text {
  font: 600 1.125rem / 1.5 var(--font-serif);
  color: var(--color-text);
  text-align: left;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  transition: color var(--duration-fast) var(--ease-smooth);
}

.ks-claim-search__claim-text:hover {
  color: var(--color-primary);
}

.ks-claim-search__claim-text:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 4px;
  border-radius: 2px;
}

.ks-claim-search__claim-quote {
  font: 700 1.5rem / 1 var(--font-display);
  color: var(--color-accent-decorative);
}

.ks-claim-search__evidence-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.ks-claim-search__evidence {
  padding: 10px 12px;
  border-left: 3px solid var(--color-border);
  border-radius: 0 2px 2px 0;
  background: rgba(250, 250, 247, 0.5);
}

.ks-claim-search__evidence-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.ks-claim-search__evidence-link {
  font: 600 0.8125rem / 1.3 var(--font-sans);
  color: var(--color-primary);
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  padding: 0;
}

.ks-claim-search__evidence-link:hover {
  text-decoration: underline;
}

.ks-claim-search__evidence-link:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-claim-search__evidence-snippet {
  color: var(--color-secondary);
}
</style>
