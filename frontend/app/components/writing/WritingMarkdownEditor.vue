<script setup lang="ts">
import type { WritingImageUploadResponse } from '~/composables/useApi'
import type { RenderedMarkdownHeading } from '~/utils/markdown'
import { BlockMath, InlineMath } from '@tiptap/extension-mathematics'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'
import { Table } from '@tiptap/extension-table'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import TableRow from '@tiptap/extension-table-row'
import Underline from '@tiptap/extension-underline'
import { Markdown } from '@tiptap/markdown'
import StarterKit from '@tiptap/starter-kit'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import GithubSlugger from 'github-slugger'
import {
  Bold,
  Code2,
  Heading1,
  Heading2,
  Heading3,
  ImagePlus,
  Italic,
  Link2,
  List,
  ListOrdered,
  Pilcrow,
  Quote,
  Redo2,
  Sigma,
  Table2,
  Undo2,
  Underline as UnderlineIcon,
} from 'lucide-vue-next'

import { countMarkdownWords } from '~/utils/writing'

type UploadImageHandler = (file: File) => Promise<WritingImageUploadResponse>
type HeadingElement = HTMLElement & { dataset: DOMStringMap }

const WRITING_HEADING_PREFIX = 'user-content-'

export interface WritingMarkdownEditorProps {
  modelValue: string
  disabled?: boolean
  saveLabel?: string
  uploadImage?: UploadImageHandler
}

const props = withDefaults(defineProps<WritingMarkdownEditorProps>(), {
  modelValue: '',
  disabled: false,
  saveLabel: 'Ready',
  uploadImage: undefined,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'wordCountChange': [value: number]
  'outlineChange': [value: RenderedMarkdownHeading[]]
  'activeHeadingChange': [value: string | null]
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)
const editorSurfaceRef = ref<HTMLElement | null>(null)
const uploadPending = ref(false)
const uploadError = ref<string | null>(null)
const syncingFromProps = ref(false)
const lastMarkdown = ref(props.modelValue)

let activeHeadingFrameId: number | null = null

function emitEditorValue() {
  const value = editor.value?.getMarkdown() ?? ''
  lastMarkdown.value = value
  emit('update:modelValue', value)
  emit('wordCountChange', countMarkdownWords(value))
}

async function insertUploadedImage(file: File) {
  if (!props.uploadImage || !editor.value)
    return

  uploadPending.value = true
  uploadError.value = null

  try {
    const result = await props.uploadImage(file)
    editor.value
      .chain()
      .focus()
      .setImage({
        src: result.url,
        alt: result.alt || file.name,
      })
      .run()
    emitEditorValue()
  }
  catch (error) {
    uploadError.value = error instanceof Error
      ? error.message
      : 'Image upload failed'
  }
  finally {
    uploadPending.value = false
  }
}

function pickImageFile(fileList: FileList | null | undefined): File | null {
  if (!fileList)
    return null

  return Array.from(fileList).find(file => file.type.startsWith('image/')) ?? null
}

function requestImageUpload() {
  fileInputRef.value?.click()
}

function handleFileInputChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  target.value = ''

  if (file)
    void insertUploadedImage(file)
}

function editLink() {
  if (!editor.value)
    return

  const previousUrl = editor.value.getAttributes('link').href || 'https://'
  const nextUrl = window.prompt('Link URL', previousUrl)

  if (nextUrl === null)
    return

  const trimmed = nextUrl.trim()
  if (!trimmed) {
    editor.value.chain().focus().unsetLink().run()
    return
  }

  editor.value.chain().focus().extendMarkRange('link').setLink({ href: trimmed }).run()
}

function editMath(kind: 'inline' | 'block', pos?: number) {
  if (!editor.value)
    return

  const existing = typeof pos === 'number'
    ? String(editor.value.state.doc.nodeAt(pos)?.attrs.latex || '')
    : kind === 'inline'
      ? 'E = mc^2'
      : '\\int_0^1 x^2 \\, dx'

  const label = kind === 'inline' ? 'Inline formula (LaTeX)' : 'Block formula (LaTeX)'
  const nextValue = window.prompt(label, existing)

  if (nextValue === null)
    return

  const latex = nextValue.trim()

  if (typeof pos === 'number') {
    if (!latex) {
      const command = kind === 'inline'
        ? editor.value.commands.deleteInlineMath
        : editor.value.commands.deleteBlockMath
      command({ pos })
    }
    else if (kind === 'inline') {
      editor.value.commands.updateInlineMath({ latex, pos })
    }
    else {
      editor.value.commands.updateBlockMath({ latex, pos })
    }
    emitEditorValue()
    return
  }

  if (!latex)
    return

  if (kind === 'inline')
    editor.value.chain().focus().insertInlineMath({ latex }).run()
  else
    editor.value.chain().focus().insertBlockMath({ latex }).run()

  emitEditorValue()
}

