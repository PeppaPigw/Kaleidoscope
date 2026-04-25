<script setup lang="ts">
/**
 * RQHeader — Research question header for Evidence Lab.
 */
import { FileQuestion, Pencil, X } from "lucide-vue-next";

export interface RQHeaderProps {
  question: string;
  description: string;
  paperCount: number;
  claimCount: number;
}

const props = defineProps<RQHeaderProps>();

const emit = defineEmits<{
  save: [payload: { question: string; description: string }];
}>();

const uid = useId();
const dialogOpen = ref(false);
const draftQuestion = ref("");
const draftDescription = ref("");

watch(
  () => [props.question, props.description],
  (value) => {
    draftQuestion.value = value[0] ?? "";
    draftDescription.value = value[1] ?? "";
  },
  { immediate: true },
);

function openDialog() {
  draftQuestion.value = props.question;
  draftDescription.value = props.description;
  dialogOpen.value = true;
}

function closeDialog() {
  dialogOpen.value = false;
}

function submitDraft() {
  const nextQuestion = draftQuestion.value.trim();
  const nextDescription = draftDescription.value.trim();
  if (!nextQuestion) return;
  emit("save", {
    question: nextQuestion,
    description: nextDescription,
  });
  dialogOpen.value = false;
}
</script>

<template>
  <header
    class="ks-rq-header ks-motion-paper-reveal"
    :aria-labelledby="`${uid}-title`"
  >
    <div class="ks-rq-header__content">
      <p class="ks-type-eyebrow" style="color: var(--color-accent)">
        RESEARCH QUESTION
      </p>
      <h2 :id="`${uid}-title`" class="ks-rq-header__question">
        {{ question }}
      </h2>
      <p
        class="ks-type-body-sm"
        style="color: var(--color-secondary); margin-top: 4px"
      >
        {{ description }}
      </p>
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
      <KsButton variant="secondary" @click="openDialog">
        <template #icon-left>
          <Pencil :size="14" />
        </template>
        Edit RQ
      </KsButton>
    </div>
  </header>

  <Teleport to="body">
    <div
      v-if="dialogOpen"
      class="ks-rq-header__overlay"
      @click.self="closeDialog"
    >
      <div
        class="ks-rq-header__dialog"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="`${uid}-dialog-title`"
      >
        <div class="ks-rq-header__dialog-header">
          <div class="ks-rq-header__dialog-icon">
            <FileQuestion :size="16" />
          </div>
          <div class="ks-rq-header__dialog-copy">
            <h3 :id="`${uid}-dialog-title`" class="ks-rq-header__dialog-title">
              Edit Research Question
            </h3>
            <p class="ks-rq-header__dialog-subtitle">
              Refine the question and narrative framing for the current evidence
              analysis scope.
            </p>
          </div>
          <button
            type="button"
            class="ks-rq-header__dialog-close"
            aria-label="Close"
            @click="closeDialog"
          >
            <X :size="16" />
          </button>
        </div>

        <div class="ks-rq-header__dialog-body">
          <label class="ks-rq-header__field">
            <span class="ks-type-data">Research question</span>
            <textarea
              v-model="draftQuestion"
              rows="3"
              class="ks-rq-header__textarea"
              placeholder="State the question this evidence analysis should answer..."
            />
          </label>

          <label class="ks-rq-header__field">
            <span class="ks-type-data">Description</span>
            <textarea
              v-model="draftDescription"
              rows="4"
              class="ks-rq-header__textarea"
              placeholder="Add a concise framing note to explain what the comparison is testing."
            />
          </label>
        </div>

        <div class="ks-rq-header__dialog-footer">
          <KsButton variant="ghost" @click="closeDialog">Cancel</KsButton>
          <KsButton
            variant="primary"
            :disabled="!draftQuestion.trim()"
            @click="submitDraft"
          >
            Save
          </KsButton>
        </div>
      </div>
    </div>
  </Teleport>
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

.ks-rq-header__overlay {
  position: fixed;
  inset: 0;
  z-index: 320;
  background: rgba(10, 10, 10, 0.42);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.ks-rq-header__dialog {
  width: min(100%, 680px);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: 0 18px 52px rgba(0, 0, 0, 0.18);
  overflow: hidden;
}

.ks-rq-header__dialog-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 18px 20px 16px;
  border-bottom: 1px solid var(--color-border);
}

.ks-rq-header__dialog-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: rgba(13, 115, 119, 0.1);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ks-rq-header__dialog-copy {
  flex: 1;
  min-width: 0;
}

.ks-rq-header__dialog-title {
  font: 600 1rem / 1.25 var(--font-display);
  color: var(--color-text);
}

.ks-rq-header__dialog-subtitle {
  margin-top: 4px;
  color: var(--color-secondary);
  font: 400 0.875rem / 1.5 var(--font-serif);
}

.ks-rq-header__dialog-close {
  border: none;
  background: none;
  color: var(--color-secondary);
  cursor: pointer;
  padding: 4px;
}

.ks-rq-header__dialog-body {
  padding: 18px 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ks-rq-header__field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ks-rq-header__textarea {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  color: var(--color-text);
  padding: 12px 14px;
  font: 400 0.9375rem / 1.6 var(--font-serif);
  resize: vertical;
  min-height: 96px;
}

.ks-rq-header__textarea:focus {
  outline: 2px solid rgba(13, 115, 119, 0.16);
  border-color: var(--color-primary);
}

.ks-rq-header__dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px 18px;
  border-top: 1px solid var(--color-border);
}

@media (max-width: 640px) {
  .ks-rq-header__stats {
    width: 100%;
    justify-content: space-between;
  }

  .ks-rq-header__dialog {
    width: 100%;
  }
}
</style>
