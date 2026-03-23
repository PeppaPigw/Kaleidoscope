<script setup lang="ts">
/**
 * Knowledge Garden — knowledge.vue
 *
 * Interactive note wall with detail drawer for viewing/editing notes.
 */
import type { NoteCard } from '~/components/knowledge/NoteWall.vue'

definePageMeta({ layout: 'default' })

useHead({
  title: 'Knowledge Garden — Kaleidoscope',
  meta: [{ name: 'description', content: 'Organize research notes, concepts, and learning materials.' }],
})

const notes = ref<NoteCard[]>([
  { id: 'n1', title: 'Atomic Claims vs. Paragraphs', excerpt: 'Key insight: decomposing at the claim level provides finer-grained evidence alignment, but introduces complexity in maintaining coherence across decomposed units. The trade-off between granularity and semantic completeness is central to effective claim extraction pipelines.', tags: ['claims', 'RAG'], backlinkCount: 5, updatedAt: '2h ago' },
  { id: 'n2', title: 'NLI Filtering Pipeline', excerpt: 'NLI (Natural Language Inference) can be used as a post-processing step to filter out claims that are contradicted or not entailed by the original text. This reduces noise by approximately 34% in decomposition pipelines, improving downstream retrieval precision significantly.', tags: ['NLI', 'pipeline'], backlinkCount: 3, updatedAt: '1d ago' },
  { id: 'n3', title: 'BioASQ Benchmark Notes', excerpt: 'BioASQ provides biomedical semantic indexing and question answering data. The Claims extension adds 12K manually annotated atomic claims across 256 biomedical papers. Performance on this benchmark correlates well with downstream RAG quality metrics.', tags: ['benchmark', 'biomedical'], backlinkCount: 7, updatedAt: '3d ago' },
  { id: 'n4', title: 'Cross-Domain Transfer Limitations', excerpt: 'Current models trained on biomedical text show significant performance drops when applied to legal or financial domains. Fine-tuning helps but requires domain-specific claim annotation data that is expensive to produce.', tags: ['transfer', 'limitations'], backlinkCount: 2, updatedAt: '5d ago' },
  { id: 'n5', title: 'Hallucination in RAG Systems', excerpt: 'Claim-level retrieval can reduce hallucination by providing more targeted evidence, but may introduce retrieval noise when claims are decontextualized. A balanced approach uses both paragraph-level and claim-level retrieval.', tags: ['hallucination', 'safety'], backlinkCount: 4, updatedAt: '1w ago' },
  { id: 'n6', title: 'SciBERT Architecture', excerpt: 'SciBERT builds on BERT with pre-training on 1.14M scientific papers from Semantic Scholar, using a domain-specific vocabulary of 30K tokens. It achieves improvements over BERT on scientific NLP tasks including NER, relation extraction, and claim verification.', tags: ['model', 'BERT'], backlinkCount: 6, updatedAt: '2w ago' },
])

const selectedNote = ref<NoteCard | null>(null)
const showDrawer = ref(false)

function handleNoteClick(note: NoteCard) {
  selectedNote.value = note
  showDrawer.value = true
}

function closeDrawer() {
  showDrawer.value = false
  setTimeout(() => { selectedNote.value = null }, 300)
}

function handleDeleteNote(note: NoteCard) {
  notes.value = notes.value.filter(n => n.id !== note.id)
  closeDrawer()
}

// Mock linked notes for detail view
function getLinkedNotes(note: NoteCard): string[] {
  const allTitles = notes.value.filter(n => n.id !== note.id).map(n => n.title)
  return allTitles.slice(0, note.backlinkCount)
}
</script>

