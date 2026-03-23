<script setup lang="ts">
/**
 * ReproductionStatus — Reproducibility assessment card.
 *
 * Shows whether the paper's results have been reproduced,
 * by whom, and with what level of success.
 */

export interface ReproductionAttempt {
  id: string
  team: string
  date: string
  success: 'full' | 'partial' | 'failed'
  notes: string
}

export interface ReproductionStatusProps {
  overallStatus: 'reproduced' | 'partially' | 'not-attempted' | 'failed'
  attempts: ReproductionAttempt[]
  codeAvailable: boolean
  dataAvailable: boolean
}

defineProps<ReproductionStatusProps>()
const uid = useId()

function statusColor(s: ReproductionStatusProps['overallStatus']): string {
  switch (s) {
    case 'reproduced': return 'var(--color-primary)'
    case 'partially': return 'var(--color-accent)'
    case 'not-attempted': return 'var(--color-secondary)'
    case 'failed': return '#B54A4A'
  }
}

function statusLabel(s: ReproductionStatusProps['overallStatus']): string {
  switch (s) {
    case 'reproduced': return '✓ Reproduced'
    case 'partially': return '◐ Partially Reproduced'
    case 'not-attempted': return '○ Not Yet Attempted'
    case 'failed': return '✗ Failed to Reproduce'
  }
}
</script>

<template>
  <section class="ks-repro-status ks-card ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <h2 :id="`${uid}-title`" class="ks-type-section-title">Reproducibility</h2>

    <div class="ks-repro-status__badge" :style="{ color: statusColor(overallStatus) }">
      {{ statusLabel(overallStatus) }}
    </div>

    <div class="ks-repro-status__checklist">
      <div class="ks-repro-status__check">
        <span :style="{ color: codeAvailable ? 'var(--color-primary)' : 'var(--color-secondary)' }">
          {{ codeAvailable ? '✓' : '✗' }}
        </span>
        <span class="ks-type-body-sm">Code available</span>
      </div>
      <div class="ks-repro-status__check">
        <span :style="{ color: dataAvailable ? 'var(--color-primary)' : 'var(--color-secondary)' }">
          {{ dataAvailable ? '✓' : '✗' }}
        </span>
        <span class="ks-type-body-sm">Data available</span>
      </div>
    </div>

    <div v-if="attempts.length > 0" class="ks-repro-status__attempts">
      <h3 class="ks-type-eyebrow" style="color: var(--color-accent); margin-bottom: 8px;">Reproduction Attempts</h3>
      <div v-for="a in attempts" :key="a.id" class="ks-repro-status__attempt">
        <div class="ks-repro-status__attempt-header">
          <span class="ks-type-data" style="font-weight: 600;">{{ a.team }}</span>
          <KsTag :variant="a.success === 'full' ? 'primary' : a.success === 'partial' ? 'accent' : 'danger'">
            {{ a.success }}
          </KsTag>
        </div>
        <p class="ks-type-body-sm" style="color: var(--color-secondary);">{{ a.notes }}</p>
        <span class="ks-type-data">{{ a.date }}</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.ks-repro-status {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ks-repro-status__badge {
  font: 700 1.125rem / 1.4 var(--font-sans);
}

.ks-repro-status__checklist {
  display: flex;
  gap: 20px;
}

.ks-repro-status__check {
  display: flex;
  align-items: center;
  gap: 6px;
  font: 600 0.875rem / 1 var(--font-mono);
}

.ks-repro-status__attempts {
  padding-top: 14px;
  border-top: 1px solid var(--color-border);
}

.ks-repro-status__attempt {
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border);
}

.ks-repro-status__attempt:last-child {
  border-bottom: none;
}

.ks-repro-status__attempt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
</style>
