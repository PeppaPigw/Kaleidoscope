<script setup lang="ts">
/**
 * KsButton — Editorial button with three visual variants and three sizes.
 *
 * Built on top of the native <button> element (or <a> / <NuxtLink> via the `as` prop).
 * Provides focus-visible ring, disabled state, loading spinner, and icon slots.
 * When `as` is a link element, disabled/loading states use `aria-disabled`
 * and `tabindex=-1` instead of the invalid `disabled` attribute.
 *
 * @slot default — Button label
 * @slot icon-left — Optional icon before label
 * @slot icon-right — Optional icon after label
 */
import { Loader2 } from "lucide-vue-next";

export interface KsButtonProps {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  loading?: boolean;
  /** Render as a different element (e.g. 'a', NuxtLink) */
  as?: string | object;
  type?: "button" | "submit" | "reset";
}

const props = withDefaults(defineProps<KsButtonProps>(), {
  variant: "primary",
  size: "md",
  disabled: false,
  loading: false,
  as: "button",
  type: "button",
});

defineEmits<{
  click: [event: MouseEvent];
}>();

const isButton = computed(() => props.as === "button");
const isEffectivelyDisabled = computed(() => props.disabled || props.loading);

const rootClasses = computed(() => [
  "ks-btn",
  `ks-btn--${props.variant}`,
  `ks-btn--${props.size}`,
  {
    "ks-btn--loading": props.loading,
    "ks-btn--disabled": props.disabled,
  },
]);

function handleClick(e: MouseEvent) {
  // For link elements, prevent activation when disabled/loading
  if (isEffectivelyDisabled.value) {
    e.preventDefault();
    e.stopPropagation();
  }
}

function handleKeydown(e: KeyboardEvent) {
  // For link elements, prevent Enter/Space when disabled/loading
  if (isEffectivelyDisabled.value && (e.key === "Enter" || e.key === " ")) {
    e.preventDefault();
    e.stopPropagation();
  }
}
</script>

<template>
  <component
    :is="as"
    :class="rootClasses"
    :disabled="isButton ? isEffectivelyDisabled : undefined"
    :type="isButton ? type : undefined"
    :aria-disabled="!isButton && isEffectivelyDisabled ? 'true' : undefined"
    :tabindex="!isButton && isEffectivelyDisabled ? -1 : undefined"
    :aria-busy="loading || undefined"
    @click="
      handleClick($event);
      $emit('click', $event);
    "
    @keydown="handleKeydown"
  >
    <!-- Loading spinner -->
    <Loader2
      v-if="loading"
      :size="size === 'sm' ? 14 : 16"
      class="ks-btn__spinner"
      aria-hidden="true"
    />

    <!-- Icon left slot -->
    <span v-if="$slots['icon-left'] && !loading" class="ks-btn__icon">
      <slot name="icon-left" />
    </span>

    <!-- Label -->
    <span class="ks-btn__label">
      <slot />
    </span>

    <!-- Icon right slot -->
    <span v-if="$slots['icon-right']" class="ks-btn__icon">
      <slot name="icon-right" />
    </span>
  </component>
</template>

<style scoped>
/* ─── Sizes ────────────────────────────────────────── */
.ks-btn--sm {
  height: 32px;
  padding: 0 12px;
  font-size: 0.8125rem;
}

.ks-btn--lg {
  height: 48px;
  padding: 0 24px;
  font-size: 1rem;
}

/* ─── States ───────────────────────────────────────── */
.ks-btn--disabled {
  opacity: 0.48;
  cursor: not-allowed;
  pointer-events: none;
}

/* For link-based buttons, pointer-events must remain so we can intercept clicks */
a.ks-btn--disabled,
[aria-disabled="true"].ks-btn--disabled {
  pointer-events: auto;
  cursor: not-allowed;
}

.ks-btn--loading {
  cursor: wait;
}

/* ─── Icon ─────────────────────────────────────────── */
.ks-btn__icon {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.ks-btn__label {
  display: inline-flex;
  align-items: center;
}

/* ─── Spinner ──────────────────────────────────────── */
.ks-btn__spinner {
  animation: ks-spin 700ms linear infinite;
  flex-shrink: 0;
}

@keyframes ks-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
