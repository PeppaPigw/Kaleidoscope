<script setup lang="ts">
/**
 * DiscoverAiAssistantDrawer — Slide-out drawer for AI research assistant.
 *
 * Chat interface for querying and analyzing arXiv papers through an AI agent.
 * Follows KsProvenanceDrawer pattern for transitions, focus management, and WCAG compliance.
 */
import { X, Bot, Send, Loader2 } from "lucide-vue-next";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  papersLoaded?: number;
}

interface Props {
  open: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits<{ close: [] }>();

const { agentQuery } = useDeepXiv();

// ── State ────────────────────────────────────────────────
const messages = ref<ChatMessage[]>([]);
const input = ref("");
const isLoading = ref(false);
const error = ref<string | null>(null);
const messagesEnd = ref<HTMLElement | null>(null);
const drawerRef = ref<HTMLElement | null>(null);
const previousFocus = ref<HTMLElement | null>(null);

// ── Computed ─────────────────────────────────────────────
const canSend = computed(
  () => input.value.trim().length > 0 && !isLoading.value,
);

// ── Actions ──────────────────────────────────────────────
async function scrollToBottom() {
  await nextTick();
  messagesEnd.value?.scrollIntoView({ behavior: "smooth" });
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text || isLoading.value) return;

  error.value = null;
  messages.value.push({ role: "user", content: text });
  input.value = "";
  isLoading.value = true;
  await scrollToBottom();

  try {
    const res = await agentQuery(text);
    messages.value.push({
      role: "assistant",
      content: res.answer,
      papersLoaded: res.papers_loaded,
    });
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Agent query failed";
    messages.value.push({
      role: "assistant",
      content:
        "Sorry, an error occurred while processing your query. Please try again.",
    });
  } finally {
    isLoading.value = false;
    await scrollToBottom();
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    void sendMessage();
  }
}

function handleSuggestionClick(text: string) {
  input.value = text;
  void sendMessage();
}

// ── Focus management ─────────────────────────────────────
function handleEscape(e: KeyboardEvent) {
  if (e.key === "Escape") {
    emit("close");
  }
}

function trapFocus(e: KeyboardEvent) {
  if (e.key !== "Tab" || !drawerRef.value) return;

  const focusable = drawerRef.value.querySelectorAll<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
  );
  if (focusable.length === 0) return;

  const first = focusable[0]!;
  const last = focusable[focusable.length - 1]!;

  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault();
    last.focus();
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault();
    first.focus();
  }
}

function onDrawerEnter() {
  previousFocus.value = document.activeElement as HTMLElement | null;
  nextTick(() => {
    const inputEl = drawerRef.value?.querySelector<HTMLElement>("input");
    inputEl?.focus();
  });
}

function onDrawerLeave() {
  previousFocus.value?.focus();
  previousFocus.value = null;
}

// ── Lifecycle ────────────────────────────────────────────
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.addEventListener("keydown", trapFocus);
    } else {
      document.removeEventListener("keydown", handleEscape);
      document.removeEventListener("keydown", trapFocus);
    }
  },
);

onUnmounted(() => {
  document.removeEventListener("keydown", handleEscape);
  document.removeEventListener("keydown", trapFocus);
});
</script>

