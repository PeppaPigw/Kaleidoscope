<script setup lang="ts">
import { renderRagflowAnswer } from "~/utils/ragflowAnswer";
import { PAPER_QA_LOADING_STAGES, usePaperQA } from "~/composables/usePaperQA";

const props = defineProps<{
  paperId: string;
  pendingContext?: string | null;
}>();

const emit = defineEmits<{
  contextConsumed: [];
}>();

const paperId = computed(() => props.paperId);

const {
  status,
  errorMessage,
  history,
  preparing,
  asking,
  ask,
  prepare,
  newChat,
} = usePaperQA(paperId);

const inputText = ref("");
const inputFocused = ref(false);
const activeContext = ref<string | null>(null);

watch(
  () => props.pendingContext,
  (val) => {
    if (val) activeContext.value = val;
  },
  { immediate: true },
);

function dismissContext() {
  activeContext.value = null;
  emit("contextConsumed");
}
const historyRef = ref<HTMLElement | null>(null);
const renderedAnswers = ref<Record<string, string>>({});
const expandedSources = ref<Record<string, boolean>>({});

type LoadingStage = (typeof PAPER_QA_LOADING_STAGES)[number]["key"];

const isReady = computed(() => status.value === "completed");
const isBuilding = computed(
  () => status.value === "pending" || status.value === "running",
);
const isFailed = computed(() => status.value === "failed");
const canStartNewChat = computed(
  () => history.value.length > 0 && !asking.value,
);
const inputPlaceholder = computed(() => {
  if (isBuilding.value || preparing.value) return "Preparing paper index…";
  if (isFailed.value) return "Paper QA unavailable";
  return "Ask a question about this paper…";
});

const SUGGESTED_QUESTIONS = [
  "What is the main contribution?",
  "Explain the methodology",
  "What are the key results?",
];

const STAGE_INDEX = Object.fromEntries(
  PAPER_QA_LOADING_STAGES.map((stage, index) => [stage.key, index]),
) as Record<LoadingStage, number>;

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

async function handleSubmit() {
  const question = inputText.value.trim();
  if (!question || !isReady.value || asking.value) return;
  inputText.value = "";
  const ctx = activeContext.value ?? undefined;
  activeContext.value = null;
  emit("contextConsumed");
  await ask(question, ctx);
}

async function handleSuggestedQuestion(question: string) {
  inputText.value = question;
  await handleSubmit();
}

function handleNewChat() {
  if (!canStartNewChat.value) return;
  inputText.value = "";
  renderedAnswers.value = {};
  expandedSources.value = {};
  newChat();
}

function stageState(stageKey: LoadingStage, currentStage: LoadingStage) {
  const currentIndex = STAGE_INDEX[currentStage];
  const stageIndex = STAGE_INDEX[stageKey];
  if (stageIndex < currentIndex) return "done";
  if (stageIndex === currentIndex) return "active";
  return "pending";
}

function sourceColor(normalized: string): string {
  const map: Record<string, string> = {
    abstract: "#6366f1",
    introduction: "#0ea5e9",
    method: "#10b981",
    methodology: "#10b981",
    experiments: "#f59e0b",
    evaluation: "#f59e0b",
    results: "#ec4899",
    conclusion: "#8b5cf6",
    appendix: "#64748b",
  };
  for (const [key, color] of Object.entries(map)) {
    if (normalized.includes(key)) return color;
  }
  return "#94a3b8";
}

function toggleSources(itemId: string) {
  expandedSources.value[itemId] = !expandedSources.value[itemId];
}

function sourcesExpanded(itemId: string): boolean {
  return expandedSources.value[itemId] ?? false;
}

function compactMathExpression(expression: string): string {
  return expression
    .replace(/\s+/g, " ")
    .replace(/\s*([{}[\]()_^=,+\-*/%])\s*/g, "$1")
    .replace(/([0-9])\s+(?=[0-9])/g, "$1")
    .replace(/\s+([.,%])/g, "$1")
    .replace(/\\\s+/g, "\\")
    .trim();
}

function normalizeInlineMathSpacing(value: string): string {
  return value
    .replace(
      /\$([^$]+)\$/g,
      (_, expression: string) => `$${compactMathExpression(expression)}$`,
    )
    .replace(
      /\\\((.+?)\\\)/g,
      (_, expression: string) => `\\(${compactMathExpression(expression)}\\)`,
    );
}

