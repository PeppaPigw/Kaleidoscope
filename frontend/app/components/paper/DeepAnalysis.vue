<script setup lang="ts">
/**
 * DeepAnalysis — renders LLM deep analysis markdown for a paper.
 *
 * After rendering, emits the actual DOM element IDs (from rehypeSlug, no
 * user-content- prefix) so the page-level outline can build accurate links.
 * Scroll / active tracking is fully owned by the parent page.
 */
import { renderPaperMarkdown } from "~/utils/markdown";

export interface AnalysisItem {
  id: string; // real DOM element id (set by rehypeSlug)
  title: string;
  level: number; // 1–6
}

const props = defineProps<{
  analysis: string;
  badge?: string;
  showHeader?: boolean;
}>();

const emit = defineEmits<{
  analysisItemsReady: [items: AnalysisItem[]];
}>();

const html = ref("");
const containerRef = ref<HTMLElement | null>(null);

watch(
  () => props.analysis,
  async (text) => {
    if (!text) {
      html.value = "";
      emit("analysisItemsReady", []);
      return;
    }

    try {
      const result = await renderPaperMarkdown(text, {
        includeHeadings: false,
      });
      html.value = result.html;
      await nextTick();
      // Query actual headings from the rendered DOM — ids set by rehypeSlug
      const headingEls = Array.from(
        containerRef.value?.querySelectorAll<HTMLElement>(
          "h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]",
        ) ?? [],
      );
      emit(
        "analysisItemsReady",
        headingEls.map((el) => {
          const level = Number.parseInt(el.tagName.slice(1), 10);
          return {
            id: el.id,
            title: el.textContent?.trim() ?? "",
            level: Number.isNaN(level) ? 1 : level,
          };
        }),
      );
    } catch {
      html.value = "";
      emit("analysisItemsReady", []);
    }
  },
  { immediate: true },
);
</script>

<template>
  <section ref="containerRef" class="ks-deep-analysis">
    <div v-if="props.showHeader !== false" class="ks-deep-analysis__header">
      <span class="ks-deep-analysis__badge">{{
        props.badge || "Deep Analysis"
      }}</span>
    </div>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div class="ks-deep-analysis__body markdown-body" v-html="html" />
  </section>
</template>

<style scoped>
.ks-deep-analysis {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-surface, rgba(15, 23, 42, 0.6));
  padding: 28px 32px 32px;
}

.ks-deep-analysis__header {
  margin-bottom: 20px;
}

.ks-deep-analysis__badge {
  font: 600 0.7rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-secondary);
  border: 1px solid var(--color-border);
  border-radius: 3px;
  padding: 3px 8px;
}

/* ── Markdown body ── */
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  color: var(--color-primary, #f8fafc);
  font-family: var(--font-sans);
  line-height: 1.3;
  margin: 1.6em 0 0.5em;
  scroll-margin-top: 88px;
}

.markdown-body :deep(h1) {
  font-size: 1.4rem;
  font-weight: 700;
}
.markdown-body :deep(h2) {
  font-size: 1.1rem;
  font-weight: 700;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border);
}
.markdown-body :deep(h3) {
  font-size: 0.97rem;
  font-weight: 600;
}
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  font-size: 0.88rem;
  font-weight: 600;
}

.markdown-body :deep(p) {
  font: 400 0.92rem / 1.75 var(--font-sans);
  color: var(--color-secondary, #94a3b8);
  margin: 0 0 1em;
  /* allow soft-wrapping between words but never inside a math token */
  overflow-wrap: break-word;
  word-break: normal;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 1.6em;
  margin: 0 0 1em;
}

.markdown-body :deep(li) {
  font: 400 0.92rem / 1.65 var(--font-sans);
  color: var(--color-secondary, #94a3b8);
  margin: 0.25em 0;
}

.markdown-body :deep(blockquote) {
  margin: 1em 0;
  padding: 4px 16px;
  border-left: 3px solid var(--color-border);
  color: var(--color-secondary);
  font-style: italic;
}

.markdown-body :deep(code) {
  font: 400 0.83em var(--font-mono);
  background: rgba(148, 163, 184, 0.08);
  padding: 1px 5px;
  border-radius: 3px;
  /* don't break code tokens at arbitrary points */
  white-space: pre-wrap;
  word-break: break-all;
}

.markdown-body :deep(pre) {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 14px 18px;
  overflow-x: auto;
  margin: 1em 0;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 0.85em;
  white-space: pre;
  word-break: normal;
}

.markdown-body :deep(strong) {
  color: var(--color-primary, #f8fafc);
  font-weight: 600;
}

.markdown-body :deep(em) {
  font-style: italic;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 1.5em 0;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  font-size: 0.88rem;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  text-align: left;
}

.markdown-body :deep(th) {
  background: rgba(148, 163, 184, 0.06);
  font-weight: 600;
  color: var(--color-primary);
}

/* ── MathJax / rehype-mathjax fix ──────────────────────────── */

/* Inline math: keep it inline, do not force a block line-break */
.markdown-body :deep(mjx-container:not([display])) {
  display: inline-block !important;
  vertical-align: -0.15em;
  line-height: 0;
  /* never break the layout by wrapping inside a formula */
  white-space: nowrap;
}

/* Display (block) math: centre it */
.markdown-body :deep(mjx-container[display="true"]) {
  display: block !important;
  line-height: 1;
  margin: 1em auto;
  text-align: center;
  overflow-x: auto;
}

/* SVG-flavour math */
.markdown-body :deep(mjx-container svg) {
  display: inline-block;
  vertical-align: middle;
  overflow: visible;
}

/* CHTML-flavour math */
.markdown-body :deep(mjx-math) {
  display: inline-block;
}
</style>