<template>
  <div class="ks-knowledge">
    <KsPageHeader title="Knowledge Garden" subtitle="KNOWLEDGE" />

    <div class="ks-knowledge__content">
      <KnowledgeNoteWall :notes="notes" @note-click="handleNoteClick" />
    </div>

    <!-- Note detail drawer -->
    <Teleport to="body">
      <Transition name="ks-slide">
        <div
          v-if="showDrawer && selectedNote"
          class="ks-knowledge__overlay"
          @click.self="closeDrawer"
        >
          <aside class="ks-knowledge__drawer" role="dialog" aria-modal="true" :aria-label="selectedNote.title">
            <div class="ks-knowledge__drawer-header">
              <h2 class="ks-knowledge__drawer-title">{{ selectedNote.title }}</h2>
              <button type="button" class="ks-knowledge__drawer-close" aria-label="Close" @click="closeDrawer">✕</button>
            </div>

            <div class="ks-knowledge__drawer-tags">
              <KsTag v-for="tag in selectedNote.tags" :key="tag" variant="primary">{{ tag }}</KsTag>
            </div>

            <div class="ks-knowledge__drawer-body">
              <p class="ks-knowledge__drawer-text">{{ selectedNote.excerpt }}</p>
            </div>

            <div class="ks-knowledge__drawer-meta">
              <span class="ks-type-data">Last updated: {{ selectedNote.updatedAt }}</span>
              <span class="ks-type-data" style="color: var(--color-primary);">{{ selectedNote.backlinkCount }} backlinks</span>
            </div>

            <!-- Linked notes -->
            <div v-if="getLinkedNotes(selectedNote).length > 0" class="ks-knowledge__drawer-links">
              <h3 class="ks-type-eyebrow" style="color: var(--color-accent); margin-bottom: 8px;">LINKED NOTES</h3>
              <button
                v-for="linked in getLinkedNotes(selectedNote)"
                :key="linked"
                type="button"
                class="ks-knowledge__linked-btn"
                @click="handleNoteClick(notes.find(n => n.title === linked)!)"
              >
                {{ linked }}
              </button>
            </div>

            <!-- Actions -->
            <div class="ks-knowledge__drawer-actions">
              <button type="button" class="ks-knowledge__action-btn ks-knowledge__action-btn--edit" @click="closeDrawer">
                Edit Note
              </button>
              <button type="button" class="ks-knowledge__action-btn ks-knowledge__action-btn--delete" @click="handleDeleteNote(selectedNote)">
                Delete
              </button>
            </div>
          </aside>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.ks-knowledge {
  min-height: 100vh;
  padding-bottom: 80px;
}

.ks-knowledge__content {
  max-width: 1040px;
  margin: 0 auto;
  padding: 0 24px;
}

/* ─── Drawer overlay ─────────────────────────────────────── */
.ks-knowledge__overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  justify-content: flex-end;
  background: rgba(26, 26, 26, 0.2);
  backdrop-filter: blur(2px);
}

.ks-knowledge__drawer {
  width: min(90vw, 480px);
  height: 100%;
  background: var(--color-surface);
  border-left: 1px solid var(--color-border);
  box-shadow: -4px 0 24px rgba(26, 26, 26, 0.08);
  overflow-y: auto;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  animation: slide-in 0.25s var(--ease-smooth) forwards;
}

@keyframes slide-in {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

.ks-knowledge__drawer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.ks-knowledge__drawer-title {
  font: 600 1.375rem / 1.3 var(--font-serif);
  color: var(--color-text);
}

.ks-knowledge__drawer-close {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  color: var(--color-secondary);
  cursor: pointer;
  font-size: 1rem;
  transition: background-color var(--duration-fast) var(--ease-smooth);
}

.ks-knowledge__drawer-close:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.ks-knowledge__drawer-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.ks-knowledge__drawer-body {
  padding: 16px 0;
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

.ks-knowledge__drawer-text {
  font: 400 0.9375rem / 1.7 var(--font-serif);
  color: var(--color-text);
}

.ks-knowledge__drawer-meta {
  display: flex;
  justify-content: space-between;
}

.ks-knowledge__drawer-links {
  padding-top: 8px;
}

.ks-knowledge__linked-btn {
  display: block;
  width: 100%;
  padding: 10px 12px;
  margin-bottom: 4px;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  text-align: left;
  font: 500 0.875rem / 1.3 var(--font-sans);
  color: var(--color-primary);
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-smooth);
}

.ks-knowledge__linked-btn:hover {
  background: var(--color-primary-light);
}

.ks-knowledge__drawer-actions {
  display: flex;
  gap: 10px;
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

.ks-knowledge__action-btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font: 600 0.875rem / 1 var(--font-sans);
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-smooth);
}

.ks-knowledge__action-btn--edit {
  background: var(--color-primary);
  color: #fff;
}

.ks-knowledge__action-btn--edit:hover {
  background: var(--color-primary-dark, #0a8a8e);
}

.ks-knowledge__action-btn--delete {
  background: var(--color-surface);
  color: #dc2626;
  border: 1px solid var(--color-border);
}

.ks-knowledge__action-btn--delete:hover {
  background: rgba(220, 38, 38, 0.06);
}

/* ─── Slide transition ──────────────────────────────────── */
.ks-slide-enter-active {
  transition: opacity 0.2s var(--ease-smooth);
}
.ks-slide-leave-active {
  transition: opacity 0.15s var(--ease-smooth);
}
.ks-slide-enter-from,
.ks-slide-leave-to {
  opacity: 0;
}
</style>

