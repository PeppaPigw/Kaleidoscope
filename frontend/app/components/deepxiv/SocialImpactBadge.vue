<script setup lang="ts">
/**
 * SocialImpactBadge -- Displays social engagement metrics for a paper.
 *
 * Shows tweet count, likes, views, replies, and date range.
 * Renders a "No data" placeholder when impact is null.
 */
import { MessageCircle, Heart, Eye, MessageSquare } from "lucide-vue-next";

export interface SocialImpact {
  total_tweets: number;
  total_likes: number;
  total_views: number;
  total_replies: number;
  first_seen_date?: string | null;
  last_seen_date?: string | null;
}

export interface SocialImpactBadgeProps {
  impact: SocialImpact | null;
}

defineProps<SocialImpactBadgeProps>();

function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}
</script>

<template>
  <div class="ks-social-impact">
    <template v-if="impact">
      <div class="ks-social-impact__metrics">
        <div class="ks-social-impact__metric">
          <MessageCircle :size="14" />
          <span class="ks-social-impact__value">{{
            formatCount(impact.total_tweets)
          }}</span>
          <span class="ks-social-impact__label">tweets</span>
        </div>
        <div class="ks-social-impact__metric">
          <Heart :size="14" />
          <span class="ks-social-impact__value">{{
            formatCount(impact.total_likes)
          }}</span>
          <span class="ks-social-impact__label">likes</span>
        </div>
        <div class="ks-social-impact__metric">
          <Eye :size="14" />
          <span class="ks-social-impact__value">{{
            formatCount(impact.total_views)
          }}</span>
          <span class="ks-social-impact__label">views</span>
        </div>
        <div class="ks-social-impact__metric">
          <MessageSquare :size="14" />
          <span class="ks-social-impact__value">{{
            formatCount(impact.total_replies)
          }}</span>
          <span class="ks-social-impact__label">replies</span>
        </div>
      </div>
      <div
        v-if="impact.first_seen_date && impact.last_seen_date"
        class="ks-social-impact__dates"
      >
        {{ formatDate(impact.first_seen_date) }} &ndash;
        {{ formatDate(impact.last_seen_date) }}
      </div>
    </template>
    <div v-else class="ks-social-impact__empty">No social data available</div>
  </div>
</template>

<style scoped>
.ks-social-impact {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 6px;
}

.ks-social-impact__metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.ks-social-impact__metric {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--color-secondary);
}

.ks-social-impact__value {
  font: 700 0.875rem / 1 var(--font-sans);
  color: var(--color-text);
}

.ks-social-impact__label {
  font: 400 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-social-impact__dates {
  font: 400 0.6875rem / 1.2 var(--font-sans);
  color: var(--color-secondary);
}

.ks-social-impact__empty {
  font: 400 0.8125rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
  text-align: center;
  padding: 8px 0;
}
</style>
