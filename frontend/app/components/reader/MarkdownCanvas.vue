<script setup lang="ts">
/**
 * MarkdownCanvas — renders paper full-text as styled markdown.
 *
 * Renders pre-fetched paper markdown through a full remark/rehype pipeline.
 * The page owns the API request so content is fetched once.
 */
import type { PaperContent } from '~/composables/useApi'
import type { RenderedMarkdownHeading } from '../../utils/markdown'
import { renderPaperMarkdown } from '../../utils/markdown'

export interface MarkdownCanvasProps {
  title: string
  content: PaperContent | null
  pending?: boolean
  error?: string | null
}

const props = defineProps<MarkdownCanvasProps>()
const emit = defineEmits<{
  outlineChange: [headings: RenderedMarkdownHeading[]]
  activeHeadingChange: [headingId: string | null]
}>()

const fontSize = ref(16)
const content = computed(() => props.content)
const pending = computed(() => props.pending ?? false)
const errorMessage = computed(() => props.error ?? null)
const renderPending = ref(false)
const renderError = ref<string | null>(null)
const renderedHtml = ref('')
const contentFormat = computed(() => content.value?.format ?? 'unknown')
const displayError = computed(() => errorMessage.value || renderError.value)
const busy = computed(() => pending.value || renderPending.value)
const contentRef = ref<HTMLElement | null>(null)
const renderedRef = ref<HTMLElement | null>(null)

let trackedScrollContainer: HTMLElement | null = null
let syncFrameId: number | null = null

function getHeadingElements(): HTMLElement[] {
  return Array.from(
    renderedRef.value?.querySelectorAll<HTMLElement>('h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]') ?? [],
  )
}

function syncActiveHeading() {
  syncFrameId = null

  if (busy.value || !contentRef.value) {
    emit('activeHeadingChange', null)
    return
  }

  const headings = getHeadingElements()
  if (headings.length === 0) {
    emit('activeHeadingChange', null)
    return
  }

  const containerTop = contentRef.value.getBoundingClientRect().top
  const activationOffset = 96
  let activeHeading = headings[0] ?? null

  for (const heading of headings) {
    const offsetFromTop = heading.getBoundingClientRect().top - containerTop
    if (offsetFromTop <= activationOffset)
      activeHeading = heading
    else
      break
  }

  emit('activeHeadingChange', activeHeading?.id ?? null)
}

function scheduleActiveHeadingSync() {
  if (syncFrameId !== null)
    return

  syncFrameId = window.requestAnimationFrame(syncActiveHeading)
}

function detachScrollTracking() {
  if (trackedScrollContainer) {
    trackedScrollContainer.removeEventListener('scroll', scheduleActiveHeadingSync)
    trackedScrollContainer = null
  }
}

function attachScrollTracking() {
  detachScrollTracking()

  if (!contentRef.value || busy.value)
    return

  trackedScrollContainer = contentRef.value
  trackedScrollContainer.addEventListener('scroll', scheduleActiveHeadingSync, { passive: true })
}

watch(
  () => ({
    markdown: content.value?.markdown ?? '',
    sections: content.value?.sections ?? [],
  }),
  async (payload, _previous, onCleanup) => {
    let cancelled = false
    onCleanup(() => {
      cancelled = true
    })

    if (!content.value) {
      renderedHtml.value = ''
      renderError.value = null
      emit('outlineChange', [])
      return
    }

    renderPending.value = true
    renderError.value = null

    try {
      const rendered = await renderPaperMarkdown(payload.markdown, {
        title: props.title,
        sections: payload.sections,
      })

      if (cancelled)
        return

      renderedHtml.value = rendered.html
      emit('outlineChange', rendered.headings)
    }
    catch (error) {
      if (cancelled)
        return

      renderedHtml.value = ''
      renderError.value = error instanceof Error
        ? error.message
        : 'Failed to render paper content'
      emit('outlineChange', [])
    }
    finally {
      if (!cancelled)
        renderPending.value = false
    }
  },
  { immediate: true, deep: true },
)

watch(
  () => renderedHtml.value,
  async () => {
    await nextTick()
    attachScrollTracking()
    scheduleActiveHeadingSync()
  },
  { flush: 'post' },
)

watch(fontSize, async () => {
  await nextTick()
  scheduleActiveHeadingSync()
})

watch(busy, async (isBusy) => {
  if (isBusy) {
    detachScrollTracking()
    emit('activeHeadingChange', null)
    return
  }

  await nextTick()
  attachScrollTracking()
  scheduleActiveHeadingSync()
})

onMounted(() => {
  window.addEventListener('resize', scheduleActiveHeadingSync)
})

onBeforeUnmount(() => {
  detachScrollTracking()
  window.removeEventListener('resize', scheduleActiveHeadingSync)

  if (syncFrameId !== null)
    window.cancelAnimationFrame(syncFrameId)
})
</script>

