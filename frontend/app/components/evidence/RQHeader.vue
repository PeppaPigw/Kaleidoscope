<script setup lang="ts">
/**
 * RQHeader — Research question header for Evidence Lab.
 */

export interface RQHeaderProps {
  question: string
  description: string
  paperCount: number
  claimCount: number
}

defineProps<RQHeaderProps>()
defineEmits<{ 'edit': [] }>()

const uid = useId()
</script>

<template>
  <header class="ks-rq-header ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <div class="ks-rq-header__content">
      <p class="ks-type-eyebrow" style="color: var(--color-accent);">RESEARCH QUESTION</p>
      <h2 :id="`${uid}-title`" class="ks-rq-header__question">{{ question }}</h2>
      <p class="ks-type-body-sm" style="color: var(--color-secondary); margin-top: 4px;">{{ description }}</p>
    </div>
    <div class="ks-rq-header__stats">
      <div class="ks-rq-header__stat">
        <span class="ks-rq-header__stat-value">{{ paperCount }}</span>
        <span class="ks-type-data">papers</span>
      </div>
      <div class="ks-rq-header__stat">
        <span class="ks-rq-header__stat-value">{{ claimCount }}</span>
        <span class="ks-type-data">claims</span>
      </div>
      <KsButton variant="secondary" @click="$emit('edit')">Edit RQ</KsButton>
    </div>
  </header>
</template>

<style scoped>
.ks-rq-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  padding: 24px 0;
  border-bottom: 1px solid var(--color-border);
  flex-wrap: wrap;
}

.ks-rq-header__question {
  font: 600 1.5rem / 1.3 var(--font-display);
  color: var(--color-text);
  margin-top: 4px;
}

.ks-rq-header__stats {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-shrink: 0;
}

.ks-rq-header__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.ks-rq-header__stat-value {
  font: 700 1.5rem / 1 var(--font-mono);
  color: var(--color-primary);
}
</style>
