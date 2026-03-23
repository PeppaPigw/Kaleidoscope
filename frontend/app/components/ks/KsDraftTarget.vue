<script setup lang="ts">
/**
 * KsDraftTarget — Cross-page draft target indicator.
 *
 * A drop zone visual that appears in Writing Studio and Synthesis pages.
 * Indicates where evidence cards, quotes, or citations can be dropped
 * to build manuscript drafts. Provides visual feedback during drag operations.
 *
 * Separates `dragover` (hover feedback) from `drop` (commit action).
 * Also provides keyboard/touch accessible paste via the `paste` event
 * and a button fallback.
 *
 * @slot default — Optional custom content inside the drop zone
 */

export interface KsDraftTargetProps {
  /** Label shown in the target zone */
  label?: string
  /** Whether a drag operation is actively hovering */
  active?: boolean
  /** Section label (e.g. "Introduction", "Methods") */
  section?: string
}

const props = withDefaults(defineProps<KsDraftTargetProps>(), {
  label: 'Drop evidence here',
  active: false,
  section: undefined,
})

const emit = defineEmits<{
  drop: [event: DragEvent]
  /** Keyboard / touch accessible paste action */
  paste: []
}>()

const isHovering = ref(false)
const isActive = computed(() => props.active || isHovering.value)

function onDragEnter(e: DragEvent) {
  e.preventDefault()
  isHovering.value = true
}

function onDragLeave() {
  isHovering.value = false
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  isHovering.value = false
  emit('drop', e)
}
</script>

<template>
  <div
    :class="[
      'ks-draft-target',
      { 'ks-draft-target--active': isActive },
    ]"
    role="region"
    :aria-label="`Drop zone: ${label}`"
    @dragover.prevent
    @dragenter="onDragEnter"
    @dragleave="onDragLeave"
    @drop="onDrop"
  >
    <span v-if="section" class="ks-draft-target__section ks-type-eyebrow">{{ section }}</span>
    <div class="ks-draft-target__content">
      <slot>
        <span class="ks-draft-target__label">{{ label }}</span>
        <!-- Keyboard / touch accessible fallback -->
        <button
          type="button"
          class="ks-draft-target__paste-btn"
          @click="emit('paste')"
        >
          or paste from clipboard
        </button>
      </slot>
    </div>
    <svg class="ks-draft-target__border" aria-hidden="true">
      <rect
        x="1" y="1"
        width="calc(100% - 2px)" height="calc(100% - 2px)"
        rx="2"
        fill="none"
        stroke="var(--color-border)"
        stroke-width="1.5"
        stroke-dasharray="8 4"
      />
    </svg>
  </div>
</template>

<style scoped>
.ks-draft-target {
  position: relative;
  padding: 24px 20px;
  text-align: center;
  border-radius: var(--radius-card);
  transition: background var(--duration-fast) var(--ease-smooth),
              transform var(--duration-fast) var(--ease-spring);
}

.ks-draft-target--active {
  background: var(--color-primary-light);
  transform: scale(1.01);
}

.ks-draft-target--active .ks-draft-target__border rect {
  stroke: var(--color-primary);
  stroke-dasharray: none;
}

.ks-draft-target__border {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.ks-draft-target__section {
  display: block;
  margin-bottom: 6px;
  color: var(--color-accent);
}

.ks-draft-target__content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.ks-draft-target__label {
  font: 500 0.8125rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
}

.ks-draft-target--active .ks-draft-target__label {
  color: var(--color-primary);
}

.ks-draft-target__paste-btn {
  padding: 0;
  border: none;
  background: none;
  font: 400 0.75rem / 1.3 var(--font-sans);
  color: var(--color-primary);
  text-decoration: underline;
  text-underline-offset: 3px;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity var(--duration-fast) var(--ease-smooth);
}

.ks-draft-target__paste-btn:hover {
  opacity: 1;
}
</style>
