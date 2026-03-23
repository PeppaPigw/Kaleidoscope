<script setup lang="ts">
/**
 * KsProvenanceDrawer — Global slide-out drawer for AI field provenance.
 *
 * Shows the full provenance chain for any AI-generated field: which model
 * produced it, when, with what confidence, and the source data it was
 * derived from. Triggered by clicking provenance badges anywhere in the UI.
 *
 * Uses Vue <Transition> for the panel animation and a backdrop overlay.
 * Implements focus trap, Escape handler, and focus restoration per WCAG.
 */
import { X, BrainCircuit, Calendar, ShieldCheck, Database, ChevronRight } from 'lucide-vue-next'
import type { ProvenanceInfo } from '~~/types/paper'

export interface ProvenanceChainStep {
  source: string
  action: string
  timestamp: string
  confidence?: number
  detail?: string
}

export interface KsProvenanceDrawerProps {
  /** Whether the drawer is open */
  open: boolean
  /** Field label (e.g. "Summary", "Claim Extraction") */
  fieldLabel?: string
  /** Field value preview */
  fieldValue?: string
  /** Provenance info */
  provenance?: ProvenanceInfo | null
  /** Full chain of provenance steps */
  chain?: ProvenanceChainStep[]
}

withDefaults(defineProps<KsProvenanceDrawerProps>(), {
  fieldLabel: 'Field',
  fieldValue: undefined,
  provenance: null,
  chain: () => [],
})

const emit = defineEmits<{
  close: []
}>()

// ─── Focus management ────────────────────────────────
const drawerRef = ref<HTMLElement | null>(null)
const previousFocus = ref<HTMLElement | null>(null)

function handleEscape(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    emit('close')
  }
}

function trapFocus(e: KeyboardEvent) {
  if (e.key !== 'Tab' || !drawerRef.value) return

  const focusable = drawerRef.value.querySelectorAll<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )
  if (focusable.length === 0) return

  const first = focusable[0]!
  const last = focusable[focusable.length - 1]!

  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault()
    last.focus()
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault()
    first.focus()
  }
}

function onDrawerEnter() {
  // Store the element that had focus before the drawer opened
  previousFocus.value = document.activeElement as HTMLElement | null
  // Move focus to the close button after the transition
  nextTick(() => {
    const closeBtn = drawerRef.value?.querySelector<HTMLElement>('.ks-provenance-drawer__close')
    closeBtn?.focus()
  })
}

function onDrawerLeave() {
  // Restore focus to the element that triggered the drawer
  previousFocus.value?.focus()
  previousFocus.value = null
}

function formatDate(ts: string): string {
  try {
    return new Date(ts).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return ts
  }
}
</script>

<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <Transition name="ks-fade">
      <div
        v-if="open"
        class="ks-provenance-backdrop"
        aria-hidden="true"
        @click="emit('close')"
      />
    </Transition>

    <!-- Drawer panel -->
    <Transition
      name="ks-drawer"
      @after-enter="onDrawerEnter"
      @after-leave="onDrawerLeave"
    >
      <aside
        v-if="open"
        ref="drawerRef"
        class="ks-provenance-drawer"
        role="dialog"
        aria-modal="true"
        :aria-label="`Provenance details for ${fieldLabel}`"
        @keydown="trapFocus"
        @keydown.escape="handleEscape"
      >
        <!-- Header -->
        <header class="ks-provenance-drawer__header">
          <div>
            <span class="ks-type-eyebrow">Provenance</span>
            <h2 class="ks-provenance-drawer__title">{{ fieldLabel }}</h2>
          </div>
          <button
            type="button"
            class="ks-provenance-drawer__close"
            aria-label="Close provenance drawer"
            @click="emit('close')"
          >
            <X :size="18" />
          </button>
        </header>

        <!-- Field preview -->
        <div v-if="fieldValue" class="ks-provenance-drawer__preview">
          <p class="ks-type-body-sm">{{ fieldValue }}</p>
        </div>

        <!-- Quick stats -->
        <div v-if="provenance" class="ks-provenance-drawer__stats">
          <div class="ks-provenance-drawer__stat">
            <BrainCircuit :size="14" aria-hidden="true" />
            <span class="ks-type-label">{{ provenance.source }}</span>
          </div>
          <div class="ks-provenance-drawer__stat">
            <ShieldCheck :size="14" aria-hidden="true" />
            <span class="ks-type-label">{{ Math.round(provenance.confidence * 100) }}% confidence</span>
          </div>
          <div class="ks-provenance-drawer__stat">
            <Calendar :size="14" aria-hidden="true" />
            <span class="ks-type-label">{{ formatDate(provenance.timestamp) }}</span>
          </div>
        </div>

        <!-- Provenance chain timeline -->
        <div v-if="chain.length > 0" class="ks-provenance-drawer__chain">
          <h3 class="ks-type-eyebrow" style="margin-bottom: 12px;">Provenance Chain</h3>
          <ol class="ks-provenance-drawer__timeline">
            <li
              v-for="(step, i) in chain"
              :key="i"
              class="ks-provenance-drawer__step"
            >
              <div class="ks-provenance-drawer__step-dot" />
              <div class="ks-provenance-drawer__step-body">
                <div class="ks-provenance-drawer__step-head">
                  <Database :size="12" aria-hidden="true" />
                  <span class="ks-type-label">{{ step.source }}</span>
                  <ChevronRight :size="12" aria-hidden="true" />
                  <span class="ks-type-label">{{ step.action }}</span>
                </div>
                <span class="ks-type-data">{{ formatDate(step.timestamp) }}</span>
                <p v-if="step.detail" class="ks-provenance-drawer__step-detail ks-type-body-sm">
                  {{ step.detail }}
                </p>
              </div>
            </li>
          </ol>
        </div>

        <!-- Empty chain -->
        <div v-else-if="!provenance" class="ks-provenance-drawer__empty">
          <p class="ks-type-label">No provenance information available.</p>
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* ─── Backdrop ─────────────────────────────────────── */
.ks-provenance-backdrop {
  position: fixed;
  inset: 0;
  z-index: 998;
  background: rgba(26, 26, 26, 0.28);
  backdrop-filter: blur(2px);
}

