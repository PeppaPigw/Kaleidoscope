<script setup lang="ts">
/**
 * NotesPanel — sidebar note-taking panel for the Smart Reader.
 *
 * Three note types:
 *   highlight   — underlined text only (no content)
 *   manual      — free-form note added via the + button
 *   annotation  — underlined text + user note
 *
 * Notes are listed in creation order (oldest first).
 * Clicking a highlight or annotation note jumps to that text in the reading area.
 * A search bar filters across selected text and note content.
 */

import type { Note } from '~/utils/notes'

const props = defineProps<{
  notes: Note[]
  /** When set, the panel pre-opens the annotation form with this text. */
  pendingText?: string | null
}>()

const emit = defineEmits<{
  'note-click': [note: Note]
  'add-highlight': [selectedText: string]
  'add-annotation': [selectedText: string, content: string]
  'add-manual': [content: string]
  'delete-note': [id: string]
  /** Emitted when the pending annotation is dismissed or submitted. */
  'pending-done': []
}>()

const searchQuery = ref('')
const showManualForm = ref(false)
const manualContent = ref('')

// Annotation form (triggered by text selection)
const annotationContent = ref('')

// When pendingText arrives, focus the annotation textarea
const annotationTextareaRef = ref<HTMLTextAreaElement | null>(null)
watch(
  () => props.pendingText,
  async (text) => {
    if (text) {
      annotationContent.value = ''
      await nextTick()
      annotationTextareaRef.value?.focus()
    }
  },
)

const filteredNotes = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  const sorted = [...props.notes].sort((a, b) => a.createdAt - b.createdAt)
  if (!q) return sorted
  return sorted.filter(n =>
    n.selectedText?.toLowerCase().includes(q)
    || n.content?.toLowerCase().includes(q),
  )
})

function submitManual() {
  const c = manualContent.value.trim()
  if (!c) return
  emit('add-manual', c)
  manualContent.value = ''
  showManualForm.value = false
}

function submitAnnotation() {
  if (!props.pendingText) return
  emit('add-annotation', props.pendingText, annotationContent.value.trim())
  annotationContent.value = ''
  emit('pending-done')
}

function cancelAnnotation() {
  annotationContent.value = ''
  emit('pending-done')
}

function typeLabel(type: Note['type']) {
  if (type === 'highlight') return 'Highlight'
  if (type === 'manual') return 'Note'
  return 'Annotation'
}
</script>

<template>
  <div class="ks-np">
    <!-- Header row -->
    <div class="ks-np__header">
      <span class="ks-np__title">Notes <span class="ks-np__count">({{ notes.length }})</span></span>
      <button
        class="ks-np__add-btn"
        title="Add a manual note"
        @click="showManualForm = !showManualForm; annotationContent = ''; $emit('pending-done')"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <line x1="7" y1="1" x2="7" y2="13" />
          <line x1="1" y1="7" x2="13" y2="7" />
        </svg>
      </button>
    </div>

    <!-- Search -->
    <div class="ks-np__search-wrap">
      <svg class="ks-np__search-icon" width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
        <circle cx="6.5" cy="6.5" r="5" />
        <line x1="10.5" y1="10.5" x2="14.5" y2="14.5" />
      </svg>
      <input
        v-model="searchQuery"
        class="ks-np__search"
        type="search"
        placeholder="Search notes…"
        aria-label="Search notes"
      >
    </div>

    <!-- Manual note form -->
    <div v-if="showManualForm" class="ks-np__form">
      <textarea
        v-model="manualContent"
        class="ks-np__textarea"
        placeholder="Write a note…"
        rows="3"
        @keydown.ctrl.enter.prevent="submitManual"
        @keydown.meta.enter.prevent="submitManual"
        @keydown.escape="showManualForm = false; manualContent = ''"
      />
      <div class="ks-np__form-actions">
        <button class="ks-np__btn-cancel" @click="showManualForm = false; manualContent = ''">Cancel</button>
        <button class="ks-np__btn-save" :disabled="!manualContent.trim()" @click="submitManual">Save</button>
      </div>
    </div>

    <!-- Annotation form (pending text selection) -->
    <div v-if="pendingText && !showManualForm" class="ks-np__form ks-np__form--annotation">
      <div class="ks-np__pending-quote">
        <span class="ks-np__pending-q">"</span>
        <span class="ks-np__pending-text">{{ pendingText }}</span>
      </div>
      <textarea
        ref="annotationTextareaRef"
        v-model="annotationContent"
        class="ks-np__textarea"
        placeholder="Add your note about this passage…"
        rows="3"
        @keydown.ctrl.enter.prevent="submitAnnotation"
        @keydown.meta.enter.prevent="submitAnnotation"
        @keydown.escape="cancelAnnotation"
      />
      <div class="ks-np__form-actions">
        <button class="ks-np__btn-cancel" @click="cancelAnnotation">Cancel</button>
        <button class="ks-np__btn-save" @click="submitAnnotation">Save annotation</button>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="filteredNotes.length === 0 && !showManualForm && !pendingText" class="ks-np__empty">
      <template v-if="notes.length === 0">
        Select text to highlight or annotate, or click <strong>+</strong> to add a note.
      </template>
      <template v-else>No notes match your search.</template>
    </div>

    <!-- Note list -->
    <div class="ks-np__list">
      <div
        v-for="note in filteredNotes"
        :key="note.id"
        :class="['ks-np__item', `ks-np__item--${note.type}`]"
      >
        <!-- Type badge -->
        <span class="ks-np__badge">{{ typeLabel(note.type) }}</span>

        <!-- Quoted text (highlight + annotation) — clickable to jump -->
        <button
          v-if="note.selectedText"
          class="ks-np__quote"
          :title="`Jump to: ${note.selectedText}`"
          @click="$emit('note-click', note)"
        >
          <span class="ks-np__q">"</span>{{ note.selectedText }}
        </button>

        <!-- Note content (manual + annotation) -->
        <p v-if="note.content" class="ks-np__content">{{ note.content }}</p>

        <!-- Delete -->
        <button class="ks-np__delete" aria-label="Delete note" @click="$emit('delete-note', note.id)">
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <line x1="1" y1="1" x2="9" y2="9" />
            <line x1="9" y1="1" x2="1" y2="9" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ks-np {
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: 100%;
}

