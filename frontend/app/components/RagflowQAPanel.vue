<template>
  <div class="ragflow-qa-panel" :class="{ 'has-answer': !!answer }">
    <!-- Header -->
    <div class="qa-header">
      <div class="qa-brand">
        <div class="qa-brand-icon">
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>
        <span class="qa-brand-label">Ask AI</span>
      </div>
      <transition name="badge-fade">
        <span v-if="syncStatus" class="qa-badge" :class="syncStatus">
          <span class="qa-badge-dot" />
          {{ syncStatus === "ready" ? "Indexed" : "Syncing" }}
        </span>
      </transition>
    </div>

    <!-- Input -->
    <form class="qa-form" @submit.prevent="handleAsk">
      <div class="qa-input-wrap" :class="{ focused: inputFocused }">
        <svg
          class="qa-input-icon"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          v-model="question"
          type="text"
          class="qa-input"
          aria-label="Ask AI a question"
          :placeholder="placeholder || `Ask about this ${sourceLabel}…`"
          :disabled="loading"
          @focus="inputFocused = true"
          @blur="inputFocused = false"
        />
        <button
          type="submit"
          class="qa-submit"
          :disabled="!question.trim() || loading"
          :class="{ active: question.trim() }"
          aria-label="Submit question"
        >
          <svg
            v-if="!loading"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
          >
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
          <span v-else class="qa-btn-spinner" />
        </button>
      </div>
    </form>

    <!-- Loading -->
    <transition name="qa-slide">
      <div v-if="loading" class="qa-loading" role="status" aria-live="polite">
        <div class="qa-pulse-bar">
          <div class="qa-pulse-track" />
        </div>
        <span class="qa-loading-text">Searching {{ sourceLabel }}…</span>
      </div>
    </transition>

    <!-- Answer -->
    <transition name="qa-slide">
      <div v-if="answer" class="qa-answer-card">
        <div class="qa-answer-header">
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
            />
          </svg>
          <span>Answer</span>
          <div
            v-if="grounding"
            class="qa-grounding-pill"
            :class="{ good: grounding.grounded, weak: !grounding.grounded }"
          >
            <svg
              width="10"
              height="10"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="3"
            >
              <polyline v-if="grounding.grounded" points="20 6 9 17 4 12" />
              <line v-else x1="18" y1="6" x2="6" y2="18" />
            </svg>
            {{ Math.round(grounding.coverage * 100) }}% grounded
          </div>
        </div>
        <div class="qa-answer-body">
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div class="qa-answer-rich ks-prose" v-html="renderedAnswerHtml" />
        </div>
      </div>
    </transition>

    <!-- Sources -->
    <transition name="qa-slide">
      <div v-if="sources.length" class="qa-sources-card">
        <div class="qa-sources-header">
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
            />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          <span>Sources ({{ sources.length }})</span>
        </div>
        <div class="qa-sources-list">
          <div v-for="(src, i) in sources" :key="i" class="qa-source-chip">
            <div class="qa-source-rank">#{{ i + 1 }}</div>
            <div class="qa-source-content">
              {{ truncate(src.content, 180) }}
            </div>
            <div v-if="src.score" class="qa-source-score-bar">
              <div
                class="qa-score-fill"
                :style="{ width: `${Math.min(src.score * 100, 100)}%` }"
              />
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Error -->
    <transition name="qa-slide">
      <div
        v-if="error"
        class="qa-error-card"
        role="alert"
        aria-live="assertive"
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="15" y1="9" x2="9" y2="15" />
          <line x1="9" y1="9" x2="15" y2="15" />
        </svg>
        <span>{{ error }}</span>
      </div>
    </transition>

    <!-- Metadata -->
    <div v-if="latencyMs" class="qa-meta">
      <span class="qa-meta-item">⚡ {{ latencyMs }}ms</span>
      <span v-if="route" class="qa-meta-item">🔀 {{ route }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type {
  RagflowAskResponse,
  RoutedQueryResponse,
} from "~/composables/useRagflow";
import { ref, computed } from "vue";
import { renderRagflowAnswer } from "~/utils/ragflowAnswer";

const props = defineProps<{
  collectionId?: string;
  paperId?: string;
  placeholder?: string;
}>();

const { askWorkspace, askPaper, routedQuery, checkGrounding } = useRagflow();

const question = ref("");
const answer = ref<string | null>(null);
const renderedAnswerHtml = ref("");
const sources = ref<Array<{ content?: string; score?: number }>>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const latencyMs = ref<number | null>(null);
const route = ref<string | null>(null);
const syncStatus = ref<"ready" | "syncing" | null>(null);
const inputFocused = ref(false);
const grounding = ref<{
  grounded: boolean;
  coverage: number;
  sentences_checked: number;
  sentences_grounded: number;
} | null>(null);

const sourceLabel = computed(() =>
  props.collectionId ? "workspace" : props.paperId ? "paper" : "corpus",
);

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

async function applyAnswer(rawAnswer: string | null | undefined) {
  answer.value = rawAnswer ?? null;
  renderedAnswerHtml.value = "";

  if (!rawAnswer) return;

  try {
    renderedAnswerHtml.value = await renderRagflowAnswer(rawAnswer);
  } catch {
    renderedAnswerHtml.value = `<p>${escapeHtml(rawAnswer)}</p>`;
  }
}

async function handleAsk() {
  if (!question.value.trim()) return;
  loading.value = true;
  error.value = null;
  answer.value = null;
  renderedAnswerHtml.value = "";
  sources.value = [];
  grounding.value = null;
  latencyMs.value = null;
  route.value = null;

  try {
    let result: RagflowAskResponse;
    if (props.collectionId) {
      result = await askWorkspace(props.collectionId, question.value);
    } else if (props.paperId) {
      result = await askPaper(props.paperId, question.value);
    } else {
      const routedResult: RoutedQueryResponse = await routedQuery(
        question.value,
      );
      route.value = routedResult.route ?? null;
      await applyAnswer(routedResult.answer ?? null);
      sources.value = routedResult.sources ?? [];
      latencyMs.value = routedResult.latency_ms ?? null;
      if (routedResult.error) error.value = routedResult.error;
      return;
    }

    if (!result.enabled) {
      error.value = "RAGFlow is not enabled for this resource.";
      return;
    }
    if (result.ready === false) {
      syncStatus.value = "syncing";
      error.value = "Documents are still being indexed. Try again shortly.";
      return;
    }
    if (result.error) {
      error.value =
        result.error === "ragflow_unavailable"
          ? "RAGFlow service is temporarily unavailable."
          : result.error;
    }

    syncStatus.value = "ready";
    await applyAnswer(result.answer);
    sources.value = result.sources || [];
    latencyMs.value = result.latency_ms ?? null;

    if (result.answer && result.sources?.length) {
      try {
        grounding.value = await checkGrounding(
          result.answer,
          result.sources as Array<Record<string, unknown>>,
        );
      } catch {
        /* optional */
      }
    }
  } catch (caughtError: unknown) {
    error.value =
      caughtError instanceof Error
        ? caughtError.message
        : "Failed to get answer";
  } finally {
    loading.value = false;
  }
}

function truncate(text?: string | null, maxLen = 200) {
  if (!text) return "";
  return text.length > maxLen ? text.slice(0, maxLen) + "…" : text;
}
</script>

<style scoped>
.ragflow-qa-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  font-family: var(--font-sans, "Inter", system-ui, sans-serif);
}
/* Header */
.qa-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.qa-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}
.qa-brand-icon {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #6366f1, #a78bfa);
  border-radius: 8px;
  color: #fff;
}
.qa-brand-label {
  font: 600 0.9rem/1 var(--font-sans);
  color: var(--color-text, #e2e8f0);
  letter-spacing: -0.01em;
}
.qa-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  font: 500 0.65rem/1 var(--font-mono, monospace);
  padding: 3px 10px;
  border-radius: 100px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.qa-badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.qa-badge.ready {
  background: rgba(16, 185, 129, 0.12);
  color: #34d399;
}
.qa-badge.ready .qa-badge-dot {
  background: #34d399;
  box-shadow: 0 0 6px #34d399;
}
.qa-badge.syncing {
  background: rgba(251, 191, 36, 0.12);
  color: #fbbf24;
}
.qa-badge.syncing .qa-badge-dot {
  background: #fbbf24;
  animation: pulse-dot 1.2s infinite;
}
@keyframes pulse-dot {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

/* Input */
.qa-form {
  margin: 0;
}
.qa-input-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 6px 6px 14px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 12px;
  transition: all 0.2s ease;
}
.qa-input-wrap.focused {
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow:
    0 0 0 3px rgba(99, 102, 241, 0.1),
    0 2px 10px rgba(0, 0, 0, 0.15);
}
.qa-input-icon {
  color: rgba(148, 163, 184, 0.5);
  flex-shrink: 0;
}
.qa-input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font: 400 0.85rem/1.4 var(--font-sans);
  color: var(--color-text, #e2e8f0);
  min-width: 0;
}
.qa-input::placeholder {
  color: rgba(148, 163, 184, 0.4);
}
.qa-submit {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  background: rgba(148, 163, 184, 0.1);
  color: rgba(148, 163, 184, 0.4);
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.qa-submit.active {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
}
.qa-submit:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.qa-btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.5s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Loading */
.qa-loading {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.qa-pulse-bar {
  height: 3px;
  border-radius: 2px;
  background: rgba(99, 102, 241, 0.1);
  overflow: hidden;
}
.qa-pulse-track {
  width: 40%;
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, #6366f1, #a78bfa);
  animation: pulse-slide 1.2s ease-in-out infinite;
}
@keyframes pulse-slide {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(350%);
  }
}
.qa-loading-text {
  font: 400 0.75rem/1 var(--font-sans);
  color: rgba(148, 163, 184, 0.6);
}

/* Answer card */
.qa-answer-card {
  background: rgba(30, 41, 59, 0.45);
  border: 1px solid rgba(148, 163, 184, 0.1);
  border-radius: 12px;
  overflow: hidden;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
.qa-answer-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.08);
  font: 500 0.7rem/1 var(--font-mono, monospace);
  color: rgba(148, 163, 184, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.qa-grounding-pill {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 100px;
  font: 600 0.6rem/1 var(--font-mono);
}
.qa-grounding-pill.good {
  background: rgba(16, 185, 129, 0.12);
  color: #34d399;
}
.qa-grounding-pill.weak {
  background: rgba(239, 68, 68, 0.12);
  color: #f87171;
}
.qa-answer-body {
  padding: 14px;
}

.qa-answer-rich.ks-prose {
  max-width: none;
  font: 400 0.85rem/1.7 var(--font-serif, Georgia, serif);
  color: var(--color-text, #e2e8f0);
}

.qa-answer-rich :deep(p:first-child),
.qa-answer-rich :deep(ul:first-child),
.qa-answer-rich :deep(ol:first-child),
.qa-answer-rich :deep(blockquote:first-child) {
  margin-top: 0;
}

.qa-answer-rich :deep(p:last-child),
.qa-answer-rich :deep(ul:last-child),
.qa-answer-rich :deep(ol:last-child),
.qa-answer-rich :deep(blockquote:last-child) {
  margin-bottom: 0;
}

.qa-answer-rich :deep(p),
.qa-answer-rich :deep(ul),
.qa-answer-rich :deep(ol),
.qa-answer-rich :deep(blockquote) {
  color: inherit;
}

.qa-answer-rich :deep(li + li) {
  margin-top: 0.35rem;
}

.qa-answer-rich :deep(code) {
  background: rgba(148, 163, 184, 0.12);
}

.qa-answer-rich :deep(pre) {
  background: rgba(15, 23, 42, 0.55);
  border-color: rgba(148, 163, 184, 0.12);
}

/* Sources card */
.qa-sources-card {
  background: rgba(30, 41, 59, 0.3);
  border: 1px solid rgba(148, 163, 184, 0.08);
  border-radius: 12px;
  overflow: hidden;
}
.qa-sources-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.06);
  font: 500 0.7rem/1 var(--font-mono);
  color: rgba(148, 163, 184, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.qa-sources-list {
  display: flex;
  flex-direction: column;
}
.qa-source-chip {
  display: grid;
  grid-template-columns: 28px 1fr;
  gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.04);
  transition: background 0.15s ease;
}
.qa-source-chip:last-child {
  border-bottom: none;
}
.qa-source-chip:hover {
  background: rgba(99, 102, 241, 0.04);
}
.qa-source-rank {
  font: 700 0.7rem/28px var(--font-mono);
  color: rgba(99, 102, 241, 0.6);
  text-align: center;
}
.qa-source-content {
  font: 400 0.78rem/1.5 var(--font-serif);
  color: rgba(226, 232, 240, 0.8);
  word-break: break-word;
}
.qa-source-score-bar {
  grid-column: 2;
  height: 3px;
  border-radius: 2px;
  background: rgba(99, 102, 241, 0.1);
  margin-top: 4px;
}
.qa-score-fill {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, #6366f1, #a78bfa);
  transition: width 0.4s ease;
}

/* Error */
.qa-error-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.15);
  color: #f87171;
  font: 400 0.8rem/1.4 var(--font-sans);
}

/* Meta */
.qa-meta {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
.qa-meta-item {
  font: 400 0.65rem/1 var(--font-mono);
  color: rgba(148, 163, 184, 0.4);
}

/* Transitions */
.qa-slide-enter-active {
  animation: slide-in 0.3s ease;
}
.qa-slide-leave-active {
  animation: slide-in 0.2s ease reverse;
}
@keyframes slide-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.badge-fade-enter-active,
.badge-fade-leave-active {
  transition: opacity 0.3s ease;
}
.badge-fade-enter-from,
.badge-fade-leave-to {
  opacity: 0;
}
</style>
