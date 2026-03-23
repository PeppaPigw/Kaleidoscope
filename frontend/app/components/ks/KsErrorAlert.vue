<script setup lang="ts">
/**
 * KsErrorAlert — Editorial error message display.
 *
 * Replaces generic error popups with a styled, accessible error notice
 * that fits the warm editorial design. Used when API calls fail or
 * when validation errors occur.
 *
 * Usage:
 *   <KsErrorAlert message="Failed to load paper data." />
 *   <KsErrorAlert :message="error.message" @retry="refetch()" />
 *
 * @slot default — Override the message content
 */
import { AlertCircle } from 'lucide-vue-next'

export interface KsErrorAlertProps {
  /** Error message to display */
  message: string
  /** Show a Retry button */
  retryable?: boolean
}

withDefaults(defineProps<KsErrorAlertProps>(), {
  retryable: false,
})

defineEmits<{
  retry: []
}>()
</script>

<template>
  <div class="ks-error-alert" role="alert">
    <AlertCircle :size="18" class="ks-error-alert__icon" aria-hidden="true" />
    <div class="ks-error-alert__body">
      <p class="ks-error-alert__message">
        <slot>{{ message }}</slot>
      </p>
      <button
        v-if="retryable"
        type="button"
        class="ks-error-alert__retry"
        @click="$emit('retry')"
      >
        Try again
      </button>
    </div>
  </div>
</template>

<style scoped>
.ks-error-alert {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 20px;
  border: 1px solid rgba(204, 68, 68, 0.2);
  border-left: 3px solid #CC4444;
  border-radius: var(--radius-card);
  background: rgba(204, 68, 68, 0.03);
}

.ks-error-alert__icon {
  flex-shrink: 0;
  color: #CC4444;
  margin-top: 2px;
}

.ks-error-alert__body {
  flex: 1;
  min-width: 0;
}

.ks-error-alert__message {
  font: 400 0.875rem / 1.5 var(--font-serif);
  color: var(--color-text);
}

.ks-error-alert__retry {
  display: inline-block;
  margin-top: 8px;
  padding: 0;
  border: none;
  background: none;
  font: 500 0.8125rem / 1 var(--font-sans);
  color: var(--color-primary);
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
  transition: color var(--duration-fast) var(--ease-smooth);
}

.ks-error-alert__retry:hover {
  color: var(--color-primary-hover);
}
</style>
