<script setup lang="ts">
/**
 * PaperFolio — Hero section for Paper Profile page.
 *
 * Displays the paper's title, authors, venue, year, DOI badge,
 * open-access status, and primary action buttons (Read, Save, Cite).
 */

export interface PaperAuthor {
  id: string
  name: string
  affiliation?: string
}

export interface PaperFolioProps {
  paperId?: string
  title: string
  titleZh?: string
  authors: PaperAuthor[]
  venue: string
  year: number
  doi?: string
  openAccess: boolean
  abstract: string
  abstractZh?: string
  citedBy: number
  references: number
}

defineProps<PaperFolioProps>()

defineEmits<{
  'read': []
  'save': []
  'cite': []
  'author-click': [author: PaperAuthor]
}>()

const { t } = useTranslation()
const uid = useId()
</script>

<template>
  <header class="ks-paper-folio ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <div class="ks-paper-folio__badges">
      <KsTag v-if="openAccess" variant="primary">Open Access</KsTag>
      <KsTag variant="neutral">{{ venue }} {{ year }}</KsTag>
      <a v-if="doi" :href="`https://doi.org/${doi}`" target="_blank" rel="noopener" class="ks-paper-folio__doi">
        DOI: {{ doi }}
      </a>
    </div>

    <KsTranslatableTitle :text="title" :paper-id="paperId" :title-zh="titleZh" tag="h1" title-class="ks-paper-folio__title" />

    <div class="ks-paper-folio__authors">
      <button
        v-for="author in authors"
        :key="author.id"
        type="button"
        class="ks-paper-folio__author"
        @click="$emit('author-click', author)"
      >
        <span class="ks-paper-folio__author-name">{{ author.name }}</span>
        <span v-if="author.affiliation" class="ks-type-data">{{ author.affiliation }}</span>
      </button>
    </div>

    <p class="ks-paper-folio__abstract">{{ abstract }}</p>
    <KsTranslateBtn v-if="abstract" :text="abstract" :paper-id="paperId" :abstract-zh="abstractZh" />

    <div class="ks-paper-folio__stats">
      <span class="ks-type-data"><strong>{{ citedBy }}</strong> citations</span>
      <span class="ks-paper-folio__stat-dot">·</span>
      <span class="ks-type-data"><strong>{{ references }}</strong> references</span>
    </div>

    <div class="ks-paper-folio__actions">
      <KsButton variant="primary" @click="$emit('read')">{{ t('readPaper') }}</KsButton>
      <KsButton variant="secondary" @click="$emit('save')">{{ t('save') }}</KsButton>
      <KsButton variant="secondary" @click="$emit('cite')">{{ t('cite') }}</KsButton>
    </div>
  </header>
</template>

<style scoped>
.ks-paper-folio {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 40px 0;
  border-bottom: 1px solid var(--color-border);
}

.ks-paper-folio__badges {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.ks-paper-folio__doi {
  font: 500 0.75rem / 1 var(--font-mono);
  color: var(--color-primary);
  text-decoration: none;
}

.ks-paper-folio__doi:hover {
  text-decoration: underline;
}

.ks-paper-folio__title {
  font: 700 2rem / 1.3 var(--font-display);
  color: var(--color-text);
  max-width: 800px;
}

.ks-paper-folio__authors {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.ks-paper-folio__author {
  display: flex;
  flex-direction: column;
  padding: 6px 10px;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 2px;
  cursor: pointer;
  text-align: left;
  transition: border-color var(--duration-fast) var(--ease-smooth),
              background-color var(--duration-fast) var(--ease-smooth);
}

.ks-paper-folio__author:hover {
  border-color: var(--color-primary);
  background: rgba(13, 115, 119, 0.04);
}

.ks-paper-folio__author:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-paper-folio__author-name {
  font: 600 0.875rem / 1.3 var(--font-sans);
  color: var(--color-text);
}

.ks-paper-folio__abstract {
  font: 400 1rem / 1.7 var(--font-serif);
  color: var(--color-secondary);
}

.ks-paper-folio__stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ks-paper-folio__stat-dot {
  color: var(--color-border);
}

.ks-paper-folio__actions {
  display: flex;
  gap: 8px;
  padding-top: 8px;
}

@media (max-width: 768px) {
  .ks-paper-folio__title {
    font-size: 1.5rem;
  }
  .ks-paper-folio__actions {
    flex-direction: column;
  }
}
</style>
