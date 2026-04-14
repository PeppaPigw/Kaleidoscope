<script setup lang="ts">
/**
 * AgentChatMessage -- Chat message bubble for DeepXiv agent conversations.
 *
 * User messages render right-aligned; assistant messages render left-aligned
 * with an optional papers-loaded badge.
 */
import { FileText } from 'lucide-vue-next'

export interface AgentChatMessageProps {
  role: 'user' | 'assistant'
  content: string
  papersLoaded?: number
}

defineProps<AgentChatMessageProps>()
</script>

<template>
  <div
    :class="[
      'ks-chat-message',
      `ks-chat-message--${role}`,
    ]"
  >
    <div class="ks-chat-message__bubble">
      <p class="ks-chat-message__text">{{ content }}</p>
      <span
        v-if="role === 'assistant' && papersLoaded && papersLoaded > 0"
        class="ks-chat-message__papers"
      >
        <FileText :size="12" />
        {{ papersLoaded }} paper{{ papersLoaded === 1 ? '' : 's' }} loaded
      </span>
    </div>
  </div>
</template>

<style scoped>
.ks-chat-message {
  display: flex;
  margin-bottom: 12px;
}

.ks-chat-message--user {
  justify-content: flex-end;
}

.ks-chat-message--assistant {
  justify-content: flex-start;
}

.ks-chat-message__bubble {
  max-width: 75%;
  padding: 10px 14px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ks-chat-message--user .ks-chat-message__bubble {
  background: var(--color-primary);
  color: #fff;
  border-bottom-right-radius: 2px;
}

.ks-chat-message--assistant .ks-chat-message__bubble {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-text);
  border-bottom-left-radius: 2px;
}

.ks-chat-message__text {
  font: 400 0.875rem / 1.6 var(--font-sans);
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.ks-chat-message__papers {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font: 500 0.6875rem / 1 var(--font-sans);
  color: var(--color-secondary);
  padding-top: 4px;
  border-top: 1px solid var(--color-border);
}
</style>