function handleTransferFiles(fileList: FileList | null | undefined): boolean {
  const file = pickImageFile(fileList)
  if (!file)
    return false

  void insertUploadedImage(file)
  return true
}

function getHeadingElements(): HeadingElement[] {
  return Array.from(
    editorSurfaceRef.value?.querySelectorAll<HeadingElement>(
      '.ks-writing-editor__prosemirror h1, .ks-writing-editor__prosemirror h2, .ks-writing-editor__prosemirror h3',
    ) ?? [],
  )
}

function syncOutlineHeadings() {
  const slugger = new GithubSlugger()
  const headings: RenderedMarkdownHeading[] = []

  for (const heading of getHeadingElements()) {
    const title = heading.innerText.trim()
    if (!title) {
      heading.removeAttribute('id')
      delete heading.dataset.headingId
      continue
    }

    const level = Number.parseInt(heading.tagName.replace('H', ''), 10)
    const id = `${WRITING_HEADING_PREFIX}${slugger.slug(title)}`
    heading.id = id
    heading.dataset.headingId = id
    headings.push({ id, title, level })
  }

  emit('outlineChange', headings)
  return headings
}

function syncActiveHeading() {
  activeHeadingFrameId = null

  const headings = getHeadingElements().filter(heading => heading.dataset.headingId)
  if (headings.length === 0) {
    emit('activeHeadingChange', null)
    return
  }

  const activationOffset = 156
  let activeHeading = headings[0] ?? null

  for (const heading of headings) {
    if (heading.getBoundingClientRect().top <= activationOffset)
      activeHeading = heading
    else
      break
  }

  emit('activeHeadingChange', activeHeading?.dataset.headingId ?? null)
}

function scheduleActiveHeadingSync() {
  if (activeHeadingFrameId !== null)
    return

  activeHeadingFrameId = window.requestAnimationFrame(syncActiveHeading)
}

async function refreshOutlineState() {
  await nextTick()
  syncOutlineHeadings()
  scheduleActiveHeadingSync()
}

function scrollToHeading(headingId: string) {
  const selector = `#${window.CSS?.escape?.(headingId) ?? headingId}`
  const heading = editorSurfaceRef.value?.querySelector<HTMLElement>(selector)
  heading?.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  })
}

const editor = useEditor({
  content: props.modelValue,
  contentType: 'markdown',
  editable: !props.disabled,
  editorProps: {
    attributes: {
      class: 'ks-writing-editor__prosemirror',
      spellcheck: 'true',
    },
    handlePaste: (_view, event) => {
      const handled = handleTransferFiles(event.clipboardData?.files)
      if (handled)
        event.preventDefault()
      return handled
    },
    handleDrop: (_view, event) => {
      const handled = handleTransferFiles(event.dataTransfer?.files)
      if (handled)
        event.preventDefault()
      return handled
    },
  },
  extensions: [
    StarterKit.configure({
      heading: { levels: [1, 2, 3] },
      codeBlock: {
        HTMLAttributes: { class: 'ks-writing-editor__code' },
      },
    }),
    Markdown,
    Underline,
    Link.configure({
      openOnClick: false,
      autolink: true,
      defaultProtocol: 'https',
    }),
    Image,
    Placeholder.configure({
      placeholder: ({ node }) => node.type.name === 'heading'
        ? 'Section heading'
        : 'Write in rich text. Kaleidoscope will persist Markdown behind the scenes.',
    }),
    Table.configure({
      resizable: true,
      HTMLAttributes: { class: 'ks-writing-editor__table' },
    }),
    TableRow,
    TableHeader,
    TableCell,
    InlineMath.configure({
      katexOptions: {
        throwOnError: false,
      },
      onClick: (_node, pos) => {
        editMath('inline', pos)
      },
    }),
    BlockMath.configure({
      katexOptions: {
        throwOnError: false,
      },
      onClick: (_node, pos) => {
        editMath('block', pos)
      },
    }),
  ],
  onCreate: () => {
    emit('wordCountChange', countMarkdownWords(props.modelValue))
    void refreshOutlineState()
  },
  onUpdate: () => {
    if (syncingFromProps.value)
      return

    uploadError.value = null
    emitEditorValue()
    void refreshOutlineState()
  },
})

