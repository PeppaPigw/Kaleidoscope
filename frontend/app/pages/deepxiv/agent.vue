<script setup lang="ts">
/**
 * DeepXiv Research Agent — chat interface for querying and analyzing
 * arXiv papers through an AI research agent.
 */
import { Loader2, Send, Bot } from 'lucide-vue-next'

definePageMeta({ layout: 'default', title: 'Research Agent' })
useHead({ title: 'Research Agent -- DeepXiv' })

const { t } = useTranslation()
const { agentQuery } = useDeepXiv()

// ── Types ───────────────────────────────────────────────
interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  papersLoaded?: number
}

// ── State ───────────────────────────────────────────────
const messages = ref<ChatMessage[]>([])
const input = ref('')
const isLoading = ref(false)
const error = ref<string | null>(null)
const messagesEnd = ref<HTMLElement | null>(null)

// ── Computed ────────────────────────────────────────────
const canSend = computed(() => input.value.trim().length > 0 && !isLoading.value)

// ── Actions ─────────────────────────────────────────────
async function scrollToBottom() {
  await nextTick()
  messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
}

async function sendMessage() {
  const text = input.value.trim()
  if (!text || isLoading.value) return

  error.value = null
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  isLoading.value = true
  await scrollToBottom()

  try {
    const res = await agentQuery(text)
    messages.value.push({
      role: 'assistant',
      content: res.answer,
      papersLoaded: res.papers_loaded,
    })
  }
  catch (err) {
    error.value = err instanceof Error ? err.message : 'Agent query failed'
    messages.value.push({
      role: 'assistant',
      content: 'Sorry, an error occurred while processing your query. Please try again.',
    })
  }
  finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    void sendMessage()
  }
}
</script>

<template>
  <div class="ks-dxagent">
    <!-- Header -->
    <header class="ks-dxagent__header">
      <div class="ks-dxagent__header-left">
        <Bot :size="24" class="ks-dxagent__header-icon" />
        <div>
          <h1 class="ks-dxagent__title">DeepXiv Research Agent</h1>
          <p class="ks-dxagent__subtitle">
            Ask questions about arXiv papers. The agent can search, retrieve, and analyze papers.
          </p>
        </div>
      </div>
    </header>

    <!-- Chat area -->
    <div class="ks-dxagent__chat">
      <!-- Empty state -->
      <div v-if="messages.length === 0 && !isLoading" class="ks-dxagent__empty">
        <Bot :size="40" class="ks-dxagent__empty-icon" />
        <h3 class="ks-dxagent__empty-title">Start a research conversation</h3>
        <p class="ks-dxagent__empty-text">
          Ask about specific papers, compare methodologies, summarize findings,
          or explore research topics.
        </p>
        <div class="ks-dxagent__suggestions">
          <button class="ks-dxagent__suggestion" @click="input = 'What are the latest advances in large language models?'; sendMessage()">
            Latest advances in LLMs
          </button>
          <button class="ks-dxagent__suggestion" @click="input = 'Find papers on retrieval-augmented generation'; sendMessage()">
            Papers on RAG
          </button>
          <button class="ks-dxagent__suggestion" @click="input = 'Summarize recent work on multimodal AI'; sendMessage()">
            Multimodal AI research
          </button>
        </div>
      </div>

      <!-- Messages -->
      <div v-else class="ks-dxagent__messages">
        <template v-for="(msg, i) in messages" :key="i">
          <DeepxivAgentChatMessage
            :role="msg.role"
            :content="msg.content"
            :papers-loaded="msg.papersLoaded"
          />
        </template>

        <!-- Thinking indicator -->
        <div v-if="isLoading" class="ks-dxagent__thinking">
          <Loader2 :size="16" class="ks-dxagent__spinner" />
          <span>Thinking...</span>
        </div>

        <!-- Error -->
        <div v-if="error" class="ks-dxagent__error">
          {{ error }}
        </div>

        <div ref="messagesEnd" />
      </div>
    </div>

    <!-- Input area -->
    <div class="ks-dxagent__input-area">
      <div class="ks-dxagent__input-row">
        <input
          v-model="input"
          type="text"
          class="ks-dxagent__input"
          placeholder="Ask about papers, methods, findings..."
          :disabled="isLoading"
          @keydown="handleKeydown"
        />
        <button
          class="ks-dxagent__send-btn"
          :disabled="!canSend"
          @click="sendMessage"
        >
          <Loader2 v-if="isLoading" :size="16" class="ks-dxagent__spinner" />
          <Send v-else :size="16" />
        </button>
      </div>
      <p class="ks-dxagent__input-hint">
        Press Enter to send
      </p>
    </div>
  </div>
