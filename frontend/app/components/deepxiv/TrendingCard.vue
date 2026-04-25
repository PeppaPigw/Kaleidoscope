<script setup lang="ts">
/**
 * TrendingCard — card for a trending arXiv paper.
 *
 * Accepts the raw DeepXivTrendingPaper shape from the API plus an optional
 * brief (title, TLDR, keywords, citations) fetched separately.
 */
import {
  Eye,
  Heart,
  MessageCircle,
  ExternalLink,
  Quote,
} from "lucide-vue-next";
import type {
  DeepXivTrendingPaper,
  DeepXivBriefResponse,
} from "~/composables/useDeepXiv";

interface TrendingCardProps {
  paper: DeepXivTrendingPaper;
  brief?: DeepXivBriefResponse;
  rank?: number;
}

const props = defineProps<TrendingCardProps>();

defineEmits<{ click: [paper: DeepXivTrendingPaper] }>();

function fmt(n: number | undefined): string {
  if (!n) return "0";
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

function fmtDate(d: string | null | undefined): string {
  if (!d) return "";
  return new Date(d).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

const displayRank = computed(() => props.paper.rank ?? props.rank ?? 0);
const title = computed(
  () => props.brief?.title ?? props.paper.title ?? props.paper.arxiv_id,
);
const tldr = computed(() => props.brief?.tldr ?? null);
const keywords = computed(() => props.brief?.keywords?.slice(0, 4) ?? []);
const citations = computed(
  () => props.brief?.citations ?? props.paper.citation_count ?? 0,
);
const publishedAt = computed(() =>
  fmtDate(props.brief?.publish_at ?? props.paper.publish_at),
);

const views = computed(() => props.paper.stats?.total_views ?? 0);
const likes = computed(() => props.paper.stats?.total_likes ?? 0);
const mentions = computed(() => props.paper.stats?.total_mentions ?? 0);
const mentionedBy = computed(() => props.paper.mentioned_by?.slice(0, 3) ?? []);
</script>

<template>
  <article
    class="ks-tc"
    tabindex="0"
    @click="$emit('click', paper)"
    @keydown.enter="$emit('click', paper)"
  >
    <!-- Rank badge -->
    <div class="ks-tc__rank">
      {{ displayRank }}
    </div>

    <!-- Body -->
    <div class="ks-tc__body">
      <!-- Title -->
      <h3 class="ks-tc__title">{{ title }}</h3>

      <!-- TLDR -->
      <p v-if="tldr" class="ks-tc__tldr">{{ tldr }}</p>

      <!-- Keywords -->
      <div v-if="keywords.length > 0" class="ks-tc__keywords">
        <span v-for="kw in keywords" :key="kw" class="ks-tc__kw">{{ kw }}</span>
      </div>

      <!-- Meta row -->
      <div class="ks-tc__meta">
        <span class="ks-tc__arxiv-id">{{ paper.arxiv_id }}</span>
        <span v-if="publishedAt" class="ks-tc__date">{{ publishedAt }}</span>
        <span v-if="citations > 0" class="ks-tc__cite">
          <Quote :size="11" />
          {{ fmt(citations) }}
        </span>
      </div>

      <!-- Mentioned by -->
      <div v-if="mentionedBy.length > 0" class="ks-tc__mentioned">
        <span
          v-for="user in mentionedBy"
          :key="user.username"
          class="ks-tc__mention"
          :title="`${user.name} (${user.followers.toLocaleString()} followers)`"
        >
          @{{ user.username }}
        </span>
        <span
          v-if="(paper.mentioned_by?.length ?? 0) > 3"
          class="ks-tc__mention ks-tc__mention--more"
        >
          +{{ (paper.mentioned_by?.length ?? 0) - 3 }} more
        </span>
      </div>
    </div>

    <!-- Stats + link -->
    <div class="ks-tc__right">
      <div class="ks-tc__stats">
        <span v-if="views > 0" class="ks-tc__stat">
          <Eye :size="13" />
          {{ fmt(views) }}
        </span>
        <span v-if="likes > 0" class="ks-tc__stat">
          <Heart :size="13" />
          {{ fmt(likes) }}
        </span>
        <span v-if="mentions > 0" class="ks-tc__stat">
          <MessageCircle :size="13" />
          {{ fmt(mentions) }}
        </span>
      </div>
      <span class="ks-tc__open">
        <ExternalLink :size="13" />
      </span>
    </div>
  </article>
</template>

<style scoped>
.ks-tc {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  transition:
    transform 0.15s,
    border-color 0.15s,
    box-shadow 0.15s;
}

.ks-tc:hover {
  transform: translateY(-2px);
  border-color: var(--color-primary);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

.ks-tc:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* ─── Rank ──────────────────────────────────────────── */
.ks-tc__rank {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font: 700 0.9375rem / 1 var(--font-display);
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: 50%;
  margin-top: 2px;
}

/* ─── Body ──────────────────────────────────────────── */
.ks-tc__body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ks-tc__title {
  font: 600 0.9375rem / 1.35 var(--font-display);
  color: var(--color-text);
  margin: 0;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.ks-tc__tldr {
  font: 400 0.8125rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
  padding: 5px 9px;
  background: var(--color-primary-light);
  border-left: 2px solid var(--color-primary);
  border-radius: 0 4px 4px 0;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* ─── Keywords ──────────────────────────────────────── */
.ks-tc__keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.ks-tc__kw {
  font: 500 0.6875rem / 1 var(--font-sans);
  color: var(--color-primary);
  background: var(--color-primary-light);
  padding: 2px 7px;
  border-radius: 3px;
}

/* ─── Meta ──────────────────────────────────────────── */
.ks-tc__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.ks-tc__arxiv-id {
  font: 500 0.75rem / 1 var(--font-mono);
  color: var(--color-secondary);
}

.ks-tc__date {
  font: 400 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-tc__cite {
  display: flex;
  align-items: center;
  gap: 3px;
  font: 500 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

/* ─── Mentioned by ──────────────────────────────────── */
.ks-tc__mentioned {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.ks-tc__mention {
  font: 400 0.6875rem / 1.3 var(--font-sans);
  color: var(--color-secondary);
  opacity: 0.85;
}

.ks-tc__mention--more {
  opacity: 0.5;
}

/* ─── Right column ──────────────────────────────────── */
.ks-tc__right {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  padding-top: 2px;
}

.ks-tc__stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.ks-tc__stat {
  display: flex;
  align-items: center;
  gap: 4px;
  font: 500 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
  white-space: nowrap;
}

.ks-tc__open {
  color: var(--color-secondary);
  opacity: 0.4;
  transition:
    opacity 0.15s,
    color 0.15s;
}

.ks-tc:hover .ks-tc__open {
  opacity: 1;
  color: var(--color-primary);
}
</style>
