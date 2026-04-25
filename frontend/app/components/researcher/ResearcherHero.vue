<script setup lang="ts">
/**
 * ResearcherHero — Profile header for researcher pages.
 *
 * Displays the researcher's name, affiliation, h-index, publication count,
 * citation count, ORCID, profile photo placeholder, and social links.
 */

export interface ResearcherHeroProps {
  name: string;
  affiliation: string;
  title: string;
  hIndex: number;
  totalPapers: number;
  totalCitations: number;
  orcid?: string;
  homepage?: string;
  scholarUrl?: string;
  imageUrl?: string;
}

defineProps<ResearcherHeroProps>();
defineEmits<{ follow: [] }>();

const uid = useId();
</script>

<template>
  <header
    class="ks-researcher-hero ks-motion-paper-reveal"
    :aria-labelledby="`${uid}-title`"
  >
    <div class="ks-researcher-hero__avatar">
      <img
        v-if="imageUrl"
        :src="imageUrl"
        :alt="`Photo of ${name}`"
        class="ks-researcher-hero__avatar-img"
      />
      <div
        v-else
        class="ks-researcher-hero__avatar-placeholder"
        aria-hidden="true"
      >
        <svg
          width="48"
          height="48"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          opacity="0.3"
        >
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
      </div>
    </div>

    <div class="ks-researcher-hero__info">
      <h1 :id="`${uid}-title`" class="ks-researcher-hero__name">{{ name }}</h1>
      <p class="ks-researcher-hero__title">{{ title }}</p>
      <p class="ks-researcher-hero__affiliation">{{ affiliation }}</p>

      <div class="ks-researcher-hero__stats">
        <div class="ks-researcher-hero__stat">
          <span class="ks-researcher-hero__stat-value">{{ hIndex }}</span>
          <span class="ks-type-data">h-index</span>
        </div>
        <div class="ks-researcher-hero__stat">
          <span class="ks-researcher-hero__stat-value">{{ totalPapers }}</span>
          <span class="ks-type-data">papers</span>
        </div>
        <div class="ks-researcher-hero__stat">
          <span class="ks-researcher-hero__stat-value">{{
            totalCitations.toLocaleString()
          }}</span>
          <span class="ks-type-data">citations</span>
        </div>
      </div>

      <div class="ks-researcher-hero__links">
        <a
          v-if="orcid"
          :href="`https://orcid.org/${orcid}`"
          target="_blank"
          rel="noopener"
          class="ks-researcher-hero__link"
        >
          ORCID: {{ orcid }}
        </a>
        <a
          v-if="homepage"
          :href="homepage"
          target="_blank"
          rel="noopener"
          class="ks-researcher-hero__link"
        >
          Homepage ↗
        </a>
        <a
          v-if="scholarUrl"
          :href="scholarUrl"
          target="_blank"
          rel="noopener"
          class="ks-researcher-hero__link"
        >
          Google Scholar ↗
        </a>
      </div>

      <KsButton variant="secondary" @click="$emit('follow')"
        >Follow Researcher</KsButton
      >
    </div>
  </header>
</template>

<style scoped>
.ks-researcher-hero {
  display: flex;
  gap: 32px;
  padding: 40px 0;
  border-bottom: 1px solid var(--color-border);
}

.ks-researcher-hero__avatar {
  flex-shrink: 0;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--color-bg);
  border: 2px solid var(--color-border);
}

.ks-researcher-hero__avatar-placeholder {
  color: var(--color-secondary);
}

.ks-researcher-hero__info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ks-researcher-hero__name {
  font: 700 2rem / 1.2 var(--font-display);
  color: var(--color-text);
}

.ks-researcher-hero__title {
  font: 500 1rem / 1.4 var(--font-serif);
  color: var(--color-accent);
}

.ks-researcher-hero__affiliation {
  font: 400 0.9375rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
}

.ks-researcher-hero__stats {
  display: flex;
  gap: 24px;
  margin-top: 8px;
}

.ks-researcher-hero__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.ks-researcher-hero__stat-value {
  font: 700 1.5rem / 1 var(--font-mono);
  color: var(--color-primary);
}

.ks-researcher-hero__links {
  display: flex;
  gap: 12px;
  margin-top: 4px;
  flex-wrap: wrap;
}

.ks-researcher-hero__link {
  font: 500 0.75rem / 1 var(--font-mono);
  color: var(--color-primary);
  text-decoration: none;
  padding: 4px 8px;
  border: 1px solid var(--color-border);
  border-radius: 2px;
  transition: border-color var(--duration-fast) var(--ease-smooth);
}

.ks-researcher-hero__link:hover {
  border-color: var(--color-primary);
}

.ks-researcher-hero__link:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

@media (max-width: 640px) {
  .ks-researcher-hero {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  .ks-researcher-hero__stats {
    justify-content: center;
  }
  .ks-researcher-hero__links {
    justify-content: center;
  }
}
</style>
