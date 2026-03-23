<script setup lang="ts">
/**
 * KsTag — Small label badge for metadata display.
 *
 * Used for paper types, venue tiers, claim strengths, status indicators, etc.
 * Supports default (outlined), primary (teal tint), accent (gold tint),
 * and additional semantic variants (success, warning).
 *
 * @slot default — Tag text
 * @slot icon — Optional icon before text
 */

export interface KsTagProps {
  variant?: 'default' | 'primary' | 'accent' | 'success' | 'warning' | 'neutral' | 'danger'
  /** Renders as a larger, clickable pill shape */
  interactive?: boolean
  /** Renders removable with an × button */
  removable?: boolean
}

const props = withDefaults(defineProps<KsTagProps>(), {
  variant: 'default',
  interactive: false,
  removable: false,
})

const emit = defineEmits<{
  remove: []
  click: []
}>()

const rootClasses = computed(() => [
  'ks-tag',
  `ks-tag--${props.variant}`,
  {
    'ks-tag--interactive': props.interactive,
    'ks-tag--removable': props.removable,
  },
])

function handleTagActivate() {
  if (props.interactive) {
    emit('click')
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (!props.interactive) return
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    emit('click')
  }
}
</script>

<template>
  <span
    :class="rootClasses"
    :role="interactive ? 'button' : undefined"
    :tabindex="interactive ? 0 : undefined"
    @click="handleTagActivate"
    @keydown="handleKeydown"
  >
    <span v-if="$slots.icon" class="ks-tag__icon" aria-hidden="true">
      <slot name="icon" />
    </span>
    <slot />
    <button
      v-if="removable"
      type="button"
      class="ks-tag__remove"
      :aria-label="`Remove tag`"
      @click.stop="emit('remove')"
    >
      ×
    </button>
  </span>
</template>

<style scoped>
/* ─── Semantic variants ────────────────────────────── */
.ks-tag--success {
  background: rgba(16, 150, 72, 0.08);
  color: #0F7B3F;
  border-color: transparent;
}

.ks-tag--warning {
  background: rgba(212, 155, 33, 0.08);
  color: #8A5A04;
  border-color: transparent;
}

.ks-tag--neutral {
  background: rgba(120, 120, 120, 0.08);
  color: var(--color-secondary);
  border-color: transparent;
}

.ks-tag--danger {
  background: rgba(181, 74, 74, 0.08);
  color: #B54A4A;
  border-color: transparent;
}

/* ─── Interactive pill ─────────────────────────────── */
.ks-tag--interactive {
  cursor: pointer;
  padding: 0 12px;
  height: 28px;
  border-radius: 14px;
  transition: background-color var(--duration-fast) var(--ease-smooth),
              color var(--duration-fast) var(--ease-smooth),
              border-color var(--duration-fast) var(--ease-smooth);
}

.ks-tag--interactive:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-primary-light);
}

/* ─── Removable ────────────────────────────────────── */
.ks-tag--removable {
  padding-right: 4px;
}

.ks-tag__icon {
  display: flex;
  align-items: center;
  margin-right: 4px;
}

.ks-tag__remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-left: 4px;
  padding: 0;
  border: none;
  background: transparent;
  color: currentColor;
  opacity: 0.52;
  cursor: pointer;
  font-size: 0.75rem;
  line-height: 1;
  border-radius: 50%;
  transition: opacity var(--duration-fast) var(--ease-smooth),
              background var(--duration-fast) var(--ease-smooth);
}

.ks-tag__remove:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.06);
}
</style>