function displaySourceSnippet(value: string): string {
  return normalizeInlineMathSpacing(value);
}

async function scrollHistoryToBottom() {
  await nextTick();
  const el = historyRef.value;
  if (!el) return;
  el.scrollTop = el.scrollHeight;
}

watch(
  history,
  async (items) => {
    const activeIds = new Set(items.map((item) => item.id));
    renderedAnswers.value = Object.fromEntries(
      Object.entries(renderedAnswers.value).filter(([id]) => activeIds.has(id)),
    );
    expandedSources.value = Object.fromEntries(
      Object.entries(expandedSources.value).filter(
        ([id, expanded]) => activeIds.has(id) && expanded,
      ),
    );

    for (const item of items) {
      if (item.answer && !renderedAnswers.value[item.id]) {
        try {
          renderedAnswers.value[item.id] = await renderRagflowAnswer(
            item.answer,
          );
        } catch {
          renderedAnswers.value[item.id] = `<p>${escapeHtml(item.answer)}</p>`;
        }
      }
    }

    await scrollHistoryToBottom();
  },
  { deep: true },
);
</script>

<template>
  <div class="pqa-panel">
    <div class="pqa-topbar">
      <button
        type="button"
        class="pqa-new-chat"
        :disabled="!canStartNewChat"
        @click="handleNewChat"
      >
        <span class="pqa-new-chat-icon" aria-hidden="true">
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="12" cy="12" r="9" />
            <line x1="12" y1="8" x2="12" y2="16" />
            <line x1="8" y1="12" x2="16" y2="12" />
          </svg>
        </span>
        <span>New Chat</span>
      </button>
    </div>
    <div class="pqa-topbar-divider" />

    <transition name="qa-slide">
      <div v-if="isBuilding || preparing" class="pqa-preparing">
        <div class="pqa-pulse-bar">
          <div class="pqa-pulse-track" />
        </div>
        <span class="pqa-preparing-text">Preparing paper index…</span>
      </div>
    </transition>

    <transition name="qa-slide">
      <div v-if="isFailed" class="pqa-error-card">
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        <span>{{ errorMessage || "Indexing failed." }}</span>
        <button class="pqa-retry-btn" @click="prepare">Retry</button>
      </div>
    </transition>

    <div ref="historyRef" class="pqa-history">
      <transition name="qa-slide">
        <div v-if="isReady && history.length === 0" class="pqa-empty">
          <div class="pqa-empty-icon">
            <svg
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path
                d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
              />
            </svg>
          </div>
          <p class="pqa-empty-title">Start a paper chat</p>
          <p class="pqa-empty-hint">Ask anything about this paper</p>
          <div class="pqa-suggestions">
            <button
              v-for="question in SUGGESTED_QUESTIONS"
              :key="question"
              class="pqa-suggestion-btn"
              @click="handleSuggestedQuestion(question)"
            >
              {{ question }}
            </button>
          </div>
        </div>
      </transition>

      <transition-group name="qa-item" tag="div" class="pqa-items">
        <div v-for="item in history" :key="item.id" class="pqa-item">
          <div class="pqa-question">
            <span class="pqa-question-text">{{ item.question }}</span>
          </div>

          <div
            v-if="item.loading && !item.streamingAnswer"
            class="pqa-progress-card"
          >
            <div class="pqa-progress-visual">
              <div class="pqa-progress-spinner">
                <span class="pqa-spinner-orbit pqa-spinner-orbit--one" />
                <span class="pqa-spinner-orbit pqa-spinner-orbit--two" />
                <span class="pqa-spinner-orbit pqa-spinner-orbit--three" />
                <span class="pqa-spinner-core" />
              </div>
            </div>
            <div class="pqa-progress-steps">
              <div
                v-for="stage in PAPER_QA_LOADING_STAGES"
                :key="stage.key"
                class="pqa-progress-step"
                :class="`pqa-progress-step--${stageState(stage.key, item.loadingStage)}`"
              >
                <span class="pqa-progress-dot" />
                <span>{{ stage.label }}</span>
              </div>
            </div>
          </div>

          <div
            v-else-if="item.loading && item.streamingAnswer"
            class="pqa-answer-card"
          >
            <div class="pqa-answer-body">
              <div class="pqa-streaming-text">
                {{ item.streamingAnswer }}<span class="pqa-cursor" />
              </div>
            </div>
          </div>

          <div v-else-if="item.error" class="pqa-answer-error">
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {{ item.error }}
          </div>

          <div v-else-if="item.answer" class="pqa-answer-card">
            <div class="pqa-answer-body">
              <!-- eslint-disable-next-line vue/no-v-html -->
              <div
                class="pqa-answer-rich ks-prose"
                v-html="renderedAnswers[item.id] || item.answer"
              />
            </div>

            <div v-if="item.sources.length" class="pqa-sources">
              <button
                type="button"
                class="pqa-sources-header"
                @click="toggleSources(item.id)"
              >
                <span>Sources</span>
                <span class="pqa-sources-header-meta">{{
                  item.sources.length
                }}</span>
                <svg
                  class="pqa-sources-caret"
                  :class="{
                    'pqa-sources-caret--open': sourcesExpanded(item.id),
                  }"
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  aria-hidden="true"
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </button>
              <div v-if="sourcesExpanded(item.id)" class="pqa-sources-list">
                <div
                  v-for="(src, index) in item.sources"
                  :key="`${item.id}-source-${index}`"
                  class="pqa-source-item"
                >
                  <div class="pqa-source-head">
                    <span class="pqa-source-index">[{{ index + 1 }}]</span>
                    <span
                      class="pqa-section-chip"
                      :style="{
                        borderColor: sourceColor(src.normalized_section),
                        color: sourceColor(src.normalized_section),
                      }"
                    >
                      {{ src.section_title }}
                    </span>
                  </div>
                  <p class="pqa-source-snippet">
                    {{ displaySourceSnippet(src.text_snippet) }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </transition-group>
    </div>

    <form class="pqa-form" @submit.prevent="handleSubmit">
      <div
        class="pqa-input-wrap"
        :class="{
          'pqa-input-wrap--focused': inputFocused,
          'pqa-input-wrap--has-context': activeContext,
        }"
      >
        <!-- Context quote row -->
        <div v-if="activeContext" class="pqa-context-row">
          <svg
            class="pqa-context-arrow"
            width="13"
            height="13"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <polyline points="4 6 4 12 12 12" />
            <line x1="4" y1="12" x2="13" y2="3" />
          </svg>
          <span class="pqa-context-quote">"{{ activeContext }}"</span>
          <button
            type="button"
            class="pqa-context-dismiss"
            aria-label="Clear context"
            @click="dismissContext"
          >
            <svg
              width="11"
              height="11"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              stroke-width="2.2"
              stroke-linecap="round"
            >
              <line x1="4" y1="4" x2="12" y2="12" />
              <line x1="12" y1="4" x2="4" y2="12" />
            </svg>
          </button>
        </div>
        <div v-if="activeContext" class="pqa-context-sep" />

        <!-- Input row -->
        <div class="pqa-input-row">
          <svg
            class="pqa-input-icon"
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            v-model="inputText"
            type="text"
            class="pqa-input"
            :placeholder="inputPlaceholder"
            :disabled="!isReady || asking"
            aria-label="Ask a question about this paper"
            @focus="inputFocused = true"
            @blur="inputFocused = false"
            @keydown.enter.prevent="handleSubmit"
          />
          <button
            type="submit"
            class="pqa-submit"
            :disabled="!isReady || asking || !inputText.trim()"
            :class="{
              'pqa-submit--active': isReady && inputText.trim() && !asking,
            }"
            aria-label="Submit question"
          >
            <svg
              v-if="!asking"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
            >
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
            <span v-else class="pqa-submit-spinner" />
          </button>
        </div>
      </div>
    </form>
  </div>
