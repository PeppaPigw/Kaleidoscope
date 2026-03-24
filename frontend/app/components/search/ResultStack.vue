<script setup lang="ts">
/**
 * ResultStack — Vertical list of search result cards.
 *
 * Each card displays paper title (linked), authors, venue, year,
 * abstract with matching highlights, relevance score, tags,
 * and action buttons (Save / Compare / Read).
 */

export interface SearchResultItem {
  id: string
  title: string
  authors: string[]
  venue: string
  year: number
  abstract: string
  score: number
  tags: string[]
  cited: number
  openAccess: boolean
}

export interface ResultStackProps {
  results: SearchResultItem[]
  loading?: boolean
}

defineProps<ResultStackProps>()

defineEmits<{
  'paper-click': [paper: SearchResultItem]
  'save': [paper: SearchResultItem]
  'compare': [paper: SearchResultItem]
  'read': [paper: SearchResultItem]
}>()

const uid = useId()
const { t } = useTranslation()
</script>

<template>
  <section class="ks-result-stack" :aria-labelledby="`${uid}-title`">
    <h2 :id="`${uid}-title`" class="sr-only">{{ t('searchResults') }}</h2>

    <!-- Loading skeletons -->
    <div v-if="loading" class="ks-result-stack__list">
      <div v-for="i in 4" :key="i" class="ks-card ks-result-stack__card ks-result-stack__card--skeleton">
        <KsSkeleton variant="line" width="80%" />
        <KsSkeleton variant="line" width="60%" />
        <KsSkeleton variant="paragraph" :lines="3" />
        <KsSkeleton variant="line" width="40%" />
      </div>
    </div>

    <!-- Results -->
    <ol v-else class="ks-result-stack__list">
      <li
        v-for="(result, i) in results"
        :key="result.id"
        :class="[
          'ks-card ks-result-stack__card',
          'ks-motion-paper-reveal',
          `ks-motion-paper-reveal--delay-${(i % 4) + 1}`,
        ]"
      >
        <div class="ks-result-stack__card-header">
          <NuxtLink
            :to="`/papers/${result.id}`"
            class="ks-result-stack__card-title-link"
            @click="$emit('paper-click', result)"
          >
            <KsTranslatableTitle :text="result.title" tag="h3" title-class="ks-result-stack__card-title" />
          </NuxtLink>
          <span class="ks-type-data ks-result-stack__card-score" style="color: var(--color-primary);">
            {{ (result.score * 100).toFixed(0) }}%
          </span>
        </div>

        <div class="ks-result-stack__card-authors">
          <span class="ks-type-data">
            {{ result.authors.slice(0, 3).join(', ') }}
            <template v-if="result.authors.length > 3"> et al.</template>
          </span>
          <span class="ks-result-stack__card-dot">·</span>
          <span class="ks-type-data">{{ result.venue }}</span>
          <span class="ks-result-stack__card-dot">·</span>
          <span class="ks-type-data">{{ result.year }}</span>
          <span v-if="result.openAccess" class="ks-result-stack__card-oa" title="Open Access">🔓</span>
        </div>

        <div class="ks-result-stack__card-abstract-wrap">
          <p class="ks-type-body-sm ks-result-stack__card-abstract">
            {{ result.abstract }}
          </p>
          <KsTranslateBtn :text="result.abstract" />
        </div>

        <div class="ks-result-stack__card-footer">
          <div class="ks-result-stack__card-meta">
            <span class="ks-type-data">Cited {{ result.cited }}</span>
            <KsTag
              v-for="tag in result.tags"
              :key="tag"
              variant="primary"
            >
              {{ tag }}
            </KsTag>
          </div>
          <div class="ks-result-stack__card-actions">
            <KsButton
              variant="secondary"
              size="sm"
              :aria-label="`${t('save')} ${result.title}`"
              @click="$emit('save', result)"
            >
              {{ t('save') }}
            </KsButton>
            <KsButton
              variant="secondary"
              size="sm"
              :aria-label="`${t('compare')} ${result.title}`"
              @click="$emit('compare', result)"
            >
              {{ t('compare') }}
            </KsButton>
            <KsButton
              variant="primary"
              size="sm"
              :aria-label="`${t('readPaper')} ${result.title}`"
              @click="$emit('read', result)"
            >
              {{ t('readPaper') }}
            </KsButton>
          </div>
        </div>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.sr-only {
  position: absolute;
  width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border-width: 0;
}

.ks-result-stack__list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  list-style: none;
  padding: 0;
  margin: 0;
}

.ks-result-stack__card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 24px;
  transition: transform var(--duration-normal) var(--ease-spring),
              box-shadow var(--duration-normal) var(--ease-smooth);
}

.ks-result-stack__card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(26, 26, 26, 0.05);
}

.ks-result-stack__card--skeleton {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ks-result-stack__card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.ks-result-stack__card-title-link {
  text-decoration: none;
  color: inherit;
  flex: 1;
}

.ks-result-stack__card-title-link:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: 2px;
}

.ks-result-stack__card-title {
  font: 600 1.125rem / 1.4 var(--font-serif);
  color: var(--color-text);
}

.ks-result-stack__card-title-link:hover .ks-result-stack__card-title {
  color: var(--color-primary);
}

.ks-result-stack__card-score {
  flex-shrink: 0;
  font-weight: 700;
}

.ks-result-stack__card-authors {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.ks-result-stack__card-dot {
  color: var(--color-border);
}

.ks-result-stack__card-oa {
  font-size: 0.75rem;
}

.ks-result-stack__card-abstract {
  color: var(--color-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ks-result-stack__card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.ks-result-stack__card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ks-result-stack__card-actions {
  display: flex;
  gap: 6px;
}

@media (max-width: 768px) {
  .ks-result-stack__card-footer {
    flex-direction: column;
    align-items: flex-start;
  }
  .ks-result-stack__card-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
