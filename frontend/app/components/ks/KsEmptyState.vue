<script setup lang="ts">
/**
 * KsEmptyState — Inviting empty state placeholder.
 *
 * Shown when a data-dependent component has no results or content.
 * Provides a message, (optional) description, icon slot, and action slot.
 * Editorial minimalism — no illustration clutter.
 *
 * Usage:
 *   <KsEmptyState
 *     title="No papers found"
 *     description="Try adjusting your search filters."
 *   >
 *     <template #action>
 *       <KsButton variant="secondary">Clear Filters</KsButton>
 *     </template>
 *   </KsEmptyState>
 *
 * @slot icon — Optional icon above the title (defaults to a thin border circle)
 * @slot action — Optional call-to-action button(s)
 */

export interface KsEmptyStateProps {
  /** Headline */
  title: string
  /** Supporting description */
  description?: string
}

withDefaults(defineProps<KsEmptyStateProps>(), {
  description: undefined,
})
</script>

<template>
  <div class="ks-empty-state" role="status">
    <div class="ks-empty-state__icon">
      <slot name="icon">
        <!-- Default: decorative circle with center dot -->
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
          <circle cx="24" cy="24" r="22" stroke="var(--color-border)" stroke-width="1.5" />
          <circle cx="24" cy="24" r="3" fill="var(--color-accent)" opacity="0.6" />
        </svg>
      </slot>
    </div>
    <h3 class="ks-empty-state__title">{{ title }}</h3>
    <p v-if="description" class="ks-empty-state__desc">{{ description }}</p>
    <div v-if="$slots.action" class="ks-empty-state__action">
      <slot name="action" />
    </div>
  </div>
</template>

<style scoped>
.ks-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 32px;
  text-align: center;
}

.ks-empty-state__icon {
  margin-bottom: 16px;
  opacity: 0.8;
}

.ks-empty-state__title {
  font: 600 1.125rem / 1.35 var(--font-display);
  color: var(--color-text);
  margin-bottom: 6px;
}

.ks-empty-state__desc {
  font: 400 0.875rem / 1.5 var(--font-serif);
  color: var(--color-secondary);
  max-width: 36ch;
}

.ks-empty-state__action {
  margin-top: 20px;
}
</style>