<template>
  <div class="ks-mc" :aria-label="`Paper content for ${title}`">
    <!-- Toolbar -->
    <div class="ks-mc__toolbar">
      <div class="ks-mc__meta">
        <span class="ks-mc__badge" :title="contentFormat">
          {{ contentFormat === 'markdown' ? '✦ Full text' : contentFormat === 'abstract_only' ? '◇ Abstract' : '○ Metadata' }}
        </span>
      </div>
      <div class="ks-mc__controls">
        <button class="ks-mc__btn" aria-label="Decrease font" @click="fontSize = Math.max(12, fontSize - 1)">A−</button>
        <span class="ks-type-data">{{ fontSize }}px</span>
        <button class="ks-mc__btn" aria-label="Increase font" @click="fontSize = Math.min(24, fontSize + 1)">A+</button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="busy" class="ks-mc__loading">
      <KsSkeleton height="400px" />
    </div>

    <!-- Error -->
    <div v-else-if="displayError" class="ks-mc__error">
      <KsErrorAlert :message="displayError || 'Failed to load paper content'" />
    </div>

    <!-- Content -->
    <div
      v-else
      ref="contentRef"
      class="ks-mc__content"
      :style="{ fontSize: `${fontSize}px` }"
    >
      <article class="ks-mc__article">
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div
          ref="renderedRef"
          class="ks-mc__rendered ks-prose"
          v-html="renderedHtml"
        />
      </article>
    </div>
  </div>
</template>

<style scoped>
.ks-mc {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  overflow: hidden;
  background: var(--color-bg);
}

.ks-mc__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 5;
  padding: 6px 12px;
  border-bottom: 1px solid var(--color-border);
  background: rgba(250, 250, 247, 0.6);
  backdrop-filter: blur(8px);
}

.ks-mc__meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ks-mc__badge {
  font: 500 0.7rem / 1 var(--font-mono);
  color: var(--color-primary);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 4px 8px;
  border: 1px solid var(--color-primary);
  border-radius: 4px;
}

.ks-mc__controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ks-mc__btn {
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  font: 500 0.8rem / 1 var(--font-mono);
  color: var(--color-text);
  transition: background var(--duration-fast) var(--ease-smooth);
}
.ks-mc__btn:hover {
  background: var(--color-surface);
}

.ks-mc__loading,
.ks-mc__error {
  padding: 24px;
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ks-mc__content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 14px 26px 32px;
  line-height: 1.75;
}

.ks-mc__article {
  width: 100%;
  max-width: none;
  margin: 0;
}

.ks-mc__rendered.ks-prose {
  width: 100%;
  max-width: none;
}

.ks-mc__rendered :deep(h1),
.ks-mc__rendered :deep(h2),
.ks-mc__rendered :deep(h3),
.ks-mc__rendered :deep(h4),
.ks-mc__rendered :deep(h5),
.ks-mc__rendered :deep(h6) {
  scroll-margin-top: 80px;
}

.ks-mc__rendered :deep(h1) {
  margin-top: 0;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid var(--color-primary);
}

.ks-mc__rendered :deep(h2) {
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0.35rem;
}

.ks-mc__rendered :deep(pre) {
  margin: 1.5rem 0;
  padding: 1rem 1.1rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  overflow-x: auto;
}

.ks-mc__rendered :deep(pre code) {
  padding: 0;
  background: transparent;
  border-radius: 0;
}

.ks-mc__rendered :deep(code) {
  font-family: var(--font-mono);
  font-size: 0.88em;
}

.ks-mc__rendered :deep(blockquote) {
  border-left: 3px solid var(--color-primary);
  padding-left: 16px;
  margin: 1.25rem 0;
  color: var(--color-secondary);
  font-style: italic;
}

.ks-mc__rendered :deep(img) {
  display: block;
  width: auto;
  max-width: min(100%, 56rem);
  max-height: min(70vh, 40rem);
  height: auto;
  object-fit: contain;
  margin: 1.5rem auto;
  border-radius: var(--radius-card);
}

.ks-mc__rendered :deep(figure) {
  margin: 1.5rem 0;
}

.ks-mc__rendered :deep(figcaption) {
  font: 400 0.85em / 1.4 var(--font-serif);
  color: var(--color-secondary);
  margin-top: 6px;
  text-align: center;
}

.ks-mc__rendered :deep(table) {
  width: 100%;
  margin: 1.5rem 0;
  border-collapse: collapse;
  border-spacing: 0;
  display: block;
  overflow-x: auto;
}

.ks-mc__rendered :deep(thead th) {
  background: var(--color-surface);
  font-weight: 600;
}

.ks-mc__rendered :deep(th),
.ks-mc__rendered :deep(td) {
  padding: 0.75rem 0.85rem;
  border: 1px solid var(--color-border);
  text-align: left;
  vertical-align: top;
}

.ks-mc__rendered :deep(ul),
.ks-mc__rendered :deep(ol) {
  margin: 1rem 0 1.25rem 1.5rem;
  padding: 0;
}

.ks-mc__rendered :deep(li + li) {
  margin-top: 0.35rem;
}

.ks-mc__rendered :deep(hr) {
  margin: 2rem 0;
  border: none;
  border-top: 1px solid var(--color-border);
}

.ks-mc__rendered :deep(mjx-container[jax='SVG']:not([display='true'])) {
  display: inline-block;
  margin: 0;
  white-space: nowrap;
  overflow-x: visible;
}

.ks-mc__rendered :deep(mjx-container[jax='SVG'][display='true']) {
  display: block;
  margin: 1.25rem 0;
  overflow-x: auto;
  padding: 1rem 0.75rem;
  border-radius: var(--radius-card);
  background: color-mix(in srgb, var(--color-surface) 82%, white 18%);
}

.ks-mc__rendered :deep(header p) {
  width: 100%;
  max-width: none;
}

.ks-mc__rendered :deep(.footnotes) {
  margin-top: 2.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--color-border);
}

@media (max-width: 768px) {
  .ks-mc__content {
    padding: 10px 14px 20px;
  }
}
</style>