watch(
  () => props.modelValue,
  (value) => {
    if (!editor.value)
      return

    const nextMarkdown = value ?? ''
    if (nextMarkdown === lastMarkdown.value)
      return

    syncingFromProps.value = true
    editor.value.commands.setContent(nextMarkdown, { contentType: 'markdown' })
    lastMarkdown.value = editor.value.getMarkdown()
    emit('wordCountChange', countMarkdownWords(lastMarkdown.value))
    nextTick(() => {
      syncingFromProps.value = false
    })
    void refreshOutlineState()
  },
)

watch(
  () => props.disabled,
  (disabled) => {
    editor.value?.setEditable(!disabled)
  },
)

onBeforeUnmount(() => {
  window.removeEventListener('scroll', scheduleActiveHeadingSync)
  window.removeEventListener('resize', scheduleActiveHeadingSync)

  if (activeHeadingFrameId !== null)
    window.cancelAnimationFrame(activeHeadingFrameId)

  editor.value?.destroy()
})

onMounted(() => {
  window.addEventListener('scroll', scheduleActiveHeadingSync, { passive: true })
  window.addEventListener('resize', scheduleActiveHeadingSync)
  void refreshOutlineState()
})

defineExpose({
  scrollToHeading,
})
</script>

<template>
  <section class="ks-writing-editor">
    <div class="ks-writing-editor__toolbar">
      <div class="ks-writing-editor__group">
        <button
          type="button"
          class="ks-writing-editor__tool"
          :class="{ 'is-active': editor?.isActive('paragraph') }"
          aria-label="Paragraph"
          @click="editor?.chain().focus().setParagraph().run()"
        >
          <Pilcrow :size="16" />
        </button>
        <button
          type="button"
          class="ks-writing-editor__tool"
          :class="{ 'is-active': editor?.isActive('heading', { level: 1 }) }"
          aria-label="Heading 1"
          @click="editor?.chain().focus().toggleHeading({ level: 1 }).run()"
        >
          <Heading1 :size="16" />
        </button>
        <button
          type="button"
          class="ks-writing-editor__tool"
          :class="{ 'is-active': editor?.isActive('heading', { level: 2 }) }"
          aria-label="Heading 2"
          @click="editor?.chain().focus().toggleHeading({ level: 2 }).run()"
        >
          <Heading2 :size="16" />
        </button>
        <button
          type="button"
          class="ks-writing-editor__tool"
          :class="{ 'is-active': editor?.isActive('heading', { level: 3 }) }"
          aria-label="Heading 3"
          @click="editor?.chain().focus().toggleHeading({ level: 3 }).run()"
        >
          <Heading3 :size="16" />
        </button>
      </div>

      <div class="ks-writing-editor__group">
        <button
          type="button"
          class="ks-writing-editor__tool"
          :class="{ 'is-active': editor?.isActive('bold') }"
          aria-label="Bold"
          @click="editor?.chain().focus().toggleBold().run()"
        >
          <Bold :size="16" />
        </button>
        <button
          type="button"
          class="ks-writing-editor__tool"
          :class="{ 'is-active': editor?.isActive('italic') }"
          aria-label="Italic"
          @click="editor?.chain().focus().toggleItalic().run()"
        >
          <Italic :size="16" />
        </button>
        <button
          type="button"
          class="ks-writing-editor__tool"
          :class="{ 'is-active': editor?.isActive('underline') }"
          aria-label="Underline"
          @click="editor?.chain().focus().toggleUnderline().run()"
        >
          <UnderlineIcon :size="16" />
        </button>
        <button
          type="button"
          class="ks-writing-editor__tool"
          :class="{ 'is-active': editor?.isActive('bulletList') }"
          aria-label="Bullet list"
          @click="editor?.chain().focus().toggleBulletList().run()"
        >
          <List :size="16" />
        </button>
        <button
          type="button"
          class="ks-writing-editor__tool"
          :class="{ 'is-active': editor?.isActive('orderedList') }"
          aria-label="Ordered list"
          @click="editor?.chain().focus().toggleOrderedList().run()"
        >
          <ListOrdered :size="16" />
        </button>
        <button
          type="button"
          class="ks-writing-editor__tool"
          :class="{ 'is-active': editor?.isActive('blockquote') }"
          aria-label="Blockquote"
          @click="editor?.chain().focus().toggleBlockquote().run()"
        >
          <Quote :size="16" />
        </button>
        <button
          type="button"
          class="ks-writing-editor__tool"
          :class="{ 'is-active': editor?.isActive('codeBlock') }"
          aria-label="Code block"
          @click="editor?.chain().focus().toggleCodeBlock().run()"
        >
          <Code2 :size="16" />
        </button>
      </div>

      <div class="ks-writing-editor__group">
        <button type="button" class="ks-writing-editor__tool" aria-label="Edit link" @click="editLink">
          <Link2 :size="16" />
        </button>
        <button type="button" class="ks-writing-editor__tool" aria-label="Upload image" @click="requestImageUpload">
          <ImagePlus :size="16" />
        </button>
        <button type="button" class="ks-writing-editor__tool" aria-label="Insert inline math" @click="editMath('inline')">
          <span class="ks-writing-editor__tool-text">$x$</span>
        </button>
        <button type="button" class="ks-writing-editor__tool" aria-label="Insert block math" @click="editMath('block')">
          <Sigma :size="16" />
        </button>
        <button
          type="button"
          class="ks-writing-editor__tool"
          aria-label="Insert table"
          @click="editor?.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()"
        >
          <Table2 :size="16" />
        </button>
      </div>

      <div class="ks-writing-editor__group ks-writing-editor__group--status">
        <button type="button" class="ks-writing-editor__tool" aria-label="Undo" @click="editor?.chain().focus().undo().run()">
          <Undo2 :size="16" />
        </button>
        <button type="button" class="ks-writing-editor__tool" aria-label="Redo" @click="editor?.chain().focus().redo().run()">
          <Redo2 :size="16" />
        </button>
        <span class="ks-writing-editor__status">
          {{ uploadPending ? 'Uploading image…' : saveLabel }}
        </span>
      </div>
    </div>

    <div v-if="uploadError" class="ks-writing-editor__notice">
      {{ uploadError }}
    </div>

    <input
      ref="fileInputRef"
      data-testid="writing-image-input"
      class="ks-writing-editor__file-input"
      type="file"
      accept="image/*"
      @change="handleFileInputChange"
    >

    <div ref="editorSurfaceRef" class="ks-writing-editor__surface">
      <EditorContent v-if="editor" :editor="editor" class="ks-writing-editor__content" />
      <div v-else class="ks-writing-editor__empty">
        Loading editor…
      </div>
    </div>
  </section>
