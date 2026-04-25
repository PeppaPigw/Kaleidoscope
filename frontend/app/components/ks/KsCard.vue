<script setup lang="ts">
/**
 * KsCard — Editorial card surface with optional accent border variants.
 *
 * Provides a consistent card surface with border, shadow lift on hover,
 * and optional top-accent (teal or gold) for visual hierarchy.
 *
 * @slot default — Card body content
 * @slot header — Optional header area (above body)
 * @slot footer — Optional footer area (below body)
 */

export interface KsCardProps {
  /** Visual variant: default | teal-top | gold-top | flat */
  variant?: "default" | "teal-top" | "gold-top" | "flat";
  /** Padding preset — none removes all padding */
  padding?: "none" | "sm" | "md" | "lg";
  /** Disable hover lift animation */
  static?: boolean;
  /** HTML tag for the root element */
  as?: string;
}

const props = withDefaults(defineProps<KsCardProps>(), {
  variant: "default",
  padding: "md",
  static: false,
  as: "div",
});

const paddingMap: Record<string, string> = {
  none: "",
  sm: "ks-card-pad--sm",
  md: "ks-card-pad--md",
  lg: "ks-card-pad--lg",
};

const variantMap: Record<string, string> = {
  default: "",
  "teal-top": "ks-card--teal-top",
  "gold-top": "ks-card--gold-top",
  flat: "ks-card--flat",
};

const rootClasses = computed(() => [
  "ks-card",
  variantMap[props.variant],
  paddingMap[props.padding],
  { "ks-card--static": props.static },
]);
</script>

<template>
  <component :is="as" :class="rootClasses">
    <div v-if="$slots.header" class="ks-card__header">
      <slot name="header" />
    </div>
    <div class="ks-card__body">
      <slot />
    </div>
    <div v-if="$slots.footer" class="ks-card__footer">
      <slot name="footer" />
    </div>
  </component>
</template>

<style scoped>
.ks-card--flat {
  background: var(--color-surface);
  border: none;
  border-radius: var(--radius-card);
}

.ks-card--static:hover {
  box-shadow: var(--shadow-card) !important;
  transform: none !important;
}

/* ─── Padding presets ──────────────────────────────── */
.ks-card-pad--sm {
  padding: 12px 14px;
}
.ks-card-pad--md {
  padding: 20px 24px;
}
.ks-card-pad--lg {
  padding: 28px 32px;
}

/* ─── Sections ─────────────────────────────────────── */
.ks-card__header {
  padding-bottom: 14px;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 14px;
}

.ks-card__footer {
  padding-top: 14px;
  border-top: 1px solid var(--color-border);
  margin-top: 14px;
}
</style>
