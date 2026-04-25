<script setup lang="ts">
/**
 * SearchResultCard -- Card displaying a single DeepXiv search result.
 *
 * Shows title (clickable), abstract truncated to 3 lines, author list,
 * category badges, citation count, and a relevance score bar.
 */
import { BookOpen, Quote, BarChart3, Bookmark } from "lucide-vue-next";

export interface DeepXivSearchResult {
  arxiv_id: string;
  title: string;
  abstract: string;
  authors: string[];
  categories: string[];
  citations: number;
  score: number;
  token_count: number;
}

export interface SearchResultCardProps {
  result: DeepXivSearchResult;
}

defineProps<SearchResultCardProps>();

defineEmits<{
  click: [result: DeepXivSearchResult];
}>();

const scorePercent = (score: number) => Math.round(score * 100);

// Bookmark
const showGroupPicker = ref(false);
</script>

<template>
  <article
    class="ks-search-result-card"
    tabindex="0"
    @click="$emit('click', result)"
    @keydown.enter="$emit('click', result)"
  >
    <div class="ks-search-result-card__header">
      <h3 class="ks-search-result-card__title">{{ result.title }}</h3>
      <span class="ks-search-result-card__id">{{ result.arxiv_id }}</span>
    </div>

    <p class="ks-search-result-card__abstract">{{ result.abstract }}</p>

    <div class="ks-search-result-card__authors">
      <span
        v-for="(author, i) in result.authors.slice(0, 4)"
        :key="i"
        class="ks-search-result-card__author"
      >
        {{ author
        }}<template v-if="i < Math.min(result.authors.length, 4) - 1"
          >,</template
        >
      </span>
      <span
        v-if="result.authors.length > 4"
        class="ks-search-result-card__author"
      >
        et al.
      </span>
    </div>

    <div class="ks-search-result-card__meta">
      <div class="ks-search-result-card__categories">
        <span
          v-for="cat in result.categories"
          :key="cat"
          class="ks-search-result-card__badge"
        >
          {{ cat }}
        </span>
      </div>

      <div class="ks-search-result-card__stats">
        <span class="ks-search-result-card__stat">
          <Quote :size="14" />
          {{ result.citations }}
        </span>
        <span class="ks-search-result-card__stat">
          <BookOpen :size="14" />
          {{ result.token_count.toLocaleString() }} tokens
        </span>
      </div>
    </div>

    <div class="ks-search-result-card__score">
      <div class="ks-search-result-card__score-label">
        <BarChart3 :size="14" />
        <span>Relevance</span>
        <span class="ks-search-result-card__score-value"
          >{{ scorePercent(result.score) }}%</span
        >
      </div>
      <div class="ks-search-result-card__score-track">
        <div
          class="ks-search-result-card__score-fill"
          :style="{ width: `${scorePercent(result.score)}%` }"
        />
      </div>
    </div>

    <!-- Bookmark button -->
    <button
      type="button"
      class="ks-search-result-card__bookmark"
      aria-label="Save to group"
      @click.stop="showGroupPicker = true"
    >
      <Bookmark :size="14" :stroke-width="2" />
    </button>

    <CollectionsGroupPickerModal
      v-if="showGroupPicker"
      :arxiv-id="result.arxiv_id"
      :title="result.title"
      @close="showGroupPicker = false"
      @saved="showGroupPicker = false"
    />
  </article>
</template>

<style scoped>
.ks-search-result-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
  transition:
    transform var(--duration-normal) var(--ease-smooth),
    box-shadow var(--duration-normal) var(--ease-smooth),
    border-color var(--duration-fast) var(--ease-smooth);
}

.ks-search-result-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06);
  border-color: var(--color-primary);
}

.ks-search-result-card:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-search-result-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.ks-search-result-card__title {
  font: 600 1.0625rem / 1.4 var(--font-display);
  color: var(--color-text);
  margin: 0;
  flex: 1;
}

.ks-search-result-card__id {
  flex-shrink: 0;
  font: 500 0.75rem / 1 var(--font-mono);
  color: var(--color-secondary);
}

.ks-search-result-card__abstract {
  font: 400 0.875rem / 1.6 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ks-search-result-card__authors {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  font: 400 0.8125rem / 1.3 var(--font-sans);
  color: var(--color-secondary);
}

.ks-search-result-card__meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding-top: 8px;
  border-top: 1px solid var(--color-border);
}

.ks-search-result-card__categories {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.ks-search-result-card__badge {
  display: inline-block;
  padding: 2px 8px;
  font: 500 0.6875rem / 1.4 var(--font-sans);
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: 3px;
}

.ks-search-result-card__stats {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.ks-search-result-card__stat {
  display: flex;
  align-items: center;
  gap: 4px;
  font: 500 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-search-result-card__score {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ks-search-result-card__score-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font: 500 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-search-result-card__score-value {
  margin-left: auto;
  font-weight: 700;
  color: var(--color-primary);
}

.ks-search-result-card__score-track {
  height: 4px;
  background: var(--color-border);
  border-radius: 2px;
  overflow: hidden;
}

.ks-search-result-card__score-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 2px;
  transition: width var(--duration-normal) var(--ease-smooth);
}

@media (max-width: 640px) {
  .ks-search-result-card__meta {
    flex-direction: column;
    align-items: flex-start;
  }
}

/* Bookmark button — positioned in top-right corner */
.ks-search-result-card {
  position: relative;
}

.ks-search-result-card__bookmark {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 5px;
  color: var(--color-secondary);
  cursor: pointer;
  opacity: 0;
  transition:
    opacity 0.15s,
    background-color 0.15s,
    color 0.15s,
    border-color 0.15s;
}

.ks-search-result-card:hover .ks-search-result-card__bookmark {
  opacity: 1;
}

.ks-search-result-card__bookmark:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-color: var(--color-primary);
}
</style>