</template>

<style scoped>
.pqa-panel {
  --pqa-progress-done-color: #2f5d57;
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.pqa-topbar {
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}

.pqa-topbar-divider {
  height: 1px;
  flex-shrink: 0;
  background: color-mix(in srgb, var(--color-border) 88%, transparent);
}

.pqa-new-chat {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid
    color-mix(in srgb, var(--color-primary) 28%, var(--color-border));
  background: color-mix(in srgb, var(--color-primary) 8%, transparent);
  color: var(--color-text);
  font: 600 0.72rem / 1 var(--font-mono, monospace);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  cursor: pointer;
  transition:
    background 0.15s ease,
    border-color 0.15s ease,
    opacity 0.15s ease;
}

.pqa-new-chat-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
}

.pqa-new-chat:hover:not(:disabled) {
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
  border-color: color-mix(
    in srgb,
    var(--color-primary) 44%,
    var(--color-border)
  );
}

.pqa-new-chat:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pqa-preparing {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
}

.pqa-pulse-bar {
  height: 3px;
  border-radius: 2px;
  background: var(--color-border);
  overflow: hidden;
  position: relative;
}

.pqa-pulse-track {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, #6366f1 50%, transparent);
  animation: pulse-slide 1.6s ease-in-out infinite;
}

@keyframes pulse-slide {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(200%);
  }
}