</template>

<style scoped>
.ks-writing-editor {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(250, 250, 247, 0.92)),
    radial-gradient(circle at top right, rgba(196, 163, 90, 0.08), transparent 28%);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.ks-writing-editor__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: space-between;
  padding: 0.9rem 1rem;
  border-bottom: 1px solid rgba(232, 229, 224, 0.92);
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(14px);
}

.ks-writing-editor__group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.ks-writing-editor__group--status {
  margin-left: auto;
}

.ks-writing-editor__tool {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.2rem;
  height: 2.2rem;
  border: 1px solid rgba(232, 229, 224, 0.92);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.78);
  color: var(--color-text);
  cursor: pointer;
  transition:
    transform var(--duration-fast) var(--ease-smooth),
    border-color var(--duration-fast) var(--ease-smooth),
    background-color var(--duration-fast) var(--ease-smooth);
}

.ks-writing-editor__tool:hover {
  transform: translateY(-1px);
  border-color: rgba(13, 115, 119, 0.28);
  background: rgba(13, 115, 119, 0.08);
}

.ks-writing-editor__tool.is-active {
  border-color: rgba(13, 115, 119, 0.42);
  background: rgba(13, 115, 119, 0.14);
  color: var(--color-primary);
}

.ks-writing-editor__tool-text {
  font: 600 0.8rem / 1 var(--font-mono);
}

.ks-writing-editor__status {
  font: 600 0.72rem / 1.1 var(--font-sans);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-secondary);
  padding-left: 0.4rem;
}

.ks-writing-editor__notice {
  padding: 0.75rem 1rem 0;
  color: #8b3a18;
  font: 500 0.85rem / 1.4 var(--font-sans);
}

.ks-writing-editor__file-input {
  display: none;
}

.ks-writing-editor__surface {
  flex: 1;
  min-height: calc(100dvh - 15.5rem);
}

