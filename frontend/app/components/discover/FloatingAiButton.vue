<script setup lang="ts">
/**
 * DiscoverFloatingAiButton — Fixed floating button to trigger AI assistant drawer.
 *
 * Positioned at bottom-right corner, similar to customer support chat buttons.
 * Includes hover tooltip and pulse animation to draw attention.
 */
import { Bot } from 'lucide-vue-next'

defineEmits<{
  click: []
}>()
</script>

<template>
  <button
    type="button"
    class="ks-floating-ai"
    aria-label="Open AI Research Assistant"
    @click="$emit('click')"
  >
    <Bot :size="20" class="ks-floating-ai__icon" />
    <span class="ks-floating-ai__tooltip">AI Assistant</span>
  </button>
</template>

<style scoped>
.ks-floating-ai {
  position: fixed;
  bottom: 32px;
  right: 32px;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: var(--color-bg);
  border: none;
  border-radius: 50%;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15),
              0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  z-index: 100;
  transition: transform var(--duration-fast) var(--ease-smooth),
              box-shadow var(--duration-fast) var(--ease-smooth);
}

.ks-floating-ai:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2),
              0 3px 10px rgba(0, 0, 0, 0.15);
}

.ks-floating-ai:hover .ks-floating-ai__tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateX(-8px);
}

.ks-floating-ai:active {
  transform: scale(0.95);
}

.ks-floating-ai__icon {
  flex-shrink: 0;
}

/* ── Tooltip ───────────────────────────────────────────── */
.ks-floating-ai__tooltip {
  position: absolute;
  right: 100%;
  top: 50%;
  transform: translateY(-50%);
  margin-right: 12px;
  padding: 8px 14px;
  background: var(--color-text);
  color: var(--color-bg);
  font: 500 0.8125rem / 1 var(--font-sans);
  white-space: nowrap;
  border-radius: 6px;
  opacity: 0;
  visibility: hidden;
  transition: opacity var(--duration-fast) var(--ease-smooth),
              visibility var(--duration-fast) var(--ease-smooth),
              transform var(--duration-fast) var(--ease-smooth);
  pointer-events: none;
}

.ks-floating-ai__tooltip::after {
  content: '';
  position: absolute;
  left: 100%;
  top: 50%;
  transform: translateY(-50%);
  border: 6px solid transparent;
  border-left-color: var(--color-text);
}

/* ── Pulse animation (optional attention grabber) ────── */
@keyframes ks-floating-pulse {
  0%, 100% {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15),
                0 2px 8px rgba(0, 0, 0, 0.1),
                0 0 0 0 color-mix(in srgb, var(--color-primary) 40%, transparent);
  }
  50% {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15),
                0 2px 8px rgba(0, 0, 0, 0.1),
                0 0 0 8px color-mix(in srgb, var(--color-primary) 0%, transparent);
  }
}

/* Uncomment to enable pulse animation on first load */
/* .ks-floating-ai {
  animation: ks-floating-pulse 2s ease-out 3;
} */

/* ── Responsive ────────────────────────────────────────── */
@media (max-width: 768px) {
  .ks-floating-ai {
    bottom: 24px;
    right: 24px;
    width: 52px;
    height: 52px;
  }

  .ks-floating-ai__tooltip {
    display: none;
  }
}
</style>