<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <Transition name="ks-fade">
      <div v-if="open" class="ks-ai-drawer__backdrop" @click="emit('close')" />
    </Transition>

    <!-- Drawer panel -->
    <Transition
      name="ks-drawer"
      @enter="onDrawerEnter"
      @after-leave="onDrawerLeave"
    >
      <aside
        v-if="open"
        ref="drawerRef"
        class="ks-ai-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ai-drawer-title"
      >
        <!-- Header -->
        <header class="ks-ai-drawer__header">
          <div class="ks-ai-drawer__header-left">
            <Bot :size="20" class="ks-ai-drawer__icon" />
            <h2 id="ai-drawer-title" class="ks-ai-drawer__title">
              Research Assistant
            </h2>
          </div>
          <button
            type="button"
            class="ks-ai-drawer__close"
            aria-label="Close assistant"
            @click="emit('close')"
          >
            <X :size="18" />
          </button>
        </header>

        <!-- Chat area -->
        <div class="ks-ai-drawer__chat">
          <!-- Empty state -->
          <div
            v-if="messages.length === 0 && !isLoading"
            class="ks-ai-drawer__empty"
          >
            <Bot :size="32" class="ks-ai-drawer__empty-icon" />
            <h3 class="ks-ai-drawer__empty-title">
              Start a research conversation
            </h3>
            <p class="ks-ai-drawer__empty-text">
              Ask about specific papers, compare methodologies, or explore
              research topics.
            </p>
            <div class="ks-ai-drawer__suggestions">
              <button
                class="ks-ai-drawer__suggestion"
                @click="
                  handleSuggestionClick(
                    'What are the latest advances in large language models?',
                  )
                "
              >
                Latest advances in LLMs
              </button>
              <button
                class="ks-ai-drawer__suggestion"
                @click="
                  handleSuggestionClick(
                    'Find papers on retrieval-augmented generation',
                  )
                "
              >
                Papers on RAG
              </button>
              <button
                class="ks-ai-drawer__suggestion"
                @click="
                  handleSuggestionClick(
                    'Summarize recent work on multimodal AI',
                  )
                "
              >
                Multimodal AI research
              </button>
            </div>
          </div>

          <!-- Messages -->
          <div v-else class="ks-ai-drawer__messages">
            <DeepxivAgentChatMessage
              v-for="(msg, i) in messages"
              :key="i"
              :role="msg.role"
              :content="msg.content"
              :papers-loaded="msg.papersLoaded"
            />

            <!-- Thinking indicator -->
            <div v-if="isLoading" class="ks-ai-drawer__thinking">
              <Loader2 :size="14" class="ks-ai-drawer__spinner" />
              <span>Thinking...</span>
            </div>

            <!-- Error -->
            <div v-if="error" class="ks-ai-drawer__error">
              {{ error }}
            </div>

            <div ref="messagesEnd" />
          </div>
        </div>

        <!-- Input area -->
        <div class="ks-ai-drawer__input-area">
          <div class="ks-ai-drawer__input-row">
            <input
              v-model="input"
              type="text"
              class="ks-ai-drawer__input"
              placeholder="Ask about papers, methods, findings..."
              :disabled="isLoading"
              @keydown="handleKeydown"
            />
            <button
              class="ks-ai-drawer__send-btn"
              :disabled="!canSend"
              @click="sendMessage"
            >
              <Loader2
                v-if="isLoading"
                :size="14"
                class="ks-ai-drawer__spinner"
              />
              <Send v-else :size="14" />
            </button>
          </div>
          <p class="ks-ai-drawer__input-hint">Press Enter to send</p>
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* ── Backdrop ──────────────────────────────────────────── */
.ks-ai-drawer__backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(2px);
  z-index: 299;
}

/* ── Drawer panel ──────────────────────────────────────── */
.ks-ai-drawer {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: min(480px, 90vw);
  background: var(--color-bg);
  border-left: 1px solid var(--color-border);
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.12);
  z-index: 300;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Header ────────────────────────────────────────────── */
.ks-ai-drawer__header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
}

.ks-ai-drawer__header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ks-ai-drawer__icon {
  color: var(--color-primary);
  flex-shrink: 0;
}

.ks-ai-drawer__title {
  font: 600 1rem / 1 var(--font-sans);
  color: var(--color-text);
  margin: 0;
}

.ks-ai-drawer__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  color: var(--color-secondary);
  cursor: pointer;
  border-radius: 6px;
  transition:
    background var(--duration-fast) var(--ease-smooth),
    color var(--duration-fast) var(--ease-smooth);
}

.ks-ai-drawer__close:hover {
  background: var(--color-border);
  color: var(--color-text);
}

/* ── Chat area ─────────────────────────────────────────── */
.ks-ai-drawer__chat {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: color-mix(in srgb, var(--color-secondary) 30%, transparent)
    transparent;
}

.ks-ai-drawer__chat::-webkit-scrollbar {
  width: 4px;
}

