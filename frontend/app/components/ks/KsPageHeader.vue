<script setup lang="ts">
/**
 * KsPageHeader — Sticky running page header with backdrop blur.
 *
 * Displays at the top of every page in an editorial "running head" style:
 * uppercase eyebrow text with title on the left and metadata on the right.
 * Sticks to the top on scroll with a frosted glass backdrop.
 *
 * Uses `<header>` without `role="banner"` since it's a page-level section
 * header, not the main site banner. Renders the title as an `<h1>` for
 * proper heading hierarchy.
 *
 * Usage:
 *   <KsPageHeader title="Discovery Explorer">
 *     <template #meta>Issue No. 42 · March 2026</template>
 *     <template #actions>
 *       <KsButton variant="ghost" size="sm">Filter</KsButton>
 *     </template>
 *   </KsPageHeader>
 *
 * @slot meta — Right-aligned metadata text
 * @slot actions — Optional action buttons
 */

export interface KsPageHeaderProps {
  /** Page title (left side) */
  title: string;
  /** Optional section label before the title */
  section?: string;
  /** Heading level — defaults to h1, override when nested */
  headingLevel?: 1 | 2 | 3;
}

const props = withDefaults(defineProps<KsPageHeaderProps>(), {
  section: undefined,
  headingLevel: 1,
});

const headingTag = computed(
  () => `h${props.headingLevel}` as "h1" | "h2" | "h3",
);
</script>

<template>
  <header class="ks-page-header">
    <div class="ks-page-header__left">
      <span v-if="section" class="ks-page-header__section">{{ section }}</span>
      <component :is="headingTag" class="ks-page-header__title">{{
        title
      }}</component>
    </div>
    <div class="ks-page-header__right">
      <span v-if="$slots.meta" class="ks-page-header__meta">
        <slot name="meta" />
      </span>
      <div v-if="$slots.actions" class="ks-page-header__actions">
        <slot name="actions" />
      </div>
    </div>
  </header>
</template>

<style scoped>
/* Extends global .ks-page-header from editorial.css */

.ks-page-header__left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.ks-page-header__section {
  color: var(--color-accent);
  font-weight: 700;
}

.ks-page-header__section::after {
  content: "·";
  margin-left: 0.75rem;
  color: var(--color-border);
}

/* Reset heading styles to match the page-header's running head aesthetic */
.ks-page-header__title {
  font: inherit;
  margin: 0;
}

.ks-page-header__right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.ks-page-header__actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* ─── Responsive ───────────────────────────────────── */
@media (max-width: 640px) {
  /* Visually hide metadata on small screens but keep it accessible */
  .ks-page-header__meta {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }
}
</style>