.ks-writing-editor__content {
  min-height: 100%;
}

.ks-writing-editor__empty {
  display: grid;
  place-items: center;
  min-height: calc(100dvh - 15.5rem);
  color: var(--color-secondary);
  font: 500 0.95rem / 1.5 var(--font-serif);
}

:deep(.ks-writing-editor__prosemirror) {
  min-height: calc(100dvh - 15.5rem);
  padding: 2rem 2.2rem 2.4rem;
  font: 400 1.05rem / 1.82 var(--font-serif);
  color: var(--color-text);
  outline: none;
}

:deep(.ks-writing-editor__prosemirror > * + *) {
  margin-top: 1.1rem;
}

:deep(.ks-writing-editor__prosemirror h1),
:deep(.ks-writing-editor__prosemirror h2),
:deep(.ks-writing-editor__prosemirror h3) {
  font-family: var(--font-display);
  line-height: 1.18;
  color: var(--color-text);
}

:deep(.ks-writing-editor__prosemirror h1) {
  font-size: 2rem;
}

:deep(.ks-writing-editor__prosemirror h2) {
  font-size: 1.55rem;
}

:deep(.ks-writing-editor__prosemirror h3) {
  font-size: 1.2rem;
}

:deep(.ks-writing-editor__prosemirror p) {
  margin: 0;
}

:deep(.ks-writing-editor__prosemirror ul),
:deep(.ks-writing-editor__prosemirror ol) {
  padding-left: 1.5rem;
}

:deep(.ks-writing-editor__prosemirror blockquote) {
  border-left: 2px solid rgba(13, 115, 119, 0.32);
  padding-left: 1rem;
  color: #4f4a43;
  font-style: italic;
}

:deep(.ks-writing-editor__prosemirror pre) {
  padding: 1rem 1.15rem;
  border-radius: 1rem;
  background: #141414;
  color: #f8f8f2;
  overflow-x: auto;
  font: 500 0.9rem / 1.65 var(--font-mono);
}

:deep(.ks-writing-editor__prosemirror code) {
  font-family: var(--font-mono);
}

:deep(.ks-writing-editor__prosemirror img) {
  display: block;
  max-width: min(100%, 44rem);
  max-height: 32rem;
  margin: 1.4rem auto;
  border-radius: 1rem;
  object-fit: contain;
  box-shadow: var(--shadow-card);
}

:deep(.ks-writing-editor__prosemirror table) {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

:deep(.ks-writing-editor__prosemirror th),
:deep(.ks-writing-editor__prosemirror td) {
  border: 1px solid var(--color-border);
  padding: 0.55rem 0.65rem;
  vertical-align: top;
}

:deep(.ks-writing-editor__prosemirror th) {
  background: rgba(13, 115, 119, 0.08);
  font-weight: 600;
}

:deep(.ks-writing-editor__prosemirror .tiptap-mathematics-render) {
  border: 1px dashed rgba(13, 115, 119, 0.26);
  border-radius: 0.9rem;
  background: rgba(13, 115, 119, 0.05);
  cursor: pointer;
}

:deep(.ks-writing-editor__prosemirror .tiptap-mathematics-render--editable) {
  transition: background-color var(--duration-fast) var(--ease-smooth);
}

:deep(.ks-writing-editor__prosemirror .tiptap-mathematics-render--editable:hover) {
  background: rgba(13, 115, 119, 0.1);
}

:deep(.ks-writing-editor__prosemirror span.tiptap-mathematics-render) {
  display: inline-flex;
  align-items: center;
  padding: 0.15rem 0.45rem;
  margin: 0 0.12rem;
}

:deep(.ks-writing-editor__prosemirror div.tiptap-mathematics-render) {
  display: block;
  padding: 0.8rem 1rem;
  margin: 1.25rem 0;
}

:deep(.ks-writing-editor__prosemirror .is-empty::before) {
  content: attr(data-placeholder);
  float: left;
  height: 0;
  color: rgba(107, 107, 107, 0.9);
  pointer-events: none;
}

@media (max-width: 900px) {
  .ks-writing-editor__toolbar {
    gap: 0.55rem;
  }

  .ks-writing-editor__group--status {
    width: 100%;
    justify-content: flex-end;
    margin-left: 0;
  }

  :deep(.ks-writing-editor__prosemirror) {
    padding: 1.2rem 1rem 1.5rem;
  }
}
</style>
