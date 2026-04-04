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
import type { Note } from '~/utils/notes'

export interface MarkdownCanvasProps {
  title: string
  content: PaperContent | null
  pending?: boolean
  error?: string | null
  noteHighlights?: Note[]
}

const props = defineProps<MarkdownCanvasProps>()
const emit = defineEmits<{
  outlineChange: [headings: RenderedMarkdownHeading[]]
  activeHeadingChange: [headingId: string | null]
  addHighlight: [text: string]
  textSelected: [text: string]
  askAi: [text: string]
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

// ─── Text-selection floating menu ────────────────────────────
const selMenu = ref({ visible: false, x: 0, y: 0, text: '' })

function handleContentMouseup() {
  const sel = window.getSelection()
  if (!sel || sel.isCollapsed || sel.rangeCount === 0) {
    selMenu.value.visible = false
    return
  }
  const text = sel.toString().trim()
  if (text.length < 2) {
    selMenu.value.visible = false
    return
  }
  const range = sel.getRangeAt(0)
  const rect = range.getBoundingClientRect()
  selMenu.value = {
    visible: true,
    x: rect.left + rect.width / 2,
    y: rect.bottom + 8,
    text,
  }
}

function hideSelMenu() {
  selMenu.value.visible = false
}

function handleHighlightClick() {
  emit('addHighlight', selMenu.value.text)
  window.getSelection()?.removeAllRanges()
  hideSelMenu()
}

function handleAnnotateClick() {
  emit('textSelected', selMenu.value.text)
  window.getSelection()?.removeAllRanges()
  hideSelMenu()
}

function handleAskAiClick() {
  emit('askAi', selMenu.value.text)
  window.getSelection()?.removeAllRanges()
  hideSelMenu()
}

function handleDocMousedown(e: MouseEvent) {
  const menu = document.getElementById('ks-mc-sel-menu')
  if (menu && menu.contains(e.target as Node)) return
  hideSelMenu()
}

// ─── Note highlight injection ─────────────────────────────────
function applyNoteHighlights() {
  const container = renderedRef.value
  if (!container) return

  // Remove existing note marks and normalize
  for (const el of Array.from(container.querySelectorAll('.ks-note-hl'))) {
    const parent = el.parentNode
    if (!parent) continue
    while (el.firstChild) parent.insertBefore(el.firstChild, el)
    parent.removeChild(el)
    parent.normalize()
  }

  // Inject new marks
  for (const note of (props.noteHighlights ?? [])) {
    if (!note.selectedText) continue
    wrapFirstOccurrence(container, note.selectedText, note.id, note.type)
  }
}

function wrapFirstOccurrence(root: HTMLElement, searchText: string, noteId: string, type: string) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      // skip already-marked nodes
      if ((node.parentElement as HTMLElement | null)?.closest('.ks-note-hl')) {
        return NodeFilter.FILTER_REJECT
      }
      return NodeFilter.FILTER_ACCEPT
    },
  })

  let node: Text | null
  while ((node = walker.nextNode() as Text | null)) {
    const text = node.textContent ?? ''
    const idx = text.indexOf(searchText)
    if (idx >= 0) {
      const parent = node.parentNode!
      const mark = document.createElement('mark')
      mark.className = `ks-note-hl ks-note-hl--${type}`
      mark.dataset.noteId = noteId
      mark.textContent = text.slice(idx, idx + searchText.length)

      const before = text.slice(0, idx)
      const after = text.slice(idx + searchText.length)

      if (before) parent.insertBefore(document.createTextNode(before), node)
      parent.insertBefore(mark, node)
      if (after) parent.insertBefore(document.createTextNode(after), node)
      parent.removeChild(node)
      return
    }
  }
}

/** Scroll to the DOM mark for a note. Called by the parent page. */
function scrollToNote(noteId: string) {
  const el = renderedRef.value?.querySelector<HTMLElement>(`[data-note-id="${CSS.escape(noteId)}"]`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

defineExpose({ scrollToNote })

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
    applyNoteHighlights()
  },
  { flush: 'post' },
)

// Re-apply highlights whenever the notes list changes
watch(
  () => props.noteHighlights,
  () => { applyNoteHighlights() },
  { deep: true },
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
  document.addEventListener('mousedown', handleDocMousedown)
})