.ks-ai-drawer__chat::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--color-secondary) 30%, transparent);
  border-radius: 9999px;
}

/* ── Empty state ───────────────────────────────────────── */
.ks-ai-drawer__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 32px 24px;
  text-align: center;
}

.ks-ai-drawer__empty-icon {
  color: var(--color-border);
  margin-bottom: 12px;
}

.ks-ai-drawer__empty-title {
  font: 600 1rem / 1.3 var(--font-sans);
  color: var(--color-text);
  margin: 0 0 6px;
}

.ks-ai-drawer__empty-text {
  font: 400 0.8125rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  max-width: 320px;
  margin: 0 0 20px;
}

.ks-ai-drawer__suggestions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  max-width: 320px;
}

.ks-ai-drawer__suggestion {
  padding: 10px 16px;
  border: 1px solid var(--color-border);
  background: none;
  border-radius: 8px;
  font: 400 0.8125rem / 1.3 var(--font-sans);
  color: var(--color-text);
  text-align: left;
  cursor: pointer;
  transition:
    border-color var(--duration-fast) var(--ease-smooth),
    background var(--duration-fast) var(--ease-smooth);
}

.ks-ai-drawer__suggestion:hover {
  border-color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 6%, transparent);
}

/* ── Messages ──────────────────────────────────────────── */
.ks-ai-drawer__messages {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 24px;
}

/* ── Thinking ──────────────────────────────────────────── */
.ks-ai-drawer__thinking {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font: 400 0.8125rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-ai-drawer__spinner {
  animation: ks-ai-spin 0.8s linear infinite;
}

@keyframes ks-ai-spin {
  to {
    transform: rotate(360deg);
  }
}

/* ── Error ─────────────────────────────────────────────── */
.ks-ai-drawer__error {
  padding: 8px 12px;
  border-left: 3px solid #ba1a1a;
  background: rgba(186, 26, 26, 0.06);
  font: 400 0.75rem / 1.4 var(--font-sans);
  color: #ba1a1a;
}

/* ── Input area ────────────────────────────────────────── */
.ks-ai-drawer__input-area {
  flex-shrink: 0;
  padding: 16px 24px 20px;
  border-top: 1px solid var(--color-border);
  background: var(--color-surface);
}

.ks-ai-drawer__input-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  transition:
    border-color var(--duration-fast) var(--ease-smooth),
    box-shadow var(--duration-fast) var(--ease-smooth);
}

.ks-ai-drawer__input-row:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px
    color-mix(in srgb, var(--color-primary) 12%, transparent);
}

.ks-ai-drawer__input {
  flex: 1;
  border: none;
  outline: none;
  background: none;
  font: 400 0.875rem / 1.4 var(--font-sans);
  color: var(--color-text);
}

.ks-ai-drawer__input::placeholder {
  color: var(--color-secondary);
}

.ks-ai-drawer__input:disabled {
  opacity: 0.5;
}

.ks-ai-drawer__send-btn {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: var(--color-bg);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: opacity var(--duration-fast) var(--ease-smooth);
}

.ks-ai-drawer__send-btn:hover:not(:disabled) {
  opacity: 0.85;
}

.ks-ai-drawer__send-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.ks-ai-drawer__input-hint {
  margin: 6px 0 0;
  font: 400 0.6875rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-secondary);
  opacity: 0.6;
}

/* ── Transitions ───────────────────────────────────────── */
.ks-drawer-enter-active,
.ks-drawer-leave-active {
  transition: transform 0.3s var(--ease-smooth);
}

.ks-drawer-enter-from,
.ks-drawer-leave-to {
  transform: translateX(100%);
}

.ks-fade-enter-active,
.ks-fade-leave-active {
  transition: opacity 0.25s var(--ease-smooth);
}

.ks-fade-enter-from,
.ks-fade-leave-to {
  opacity: 0;
}

/* ── Responsive ────────────────────────────────────────── */
@media (max-width: 640px) {
  .ks-ai-drawer {
    width: 100vw;
  }
}
</style>