/* Header */
.ks-np__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2px;
}

.ks-np__title {
  font: 600 0.7rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-secondary);
}

.ks-np__count {
  font-weight: 400;
}

.ks-np__add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: none;
  color: var(--color-secondary);
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s, background 0.15s;
}

.ks-np__add-btn:hover {
  color: var(--color-primary);
  border-color: var(--color-primary);
  background: rgba(99, 102, 241, 0.06);
}

/* Search */
.ks-np__search-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.ks-np__search-icon {
  position: absolute;
  left: 8px;
  color: var(--color-secondary);
  pointer-events: none;
}

.ks-np__search {
  width: 100%;
  padding: 5px 8px 5px 26px;
  background: var(--color-surface, rgba(30, 41, 59, 0.4));
  border: 1px solid var(--color-border);
  border-radius: 5px;
  font: 400 0.78rem / 1 var(--font-sans);
  color: var(--color-text);
  transition: border-color 0.15s;
}

.ks-np__search:focus {
  outline: none;
  border-color: var(--color-primary);
}

/* Forms */
.ks-np__form {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-surface, rgba(30, 41, 59, 0.4));
}

.ks-np__form--annotation {
  border-color: rgba(99, 102, 241, 0.4);
}

.ks-np__pending-quote {
  font: italic 400 0.78rem / 1.45 var(--font-serif);
  color: var(--color-secondary);
  padding: 4px 6px;
  border-left: 2px solid rgba(99, 102, 241, 0.5);
  margin-bottom: 2px;
}

.ks-np__pending-q {
  color: rgba(99, 102, 241, 0.7);
  font-size: 1em;
  margin-right: 2px;
}

.ks-np__pending-text {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ks-np__textarea {
  width: 100%;
  padding: 7px 9px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font: 400 0.8125rem / 1.5 var(--font-sans);
  color: var(--color-text);
  resize: vertical;
  min-height: 64px;
  transition: border-color 0.15s;
}

.ks-np__textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}

.ks-np__form-actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}

.ks-np__btn-cancel {
  padding: 4px 10px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: none;
  color: var(--color-secondary);
  font: 500 0.75rem / 1 var(--font-sans);
  cursor: pointer;
}

.ks-np__btn-cancel:hover {
  color: var(--color-text);
  border-color: var(--color-text);
}

.ks-np__btn-save {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  background: var(--color-primary);
  color: #fff;
  font: 600 0.75rem / 1 var(--font-sans);
  cursor: pointer;
  transition: opacity 0.15s;
}

.ks-np__btn-save:disabled {
  opacity: 0.4;
  cursor: default;
}

/* Empty state */
.ks-np__empty {
  font: 400 0.8rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  text-align: center;
  padding: 20px 8px;
}

/* Note list */
.ks-np__list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-y: auto;
  flex: 1;
}

.ks-np__item {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 28px 8px 10px;
  border-radius: 5px;
  border-left: 3px solid transparent;
  background: var(--color-surface, rgba(30, 41, 59, 0.35));
  transition: background 0.15s;
}

.ks-np__item--highlight {
  border-left-color: rgba(245, 158, 11, 0.7);
}

.ks-np__item--manual {
  border-left-color: rgba(100, 116, 139, 0.5);
}

.ks-np__item--annotation {
  border-left-color: rgba(99, 102, 241, 0.7);
}

.ks-np__badge {
  font: 600 0.6rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-secondary);
  margin-bottom: 1px;
}

.ks-np__item--highlight .ks-np__badge { color: rgba(245, 158, 11, 0.8); }
.ks-np__item--annotation .ks-np__badge { color: rgba(99, 102, 241, 0.8); }

/* Quote (clickable) */
.ks-np__quote {
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  background: none;
  padding: 0;
  font: italic 400 0.8rem / 1.45 var(--font-serif);
  color: var(--color-text);
  cursor: pointer;
  transition: color 0.15s;
}

.ks-np__quote:hover {
  color: var(--color-primary);
}

.ks-np__q {
  color: var(--color-secondary);
  margin-right: 1px;
}

/* Note content */
.ks-np__content {
  font: 400 0.78rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
}

/* Delete button */
.ks-np__delete {
  position: absolute;
  top: 7px;
  right: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border: none;
  background: none;
  color: transparent;
  cursor: pointer;
  border-radius: 3px;
  transition: color 0.15s, background 0.15s;
}

.ks-np__item:hover .ks-np__delete {
  color: var(--color-secondary);
}

.ks-np__delete:hover {
  color: #f87171 !important;
  background: rgba(248, 113, 113, 0.08);
}
</style>