.pqa-preparing-text {
  font: 400 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
  text-align: center;
}

.pqa-error-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: rgba(248, 113, 113, 0.08);
  border: 1px solid rgba(248, 113, 113, 0.2);
  border-radius: 8px;
  font: 400 0.8rem / 1.4 var(--font-sans);
  color: #f87171;
  flex-shrink: 0;
}

.pqa-retry-btn {
  margin-left: auto;
  padding: 4px 10px;
  background: rgba(248, 113, 113, 0.15);
  border: 1px solid rgba(248, 113, 113, 0.4);
  border-radius: 5px;
  color: #f87171;
  font: 600 0.75rem / 1 var(--font-sans);
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
}

.pqa-retry-btn:hover {
  background: rgba(248, 113, 113, 0.28);
}

.pqa-history {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 8px;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) transparent;
}

.pqa-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 6px;
  padding: 24px 8px;
  color: var(--color-secondary);
}

.pqa-empty-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface, rgba(30, 41, 59, 0.4));
  border: 1px solid var(--color-border);
  border-radius: 12px;
  margin-bottom: 4px;
}

.pqa-empty-title {
  font: 600 0.875rem / 1 var(--font-sans);
  color: var(--color-text);
  margin: 0;
}

.pqa-empty-hint {
  font: 400 0.8rem / 1.4 var(--font-sans);
  margin: 0;
  color: var(--color-secondary);
}

.pqa-suggestions {
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 100%;
  margin-top: 8px;
}

.pqa-suggestion-btn {
  padding: 7px 10px;
  background: var(--color-surface, rgba(30, 41, 59, 0.4));
  border: 1px solid var(--color-border);
  border-radius: 10px;
  color: var(--color-secondary);
  font: 400 0.8rem / 1.3 var(--font-sans);
  text-align: left;
  cursor: pointer;
  transition:
    background 0.15s,
    color 0.15s,
    border-color 0.15s;
}

.pqa-suggestion-btn:hover {
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
  border-color: color-mix(in srgb, var(--color-primary) 40%, transparent);
  color: var(--color-text);
}

.pqa-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pqa-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.pqa-question {
  display: flex;
  justify-content: flex-end;
}

.pqa-question-text {
  max-width: 88%;
  padding: 7px 11px;
  background: color-mix(in srgb, var(--color-primary) 15%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-primary) 25%, transparent);
  border-radius: 14px 14px 4px 14px;
  font: 400 0.8375rem / 1.4 var(--font-sans);
  color: var(--color-text);
}

.pqa-progress-card {
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr);
  gap: 10px;
  align-items: center;
  width: min(100%, 320px);
  padding: 10px 12px;
  background: color-mix(
    in srgb,
    var(--color-surface, rgba(30, 41, 59, 0.45)) 92%,
    transparent
  );
  border: 1px solid
    color-mix(in srgb, var(--color-primary) 20%, var(--color-border));
  border-radius: 14px 14px 14px 4px;
  backdrop-filter: blur(10px);
}

.pqa-progress-visual {
  display: flex;
  align-items: center;
  justify-content: center;
}

.pqa-progress-spinner {
  position: relative;
  width: 38px;
  height: 38px;
}