onBeforeUnmount(() => {
  detachScrollTracking()
  window.removeEventListener('resize', scheduleActiveHeadingSync)
  document.removeEventListener('mousedown', handleDocMousedown)

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
      @mouseup="handleContentMouseup"
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

  <!-- Text-selection floating menu -->
  <Teleport to="body">
    <Transition name="ks-mc-sel-fade">
      <div
        v-if="selMenu.visible"
        id="ks-mc-sel-menu"
        class="ks-mc-sel-menu"
        :style="{ left: `${selMenu.x}px`, top: `${selMenu.y}px` }"
      >
        <button class="ks-mc-sel-menu__btn ks-mc-sel-menu__btn--hl" @mousedown.prevent="handleHighlightClick">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M13 3a1 1 0 0 0-1.4 0L5 9.6 6.4 11l6.6-6.6A1 1 0 0 0 13 3zm-8 8L2.5 13.5l1.5.5L6.4 11 5 11z"/></svg>
          Highlight
        </button>
        <div class="ks-mc-sel-menu__sep" />
        <button class="ks-mc-sel-menu__btn" @mousedown.prevent="handleAnnotateClick">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M2 12V14h2l7-7-2-2-7 7z"/><path d="M11.5 3.5l1 1"/></svg>
          Add Note
        </button>
        <div class="ks-mc-sel-menu__sep" />
        <button class="ks-mc-sel-menu__btn ks-mc-sel-menu__btn--ai" @mousedown.prevent="handleAskAiClick">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M6 6.5C6 5.67 6.67 5 7.5 5h.5c.83 0 1.5.67 1.5 1.5 0 .6-.35 1.12-.86 1.37L8 8.5V9.5"/><circle cx="8" cy="11.5" r=".5" fill="currentColor"/></svg>
          Ask AI
        </button>
      </div>
    </Transition>
  </Teleport>
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
  font-size: inherit;
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

/* ── Note highlight marks ──────────────────────────── */
.ks-mc__rendered :deep(.ks-note-hl) {
  background: transparent;
  border-bottom: 2px solid;
  border-radius: 0;
  cursor: default;
  transition: background 0.15s;
}

.ks-mc__rendered :deep(.ks-note-hl--highlight) {
  border-bottom-color: rgba(245, 158, 11, 0.65);
}

.ks-mc__rendered :deep(.ks-note-hl--annotation) {
  border-bottom-color: rgba(99, 102, 241, 0.65);
}

.ks-mc__rendered :deep(.ks-note-hl:hover) {
  background: rgba(245, 158, 11, 0.08);
}

.ks-mc__rendered :deep(.ks-note-hl--annotation:hover) {
  background: rgba(99, 102, 241, 0.08);
}
</style>

<!-- Note: selection menu is Teleported so styles must be non-scoped -->
<style>
/* ── Text-selection floating menu ──────────────────── */
.ks-mc-sel-menu {
  position: fixed;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 0;
  background: var(--color-bg, #0f172a);
  border: 1px solid var(--color-border, rgba(148, 163, 184, 0.2));
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.45);
  z-index: 9999;
  overflow: hidden;
  white-space: nowrap;
}

.ks-mc-sel-menu__btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border: none;
  background: none;
  color: var(--color-text, #f1f5f9);
  font: 500 0.78rem / 1 var(--font-sans, 'Inter', sans-serif);
  cursor: pointer;
  transition: background 0.13s;
}

.ks-mc-sel-menu__btn:hover {
  background: rgba(148, 163, 184, 0.1);
}

.ks-mc-sel-menu__btn--hl {
  color: rgba(245, 158, 11, 0.9);
}

.ks-mc-sel-menu__btn--ai {
  color: rgba(99, 102, 241, 0.95);
}

.ks-mc-sel-menu__sep {
  width: 1px;
  height: 20px;
  background: var(--color-border, rgba(148, 163, 184, 0.2));
  flex-shrink: 0;
}

.ks-mc-sel-fade-enter-active,
.ks-mc-sel-fade-leave-active { transition: opacity 0.1s, transform 0.1s; }
.ks-mc-sel-fade-enter-from,
.ks-mc-sel-fade-leave-to    { opacity: 0; transform: translateX(-50%) translateY(-4px); }
</style>
