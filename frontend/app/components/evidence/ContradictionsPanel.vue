<script setup lang="ts">
/**
 * ContradictionsPanel — Shows conflicting claims across papers.
 */

export interface Contradiction {
  id: string
  claimA: { text: string; paper: string; year: number }
  claimB: { text: string; paper: string; year: number }
  severity: 'high' | 'medium' | 'low'
  resolved: boolean
}

export interface ContradictionsPanelProps {
  contradictions: Contradiction[]
}

defineProps<ContradictionsPanelProps>()

const uid = useId()

type TagVariant = 'danger' | 'warning' | 'neutral'

function sevVariant(s: Contradiction['severity']): TagVariant {
  const map: Record<Contradiction['severity'], TagVariant> = { high: 'danger', medium: 'warning', low: 'neutral' }
  return map[s]
}
</script>

<template>
  <section class="ks-contradictions ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <h2 :id="`${uid}-title`" class="ks-type-section-title">Contradictions</h2>

    <div class="ks-contradictions__list">
      <div
        v-for="c in contradictions"
        :key="c.id"
        :class="['ks-card ks-contradictions__item', { 'ks-contradictions__item--resolved': c.resolved }]"
      >
        <div class="ks-contradictions__header">
          <KsTag :variant="sevVariant(c.severity)">{{ c.severity }}</KsTag>
          <KsTag v-if="c.resolved" variant="success">resolved</KsTag>
        </div>
        <div class="ks-contradictions__claims">
          <blockquote class="ks-contradictions__claim">
            <p>"{{ c.claimA.text }}"</p>
            <cite class="ks-type-data">{{ c.claimA.paper }} ({{ c.claimA.year }})</cite>
          </blockquote>
          <span class="ks-contradictions__vs" aria-hidden="true">VS</span>
          <blockquote class="ks-contradictions__claim">
            <p>"{{ c.claimB.text }}"</p>
            <cite class="ks-type-data">{{ c.claimB.paper }} ({{ c.claimB.year }})</cite>
          </blockquote>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.ks-contradictions__list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.ks-contradictions__item { padding: 16px; }

.ks-contradictions__item--resolved { opacity: 0.6; }

.ks-contradictions__header {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.ks-contradictions__claims {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 12px;
  align-items: start;
}

.ks-contradictions__claim {
  margin: 0;
  padding: 0;
  font: 400 0.875rem / 1.5 var(--font-serif);
  color: var(--color-text);
}

.ks-contradictions__claim cite {
  display: block;
  margin-top: 4px;
  font-style: normal;
}

.ks-contradictions__vs {
  align-self: center;
  font: 700 0.75rem / 1 var(--font-mono);
  color: var(--color-secondary);
  padding: 4px 8px;
  border: 1px solid var(--color-border);
  border-radius: 2px;
}

@media (max-width: 640px) {
  .ks-contradictions__claims {
    grid-template-columns: 1fr;
  }
  .ks-contradictions__vs {
    text-align: center;
  }
}
</style>
