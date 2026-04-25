<script setup lang="ts">
import { renderPaperMarkdown } from "~/utils/markdown";

export interface WritingPreviewPaneProps {
  title: string;
  markdown: string;
}

const props = defineProps<WritingPreviewPaneProps>();

const renderedHtml = ref("");
const renderPending = ref(false);
const renderError = ref<string | null>(null);

watch(
  () => ({
    title: props.title,
    markdown: props.markdown,
  }),
  async ({ title, markdown }, _previous, onCleanup) => {
    let cancelled = false;
    onCleanup(() => {
      cancelled = true;
    });

    renderPending.value = true;
    renderError.value = null;

    try {
      const rendered = await renderPaperMarkdown(markdown, {
        title,
        sections: [],
        includeHeadings: false,
      });
      if (cancelled) return;

      renderedHtml.value = rendered.html;
    } catch (error) {
      if (cancelled) return;

      renderedHtml.value = "";
      renderError.value =
        error instanceof Error ? error.message : "Preview rendering failed";
    } finally {
      if (!cancelled) renderPending.value = false;
    }
  },
  { immediate: true },
);
</script>

<template>
  <section class="ks-writing-preview" data-testid="writing-preview">
    <div v-if="renderPending" class="ks-writing-preview__state">
      <KsSkeleton height="360px" />
    </div>

    <div v-else-if="renderError" class="ks-writing-preview__state">
      <KsErrorAlert :message="renderError" />
    </div>

    <div v-else class="ks-writing-preview__viewport">
      <article class="ks-writing-preview__paper ks-prose">
        <h1 class="ks-writing-preview__paper-title">
          {{ title || "Untitled" }}
        </h1>
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div v-html="renderedHtml" />
      </article>
    </div>
  </section>
</template>

<style scoped>
.ks-writing-preview {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
}

.ks-writing-preview__state {
  padding: 0.25rem;
}

.ks-writing-preview__viewport {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0.4rem;
  border-radius: 1.1rem;
  background:
    linear-gradient(
      180deg,
      rgba(239, 234, 225, 0.94),
      rgba(235, 229, 219, 0.9)
    ),
    radial-gradient(circle at top, rgba(196, 163, 90, 0.08), transparent 22rem);
}

.ks-writing-preview__paper {
  width: min(100%, 16.75rem);
  margin: 0 auto;
  padding: 1rem 1rem 1.3rem;
  border: 1px solid rgba(226, 220, 208, 0.96);
  border-radius: 0.55rem;
  background: rgba(255, 255, 252, 0.98);
  box-shadow:
    0 14px 28px rgba(76, 67, 52, 0.08),
    0 2px 5px rgba(76, 67, 52, 0.06);
  font-size: 0.7rem;
  line-height: 1.62;
  color: #342e27;
  overflow: hidden;
}

.ks-writing-preview__paper-title {
  margin: 0 0 0.85rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(226, 220, 208, 0.96);
  font: 700 1.02rem / 1.18 var(--font-display);
  color: var(--color-text);
}

:deep(.ks-writing-preview__paper > * + *) {
  margin-top: 0.75rem;
}

:deep(.ks-writing-preview__paper h1),
:deep(.ks-writing-preview__paper h2),
:deep(.ks-writing-preview__paper h3) {
  color: var(--color-text);
  line-height: 1.2;
}

:deep(.ks-writing-preview__paper h1) {
  font-size: 1rem;
}

:deep(.ks-writing-preview__paper h2) {
  font-size: 0.88rem;
}

:deep(.ks-writing-preview__paper h3) {
  font-size: 0.8rem;
}

:deep(.ks-writing-preview__paper img) {
  display: block;
  max-width: 100%;
  max-height: 10rem;
  margin: 0.8rem auto;
  border-radius: 0.45rem;
  object-fit: contain;
}

:deep(.ks-writing-preview__paper p),
:deep(.ks-writing-preview__paper li),
:deep(.ks-writing-preview__paper td),
:deep(.ks-writing-preview__paper th) {
  overflow-wrap: anywhere;
}

:deep(.ks-writing-preview__paper pre) {
  max-width: 100%;
  overflow: hidden;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 0.65rem 0.75rem;
  border-radius: 0.45rem;
  font-size: 0.62rem;
}

:deep(.ks-writing-preview__paper table) {
  display: block;
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  table-layout: fixed;
  font-size: 0.62rem;
}

:deep(.ks-writing-preview__paper mjx-container[jax="SVG"]) {
  max-width: 100%;
  overflow: hidden;
}

:deep(
  .ks-writing-preview__paper mjx-container[jax="SVG"]:not([display="true"])
) {
  display: inline;
  margin: 0;
  white-space: normal;
}

:deep(.ks-writing-preview__paper mjx-container[jax="SVG"][display="true"]) {
  margin: 0.65rem 0;
  overflow: hidden;
}

@media (max-width: 1100px) {
  .ks-writing-preview__paper {
    width: min(100%, 100%);
  }
}
</style>
