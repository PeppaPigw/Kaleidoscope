<script setup lang="ts">
/**
 * KsResearchIntent — Cross-page Research Intent Card.
 *
 * Displays the user's current research question or goal with structured
 * sub-questions, progress indicators, and quick actions. Appears in
 * Dashboard, Workspace, and Synthesis pages.
 *
 * @slot actions — Optional action buttons (e.g., Edit, Archive)
 */

export type ResearchQuestionStatus = "active" | "answered" | "parked";

export interface ResearchQuestion {
  id: string;
  text: string;
  status: ResearchQuestionStatus;
}

export interface KsResearchIntentProps {
  /** Primary research question / intent */
  title: string;
  /** Sub-questions under this intent */
  subQuestions?: ResearchQuestion[];
  /** Number of papers collected */
  paperCount?: number;
  /** Progress percentage (0–100) */
  progress?: number;
}

const props = withDefaults(defineProps<KsResearchIntentProps>(), {
  subQuestions: () => [],
  paperCount: 0,
  progress: 0,
});

const statusIcons: Record<ResearchQuestionStatus, string> = {
  active: "◉",
  answered: "✓",
  parked: "○",
};

const statusLabels: Record<ResearchQuestionStatus, string> = {
  active: "Active",
  answered: "Answered",
  parked: "Parked",
};

const progressPercent = computed(() =>
  Math.min(100, Math.max(0, props.progress)),
);
</script>

<template>
  <div class="ks-card ks-card--teal-top ks-research-intent">
    <div class="ks-research-intent__head">
      <span class="ks-type-eyebrow">Research Intent</span>
      <div v-if="$slots.actions" class="ks-research-intent__actions">
        <slot name="actions" />
      </div>
    </div>

    <h3 class="ks-research-intent__title ks-type-section-title">{{ title }}</h3>

    <!-- Sub-questions -->
    <ul
      v-if="subQuestions.length > 0"
      class="ks-research-intent__questions"
      aria-label="Sub-questions"
    >
      <li
        v-for="rq in subQuestions"
        :key="rq.id"
        :class="[
          'ks-research-intent__rq',
          `ks-research-intent__rq--${rq.status}`,
        ]"
      >
        <span class="ks-research-intent__rq-icon" aria-hidden="true">
          {{ statusIcons[rq.status] }}
        </span>
        <span>{{ rq.text }}</span>
        <span class="visually-hidden">({{ statusLabels[rq.status] }})</span>
      </li>
    </ul>

    <!-- Stats strip -->
    <div class="ks-research-intent__stats">
      <div class="ks-research-intent__stat">
        <span class="ks-type-data">{{ paperCount }}</span>
        <span class="ks-type-eyebrow">Papers</span>
      </div>
      <div class="ks-research-intent__progress">
        <div
          class="ks-research-intent__progress-bar"
          role="progressbar"
          :aria-valuenow="progressPercent"
          :aria-valuemin="0"
          :aria-valuemax="100"
          :aria-label="`Research progress: ${progressPercent}%`"
        >
          <div
            class="ks-research-intent__progress-fill"
            :style="{ width: `${progressPercent}%` }"
          />
        </div>
        <span class="ks-type-data">{{ progressPercent }}%</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ks-research-intent {
  padding: 20px 24px;
}

.ks-research-intent__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.ks-research-intent__actions {
  display: flex;
  gap: 6px;
}

.ks-research-intent__title {
  margin-bottom: 16px;
}

/* ─── Sub-questions ────────────────────────────────── */
.ks-research-intent__questions {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 18px;
}

.ks-research-intent__rq {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font: 400 0.875rem / 1.5 var(--font-serif);
  color: var(--color-text);
}

.ks-research-intent__rq--answered {
  text-decoration: line-through;
  color: var(--color-secondary);
}

.ks-research-intent__rq--parked {
  opacity: 0.56;
}

.ks-research-intent__rq-icon {
  flex-shrink: 0;
  font-size: 0.75rem;
  margin-top: 3px;
  color: var(--color-primary);
}

.ks-research-intent__rq--answered .ks-research-intent__rq-icon {
  color: #0f7b3f;
}

.ks-research-intent__rq--parked .ks-research-intent__rq-icon {
  color: var(--color-secondary);
}

/* ─── Stats ────────────────────────────────────────── */
.ks-research-intent__stats {
  display: flex;
  align-items: center;
  gap: 24px;
  padding-top: 14px;
  border-top: 1px solid var(--color-border);
}

.ks-research-intent__stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ks-research-intent__progress {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}

.ks-research-intent__progress-bar {
  flex: 1;
  height: 4px;
  background: var(--color-border);
  border-radius: 2px;
  overflow: hidden;
}

.ks-research-intent__progress-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 2px;
  transition: width var(--duration-normal) var(--ease-smooth);
}

/* ─── Utility ──────────────────────────────────────── */
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
