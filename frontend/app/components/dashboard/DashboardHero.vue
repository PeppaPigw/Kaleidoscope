<script setup lang="ts">
/**
 * DashboardHero — Masthead hero section for the Dashboard page.
 *
 * Displays the daily research theme, lead summary, date, and key stats.
 * Uses a warm gradient overlay and magazine-style typography.
 *
 * @slot default — Optional extra content below the lead text
 */

export interface HeroStat {
  label: string;
  value: string;
}

export interface DashboardHeroProps {
  /** Section eyebrow (e.g. "Today's Research Theme") */
  eyebrow?: string;
  /** Date label */
  date: string;
  /** Headline */
  title: string;
  /** Lead paragraph */
  lead: string;
  /** Quick stat chips */
  stats?: HeroStat[];
}

const props = withDefaults(defineProps<DashboardHeroProps>(), {
  eyebrow: "",
  stats: () => [],
});

defineEmits<{ click: [] }>();

const uid = useId();
const { t } = useTranslation();

const resolvedEyebrow = computed(
  () => props.eyebrow || t("todaysResearchTheme"),
);
</script>

<template>
  <section
    class="ks-dashboard-hero ks-motion-paper-reveal"
    :aria-labelledby="`${uid}-title`"
    role="button"
    tabindex="0"
    @click="$emit('click')"
    @keydown.enter="$emit('click')"
    @keydown.space.prevent="$emit('click')"
  >
    <div class="ks-dashboard-hero__gradient" aria-hidden="true" />
    <div class="ks-dashboard-hero__content">
      <span class="ks-type-eyebrow ks-dashboard-hero__eyebrow">
        {{ resolvedEyebrow }}
      </span>
      <KsTranslatableTitle
        :text="title"
        tag="h2"
        title-class="ks-type-cover ks-dashboard-hero__title"
      />
      <p class="ks-type-lead ks-dashboard-hero__lead">
        {{ lead }}
      </p>
      <span class="ks-type-data">{{ date }}</span>
      <slot />
    </div>
    <div
      v-if="stats.length > 0"
      class="ks-dashboard-hero__stats"
      role="list"
      aria-label="Daily statistics"
    >
      <div
        v-for="stat in stats"
        :key="stat.label"
        class="ks-dashboard-hero__stat"
        role="listitem"
      >
        <span class="ks-type-eyebrow">{{ stat.label }}</span>
        <span class="ks-type-stat">{{ stat.value }}</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.ks-dashboard-hero {
  position: relative;
  padding: 48px 56px 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-top: 2px solid var(--color-accent);
  border-radius: var(--radius-card);
  overflow: hidden;
}

.ks-dashboard-hero__gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgba(13, 115, 119, 0.08) 0%,
    rgba(196, 163, 90, 0.05) 100%
  );
  pointer-events: none;
}

.ks-dashboard-hero__content {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 32px;
}

.ks-dashboard-hero__eyebrow {
  color: var(--color-primary);
}

.ks-dashboard-hero__title {
  max-width: 18ch;
  transition: transform var(--duration-normal) var(--ease-spring);
}

.ks-dashboard-hero:hover .ks-dashboard-hero__title {
  transform: translateY(-4px);
}

.ks-dashboard-hero__lead {
  max-width: 44ch;
}

.ks-dashboard-hero__stats {
  position: relative;
  display: flex;
  gap: 40px;
  padding: 20px 0;
  border-top: 1px solid var(--color-border);
}

.ks-dashboard-hero__stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

@media (max-width: 768px) {
  .ks-dashboard-hero {
    padding: 32px 24px 0;
  }

  .ks-dashboard-hero__stats {
    flex-wrap: wrap;
    gap: 20px;
  }
}
</style>