</template>

<style scoped>
.ks-dxagent {
  display: flex;
  flex-direction: column;
  max-width: 860px;
  margin: 0 auto;
  padding: 24px;
  height: 100vh;
  min-height: 0;
}

/* ── Header ──────────────────────────────────────────── */
.ks-dxagent__header {
  flex-shrink: 0;
  margin-bottom: 20px;
}

.ks-dxagent__header-left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.ks-dxagent__header-icon {
  flex-shrink: 0;
  color: var(--color-primary);
  margin-top: 2px;
}

.ks-dxagent__title {
  font: 700 1.5rem / 1.1 var(--font-display, serif);
  color: var(--color-primary);
  margin: 0;
}

.ks-dxagent__subtitle {
  font: 400 0.8125rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  margin: 4px 0 0;
  max-width: 520px;
}

/* ── Chat area ───────────────────────────────────────── */
.ks-dxagent__chat {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: color-mix(in srgb, var(--color-secondary) 30%, transparent) transparent;
}

.ks-dxagent__chat::-webkit-scrollbar {
  width: 4px;
}

.ks-dxagent__chat::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--color-secondary) 30%, transparent);
  border-radius: 9999px;
}

/* ── Empty state ─────────────────────────────────────── */
.ks-dxagent__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
  padding: 40px 20px;
  text-align: center;
}

.ks-dxagent__empty-icon {
  color: var(--color-border);
  margin-bottom: 16px;
}

.ks-dxagent__empty-title {
  font: 600 1.125rem / 1.3 var(--font-sans);
  color: var(--color-text);
  margin: 0 0 8px;
}

.ks-dxagent__empty-text {
  font: 400 0.875rem / 1.6 var(--font-sans);
  color: var(--color-secondary);
  max-width: 420px;
  margin: 0 0 24px;
}

.ks-dxagent__suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.ks-dxagent__suggestion {
  padding: 8px 16px;
  border: 1px solid var(--color-border);
  background: none;
  border-radius: 20px;
  font: 400 0.8125rem / 1 var(--font-sans);
  color: var(--color-text);
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-smooth),
              color var(--duration-fast) var(--ease-smooth),
              background var(--duration-fast) var(--ease-smooth);
}

.ks-dxagent__suggestion:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 6%, transparent);
}

/* ── Messages ────────────────────────────────────────── */
.ks-dxagent__messages {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 8px 0 16px;
}

/* ── Thinking ────────────────────────────────────────── */
.ks-dxagent__thinking {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font: 400 0.875rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-dxagent__spinner {
  animation: ks-dxa-spin 0.8s linear infinite;
}

@keyframes ks-dxa-spin {
  to { transform: rotate(360deg); }
}

/* ── Error ────────────────────────────────────────────── */
.ks-dxagent__error {
  padding: 10px 14px;
  border-left: 3px solid #ba1a1a;
  background: rgba(186, 26, 26, 0.06);
  font: 400 0.8125rem / 1.4 var(--font-sans);
  color: #ba1a1a;
}

/* ── Input area ──────────────────────────────────────── */
.ks-dxagent__input-area {
  flex-shrink: 0;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

.ks-dxagent__input-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  transition: border-color var(--duration-fast) var(--ease-smooth),
              box-shadow var(--duration-fast) var(--ease-smooth);
}

.ks-dxagent__input-row:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary) 12%, transparent);
}

.ks-dxagent__input {
  flex: 1;
  border: none;
  outline: none;
  background: none;
  font: 400 0.9375rem / 1.4 var(--font-sans);
  color: var(--color-text);
}

.ks-dxagent__input::placeholder {
  color: var(--color-secondary);
}

.ks-dxagent__input:disabled {
  opacity: 0.5;
}

.ks-dxagent__send-btn {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
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

.ks-dxagent__send-btn:hover:not(:disabled) {
  opacity: 0.85;
}

.ks-dxagent__send-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.ks-dxagent__input-hint {
  margin: 6px 0 0;
  font: 400 0.6875rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-secondary);
  opacity: 0.6;
}

/* ── Responsive ──────────────────────────────────────── */
@media (max-width: 640px) {
  .ks-dxagent {
    padding: 16px;
  }

  .ks-dxagent__suggestions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