/* ─── Drawer panel ─────────────────────────────────── */
.ks-provenance-drawer {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
  width: min(420px, 90vw);
  background: var(--color-surface);
  border-left: 1px solid var(--color-border);
  box-shadow: var(--shadow-float);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* ─── Drawer slide animation ───────────────────────── */
.ks-drawer-enter-active {
  transition: transform 320ms var(--ease-page), opacity 200ms var(--ease-smooth);
}

.ks-drawer-leave-active {
  transition: transform 240ms cubic-bezier(0.32, 0, 0.67, 0), opacity 160ms var(--ease-smooth);
}

.ks-drawer-enter-from,
.ks-drawer-leave-to {
  transform: translateX(100%);
  opacity: 0.6;
}

/* ─── Header ───────────────────────────────────────── */
.ks-provenance-drawer__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 24px 24px 16px;
  border-bottom: 1px solid var(--color-border);
}

.ks-provenance-drawer__title {
  font: 600 1.125rem / 1.35 var(--font-display);
  color: var(--color-text);
  margin-top: 4px;
}

.ks-provenance-drawer__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: transparent;
  color: var(--color-secondary);
  cursor: pointer;
  transition: color var(--duration-fast) var(--ease-smooth),
              border-color var(--duration-fast) var(--ease-smooth);
}

.ks-provenance-drawer__close:hover {
  color: var(--color-text);
  border-color: var(--color-secondary);
}

/* ─── Preview ──────────────────────────────────────── */
.ks-provenance-drawer__preview {
  padding: 16px 24px;
  background: rgba(232, 229, 224, 0.2);
  border-bottom: 1px solid var(--color-border);
}

/* ─── Stats ────────────────────────────────────────── */
.ks-provenance-drawer__stats {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
}

.ks-provenance-drawer__stat {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-secondary);
}

/* ─── Chain timeline ───────────────────────────────── */
.ks-provenance-drawer__chain {
  padding: 20px 24px;
  flex: 1;
}

.ks-provenance-drawer__timeline {
  list-style: none;
  padding-left: 16px;
  border-left: 2px solid var(--color-border);
}

.ks-provenance-drawer__step {
  position: relative;
  padding: 0 0 20px 20px;
}

.ks-provenance-drawer__step:last-child {
  padding-bottom: 0;
}

.ks-provenance-drawer__step-dot {
  position: absolute;
  left: -7px;
  top: 4px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--color-primary);
  border: 2px solid var(--color-surface);
}

.ks-provenance-drawer__step-head {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}

.ks-provenance-drawer__step-detail {
  margin-top: 4px;
  color: var(--color-secondary);
}

/* ─── Empty ────────────────────────────────────────── */
.ks-provenance-drawer__empty {
  padding: 48px 24px;
  text-align: center;
}
</style>