.pqa-spinner-core {
  position: absolute;
  inset: 12px;
  border-radius: 50%;
  background: linear-gradient(135deg, #60a5fa, #818cf8);
  box-shadow: 0 0 16px rgba(129, 140, 248, 0.35);
}

.pqa-spinner-orbit {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px solid rgba(129, 140, 248, 0.2);
  animation: orbit-spin 3.2s linear infinite;
}

.pqa-spinner-orbit::after {
  content: "";
  position: absolute;
  top: -2px;
  left: 50%;
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: #c4b5fd;
  box-shadow: 0 0 8px rgba(196, 181, 253, 0.45);
  transform: translateX(-50%);
}

.pqa-spinner-orbit--two {
  inset: 4px;
  animation-duration: 2.4s;
  animation-direction: reverse;
}

.pqa-spinner-orbit--three {
  inset: 8px;
  animation-duration: 1.8s;
}

@keyframes orbit-spin {
  to {
    transform: rotate(360deg);
  }
}

.pqa-progress-steps {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.pqa-progress-step {
  display: flex;
  align-items: center;
  gap: 6px;
  font: 500 0.68rem / 1.35 var(--font-sans);
  color: rgba(148, 163, 184, 0.62);
}

.pqa-progress-step--active {
  color: var(--color-text);
}

.pqa-progress-step--done {
  color: var(--pqa-progress-done-color);
}

.pqa-progress-dot {
  width: 6px;
  height: 6px;
  flex-shrink: 0;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.38;
}

.pqa-progress-step--active .pqa-progress-dot {
  opacity: 1;
  box-shadow: 0 0 8px color-mix(in srgb, currentColor 45%, transparent);
}

.pqa-answer-error {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 10px;
  background: rgba(248, 113, 113, 0.07);
  border: 1px solid rgba(248, 113, 113, 0.18);
  border-radius: 10px;
  font: 400 0.8rem / 1.4 var(--font-sans);
  color: #f87171;
}

.pqa-answer-card {
  background: var(--color-surface, rgba(30, 41, 59, 0.45));
  border: 1px solid var(--color-border);
  border-radius: 14px 14px 14px 4px;
  overflow: hidden;
  backdrop-filter: blur(8px);
}

.pqa-answer-body {
  padding: 12px 14px;
}

.pqa-streaming-text {
  font: 400 0.85rem / 1.7 var(--font-serif, Georgia, serif);
  color: var(--color-text);
  white-space: pre-wrap;
  word-break: break-word;
  padding: 12px 14px;
}

.pqa-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: currentColor;
  margin-left: 1px;
  vertical-align: text-bottom;
  opacity: 0.8;
  animation: pqa-blink 0.75s step-end infinite;
}

@keyframes pqa-blink {
  0%,
  100% {
    opacity: 0.8;
  }
  50% {
    opacity: 0;
  }
}

.pqa-answer-rich.ks-prose {
  max-width: none;
  font: 400 0.85rem / 1.7 var(--font-serif, Georgia, serif);
  color: var(--color-text);
}

.pqa-answer-rich :deep(p:first-child),
.pqa-answer-rich :deep(ul:first-child),
.pqa-answer-rich :deep(ol:first-child),
.pqa-answer-rich :deep(blockquote:first-child) {
  margin-top: 0;
}

.pqa-answer-rich :deep(p:last-child),
.pqa-answer-rich :deep(ul:last-child),
.pqa-answer-rich :deep(ol:last-child),
.pqa-answer-rich :deep(blockquote:last-child) {
  margin-bottom: 0;
}

.pqa-answer-rich :deep(p),
.pqa-answer-rich :deep(ul),
.pqa-answer-rich :deep(ol),
.pqa-answer-rich :deep(blockquote) {
  color: inherit;
}

.pqa-answer-rich :deep(p) {
  overflow-wrap: break-word;
  word-break: normal;
}

.pqa-answer-rich :deep(li + li) {
  margin-top: 0.35rem;
}

.pqa-answer-rich :deep(code) {
  background: rgba(148, 163, 184, 0.12);
}

.pqa-answer-rich :deep(pre) {
  background: rgba(15, 23, 42, 0.55);
  border-color: rgba(148, 163, 184, 0.12);
}

.pqa-answer-rich :deep(mjx-container:not([display])) {
  display: inline-block !important;
  vertical-align: -0.15em;
  line-height: 0;
  white-space: nowrap;
}

.pqa-answer-rich :deep(mjx-container[display="true"]) {
  display: block !important;
  line-height: 1;
  margin: 1em auto;
  text-align: center;
  overflow-x: auto;
}

.pqa-answer-rich :deep(mjx-container svg) {
  display: inline-block;
  vertical-align: middle;
  overflow: visible;
}

.pqa-answer-rich :deep(mjx-math) {
  display: inline-block;
}

.pqa-sources {
  border-top: 1px solid var(--color-border);
}

.pqa-sources-header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 9px 14px;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  font: 600 0.68rem / 1 var(--font-mono);
  color: var(--color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.pqa-sources-header-meta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
  color: var(--color-text);
}

.pqa-sources-caret {
  margin-left: auto;
  transition: transform 0.16s ease;
}

.pqa-sources-caret--open {
  transform: rotate(180deg);
}

.pqa-sources-list {
  padding: 0 14px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.pqa-source-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.pqa-source-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pqa-source-index {
  font: 700 0.68rem / 1 var(--font-mono);
  color: var(--color-primary);
}

.pqa-section-chip {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border: 1px solid;
  border-radius: 999px;
  font: 500 0.7rem / 1.4 var(--font-mono);
  width: fit-content;
}

.pqa-source-snippet {
  font: 400 0.775rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.pqa-form {
  flex-shrink: 0;
  padding-top: 8px;
  border-top: 1px solid color-mix(in srgb, var(--color-border) 85%, transparent);
}

.pqa-input-wrap {
  display: flex;
  flex-direction: column;
  background: var(--color-surface, rgba(30, 41, 59, 0.5));
  border: 1px solid var(--color-border);
  border-radius: 14px;
  overflow: hidden;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.pqa-input-wrap--focused {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px
    color-mix(in srgb, var(--color-primary) 12%, transparent);
}

/* ── Context quote row ─────────────────────────── */
.pqa-context-row {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 9px 10px 9px 12px;
}

.pqa-context-arrow {
  flex-shrink: 0;
  color: var(--color-secondary);
  opacity: 0.7;
}

.pqa-context-quote {
  flex: 1;
  min-width: 0;
  font: 400 0.775rem / 1.45 var(--font-sans);
  color: var(--color-secondary);
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  word-break: break-word;
}

.pqa-context-dismiss {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  background: none;
  border: none;
  color: var(--color-secondary);
  cursor: pointer;
  border-radius: 50%;
  opacity: 0.55;
  transition:
    opacity 0.13s,
    background 0.13s;
}

.pqa-context-dismiss:hover {
  opacity: 1;
  background: rgba(148, 163, 184, 0.12);
}

.pqa-context-sep {
  height: 1px;
  background: color-mix(in srgb, var(--color-border) 75%, transparent);
  margin: 0 10px;
}

/* ── Input row ──────────────────────────────────── */
.pqa-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 8px 8px 12px;
}

.pqa-input-icon {
  color: var(--color-secondary);
  flex-shrink: 0;
}

.pqa-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  font: 400 0.875rem / 1.4 var(--font-sans);
  color: var(--color-text);
  min-width: 0;
}

.pqa-input::placeholder {
  color: var(--color-secondary);
  opacity: 0.7;
}

.pqa-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pqa-submit {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--color-border);
  border: none;
  border-radius: 10px;
  color: var(--color-secondary);
  cursor: pointer;
  flex-shrink: 0;
  transition:
    background 0.15s,
    color 0.15s,
    transform 0.1s;
}

.pqa-submit--active {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
}

.pqa-submit--active:hover {
  transform: scale(1.04);
}

.pqa-submit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pqa-submit-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.28);
  border-top-color: #fff;
  border-radius: 50%;
  animation: submit-spin 0.55s linear infinite;
}

@keyframes submit-spin {
  to {
    transform: rotate(360deg);
  }
}

.qa-slide-enter-active {
  transition:
    opacity 0.25s ease,
    transform 0.25s ease;
}

.qa-slide-leave-active {
  transition: opacity 0.15s ease;
}

.qa-slide-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.qa-slide-leave-to {
  opacity: 0;
}

.qa-item-enter-active {
  transition: all 0.25s ease;
}

.qa-item-leave-active {
  transition: all 0.18s ease;
  position: absolute;
  width: calc(100% - 1px);
}

.qa-item-enter-from,
.qa-item-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

.qa-item-move {
  transition: transform 0.25s ease;
}

@media (max-width: 640px) {
  .pqa-question-text {
    max-width: 94%;
  }

  .pqa-progress-card {
    width: 100%;
    grid-template-columns: 44px minmax(0, 1fr);
    padding: 10px;
  }

  .pqa-answer-body,
  .pqa-sources-header,
  .pqa-sources-list {
    padding-left: 10px;
    padding-right: 10px;
  }
}
</style>
