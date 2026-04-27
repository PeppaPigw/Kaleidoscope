<script setup lang="ts">
import type { WritingDocument } from "~/composables/useApi";
import type { RenderedMarkdownHeading } from "~/utils/markdown";
import {
  BookText,
  FilePlus2,
  Files,
  ListTree,
  NotebookPen,
  RefreshCw,
  Trash2,
} from "lucide-vue-next";
import {
  buildWritingExcerpt,
  countMarkdownWords,
  sortWritingDocumentsByUpdatedAt,
} from "~/utils/writing";

definePageMeta({ layout: "default" });

useHead({
  title: "Writing Studio — Kaleidoscope",
  meta: [
    {
      name: "description",
      content:
        "Write rich documents with Tiptap while persisting canonical Markdown and uploaded image URLs.",
    },
  ],
});

const {
  listWritingDocuments,
  createWritingDocument,
  getWritingDocument,
  updateWritingDocument,
  deleteWritingDocument,
  uploadWritingImage,
} = useApi();

const documents = ref<WritingDocument[]>([]);
const selectedDocumentId = ref<string | null>(null);
const draftTitle = ref("");
const draftMarkdown = ref("");
const editorWordCount = ref(0);
const pagePending = ref(true);
const documentPending = ref(false);
const createPending = ref(false);
const deletePending = ref(false);
const pageError = ref<string | null>(null);
const saveError = ref<string | null>(null);
const saveState = ref<"idle" | "saving" | "saved" | "error">("idle");
const lastSavedAt = ref<string | null>(null);
const hydratingDraft = ref(false);
const rightRailMode = ref<"outline" | "preview">("outline");
const outlineSections = ref<RenderedMarkdownHeading[]>([]);
const activeOutlineSectionId = ref<string | null>(null);

const persistedTitle = ref("");
const persistedMarkdown = ref("");
const writingEditorRef = ref<{
  scrollToHeading: (headingId: string) => void;
} | null>(null);

let saveTimer: ReturnType<typeof setTimeout> | null = null;
let activeSavePromise: Promise<boolean> | null = null;

const sortedDocuments = computed(() =>
  sortWritingDocumentsByUpdatedAt(documents.value),
);
const selectedDocument = computed(
  () =>
    documents.value.find(
      (document) => document.id === selectedDocumentId.value,
    ) ?? null,
);
const currentWordCount = computed(() =>
  Math.max(editorWordCount.value, countMarkdownWords(draftMarkdown.value)),
);
const formulaCount = computed(() => {
  const blockCount = (draftMarkdown.value.match(/\$\$/g) || []).length / 2;
  const inlineCount =
    (draftMarkdown.value.match(/(?<!\$)\$(?!\$)/g) || []).length / 2;
  return blockCount + inlineCount;
});
const hasDirtyChanges = computed(() =>
  Boolean(
    selectedDocumentId.value &&
    (draftTitle.value !== persistedTitle.value ||
      draftMarkdown.value !== persistedMarkdown.value),
  ),
);
const saveLabel = computed(() => {
  if (saveState.value === "saving") return "Saving";
  if (saveState.value === "saved") return "Saved";
  if (saveState.value === "error") return "Save failed";
  return "Ready";
});
const editorDisabled = computed(
  () => pagePending.value || documentPending.value || !selectedDocumentId.value,
);
const headerMeta = computed(() => {
  const parts = [
    `${sortedDocuments.value.length} ${sortedDocuments.value.length === 1 ? "document" : "documents"}`,
    `${currentWordCount.value} words`,
    saveLabel.value,
  ];
  return parts.join(" · ");
});

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;

  return "The writing studio request failed.";
}

function formatTimestamp(value?: string | null): string {
  if (!value) return "Not saved yet";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Not saved yet";

  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function clearSaveTimer() {
  if (saveTimer !== null) {
    clearTimeout(saveTimer);
    saveTimer = null;
  }
}

function upsertDocument(document: WritingDocument) {
  const next = documents.value.some((entry) => entry.id === document.id)
    ? documents.value.map((entry) =>
        entry.id === document.id ? document : entry,
      )
    : [document, ...documents.value];

  documents.value = sortWritingDocumentsByUpdatedAt(next);
}

function setDraftFromDocument(document: WritingDocument) {
  hydratingDraft.value = true;
  selectedDocumentId.value = document.id;
  draftTitle.value = document.title;
  draftMarkdown.value = document.markdown_content;
  editorWordCount.value =
    document.word_count || countMarkdownWords(document.markdown_content);
  persistedTitle.value = document.title;
  persistedMarkdown.value = document.markdown_content;
  lastSavedAt.value = document.updated_at ?? document.created_at;
  saveError.value = null;
  saveState.value = "saved";

  nextTick(() => {
    hydratingDraft.value = false;
  });
}

function optimisticallyUpdateSelectedDocument() {
  if (!selectedDocumentId.value) return;

  const optimisticUpdatedAt = new Date().toISOString();
  const optimisticTitle = draftTitle.value.trim() || "Untitled";
  const optimisticWordCount = countMarkdownWords(draftMarkdown.value);

  documents.value = sortWritingDocumentsByUpdatedAt(
    documents.value.map((document) => {
      if (document.id !== selectedDocumentId.value) return document;

      return {
        ...document,
        title: optimisticTitle,
        markdown_content: draftMarkdown.value,
        plain_text_excerpt: buildWritingExcerpt(draftMarkdown.value),
        word_count: optimisticWordCount,
        updated_at: optimisticUpdatedAt,
      };
    }),
  );
}

async function persistActiveDocument(): Promise<boolean> {
  if (!selectedDocumentId.value) return true;

  if (!hasDirtyChanges.value) {
    if (saveState.value === "saving") saveState.value = "saved";
    return true;
  }

  if (activeSavePromise) return activeSavePromise;

  const documentId = selectedDocumentId.value;
  const titleToSave = draftTitle.value.trim() || "Untitled";
  const markdownToSave = draftMarkdown.value;

  activeSavePromise = (async () => {
    try {
      const saved = await updateWritingDocument(documentId, {
        title: titleToSave,
        markdown_content: markdownToSave,
      });

      upsertDocument(saved);

      if (selectedDocumentId.value === documentId) {
        persistedTitle.value = saved.title;
        persistedMarkdown.value = saved.markdown_content;
        lastSavedAt.value = saved.updated_at ?? saved.created_at;

        if (!draftTitle.value.trim()) draftTitle.value = saved.title;

        if (
          draftTitle.value === persistedTitle.value &&
          draftMarkdown.value === persistedMarkdown.value
        ) {
          saveState.value = "saved";
          saveError.value = null;
        } else {
          saveState.value = "saving";
          scheduleSave();
        }
      }

      return true;
    } catch (error) {
      saveState.value = "error";
      saveError.value = getErrorMessage(error);
      return false;
    } finally {
      activeSavePromise = null;
    }
  })();

  return activeSavePromise;
}

function scheduleSave() {
  if (hydratingDraft.value || !selectedDocumentId.value) return;

  clearSaveTimer();
  saveState.value = "saving";
  saveError.value = null;
  saveTimer = window.setTimeout(() => {
    saveTimer = null;
    void persistActiveDocument();
  }, 1200);
}

async function flushScheduledSave(): Promise<boolean> {
  clearSaveTimer();
  return persistActiveDocument();
}

async function openDocument(documentId: string) {
  if (selectedDocumentId.value && selectedDocumentId.value !== documentId) {
    const saved = await flushScheduledSave();
    if (!saved) return;
  }

  const optimisticDocument = documents.value.find(
    (document) => document.id === documentId,
  );
  if (optimisticDocument) setDraftFromDocument(optimisticDocument);

  documentPending.value = true;
  pageError.value = null;

  try {
    const document = await getWritingDocument(documentId);
    upsertDocument(document);
    setDraftFromDocument(document);
  } catch (error) {
    if (!optimisticDocument) pageError.value = getErrorMessage(error);
  } finally {
    documentPending.value = false;
  }
}

async function createAndOpenDocument() {
  if (selectedDocumentId.value) {
    const saved = await flushScheduledSave();
    if (!saved) return;
  }

  createPending.value = true;
  pageError.value = null;

  try {
    const document = await createWritingDocument();
    upsertDocument(document);
    setDraftFromDocument(document);
  } catch (error) {
    pageError.value = getErrorMessage(error);
  } finally {
    createPending.value = false;
  }
}

async function removeDocument(documentId: string) {
  const target = documents.value.find((document) => document.id === documentId);
  if (!target) return;

  const confirmed = window.confirm(
    `Delete "${target.title}"? This removes the saved draft.`,
  );
  if (!confirmed) return;

  clearSaveTimer();
  deletePending.value = true;
  pageError.value = null;

  try {
    await deleteWritingDocument(documentId);
    documents.value = documents.value.filter(
      (document) => document.id !== documentId,
    );

    if (selectedDocumentId.value === documentId) {
      selectedDocumentId.value = null;
      draftTitle.value = "";
      draftMarkdown.value = "";
      editorWordCount.value = 0;
      persistedTitle.value = "";
      persistedMarkdown.value = "";
      lastSavedAt.value = null;
      saveState.value = "idle";
      saveError.value = null;

      if (documents.value.length > 0)
        await openDocument(documents.value[0]!.id);
      else await createAndOpenDocument();
    }
  } catch (error) {
    pageError.value = getErrorMessage(error);
  } finally {
    deletePending.value = false;
  }
}

async function handleUploadImage(file: File) {
  return uploadWritingImage(file);
}

async function initializeStudio() {
  pagePending.value = true;
  pageError.value = null;

  try {
    const response = await listWritingDocuments();
    documents.value = sortWritingDocumentsByUpdatedAt(response.items);

    if (documents.value.length === 0) await createAndOpenDocument();
    else await openDocument(documents.value[0]!.id);
  } catch (error) {
    pageError.value = getErrorMessage(error);
  } finally {
    pagePending.value = false;
  }
}

async function reloadStudio() {
  if (selectedDocumentId.value) {
    const saved = await flushScheduledSave();
    if (!saved) return;
  }

  await initializeStudio();
}

function handleBeforeUnload(event: BeforeUnloadEvent) {
  if (!hasDirtyChanges.value) return;

  event.preventDefault();
  event.returnValue = "";
}

function focusOutlineSection(section: RenderedMarkdownHeading) {
  writingEditorRef.value?.scrollToHeading(section.id);
}

watch([draftTitle, draftMarkdown], () => {
  if (hydratingDraft.value || !selectedDocumentId.value) return;

  optimisticallyUpdateSelectedDocument();

  if (hasDirtyChanges.value) scheduleSave();
  else if (saveState.value !== "error") saveState.value = "saved";
});

onMounted(() => {
  window.addEventListener("beforeunload", handleBeforeUnload);
  void initializeStudio();
});

onBeforeUnmount(() => {
  clearSaveTimer();
  window.removeEventListener("beforeunload", handleBeforeUnload);
  void persistActiveDocument();
});
</script>

<template>
  <div class="ks-writing-studio">
    <div class="ks-writing-studio__frame">
      <KsPageHeader
        class="ks-writing-studio__header"
        title="Writing Studio"
        section="Workspace"
      >
        <template #meta>
          {{ headerMeta }}
        </template>
        <template #actions>
          <KsButton
            size="sm"
            variant="secondary"
            :loading="createPending"
            @click="createAndOpenDocument"
          >
            <template #icon-left>
              <FilePlus2 :size="14" />
            </template>
            New document
          </KsButton>
          <KsButton
            size="sm"
            variant="ghost"
            :disabled="!selectedDocument || deletePending"
            :loading="deletePending"
            @click="selectedDocument && removeDocument(selectedDocument.id)"
          >
            <template #icon-left>
              <Trash2 :size="14" />
            </template>
            Delete
          </KsButton>
        </template>
      </KsPageHeader>

      <div class="ks-writing-studio__shell">
        <aside class="ks-writing-studio__rail">
          <div class="ks-writing-studio__rail-head">
            <div>
              <p class="ks-writing-studio__eyebrow">Draft shelf</p>
              <h2 class="ks-writing-studio__rail-title">Titles only</h2>
            </div>
            <button
              type="button"
              class="ks-writing-studio__refresh"
              aria-label="Reload documents"
              @click="reloadStudio"
            >
              <RefreshCw :size="16" />
            </button>
          </div>

          <div
            v-if="pagePending && documents.length === 0"
            class="ks-writing-studio__rail-loading"
          >
            <KsSkeleton height="88px" />
            <KsSkeleton height="88px" />
            <KsSkeleton height="88px" />
          </div>

          <KsErrorAlert
            v-else-if="pageError && documents.length === 0"
            :message="pageError"
          />

          <div v-else class="ks-writing-studio__document-list">
            <button
              v-for="document in sortedDocuments"
              :key="document.id"
              :data-testid="`writing-document-item-${document.id}`"
              type="button"
              class="ks-writing-studio__document-item"
              :class="{ 'is-active': document.id === selectedDocumentId }"
              @click="openDocument(document.id)"
            >
              <p class="ks-writing-studio__document-title">
                {{ document.title }}
              </p>
            </button>
          </div>
        </aside>

        <main class="ks-writing-studio__workspace">
          <div class="ks-writing-studio__lead">
            <label class="ks-writing-studio__title-field">
              <span class="ks-writing-studio__title-label">Document title</span>
              <input
                v-model="draftTitle"
                aria-label="Document title"
                class="ks-writing-studio__title-input"
                type="text"
                placeholder="Untitled"
              >
            </label>

            <div class="ks-writing-studio__lead-meta">
              <span class="ks-writing-studio__lead-chip">
                <NotebookPen :size="14" />
                Canonical Markdown
              </span>
              <span class="ks-writing-studio__lead-chip">
                <Files :size="14" />
                {{ currentWordCount }} words
              </span>
              <span class="ks-writing-studio__lead-chip">
                <RefreshCw :size="14" />
                {{ saveLabel }}
              </span>
            </div>
          </div>

          <KsErrorAlert
            v-if="pageError && documents.length > 0"
            :message="pageError"
          />

          <WritingMarkdownEditor
            ref="writingEditorRef"
            v-model="draftMarkdown"
            :disabled="editorDisabled"
            :save-label="saveLabel"
            :upload-image="handleUploadImage"
            @word-count-change="editorWordCount = $event"
            @outline-change="outlineSections = $event"
            @active-heading-change="activeOutlineSectionId = $event"
          />

          <p v-if="saveError" class="ks-writing-studio__save-error">
            {{ saveError }}
          </p>
        </main>

        <aside class="ks-writing-studio__preview-stack">
          <section class="ks-writing-studio__status-card">
            <div class="ks-writing-studio__status-head">
              <div>
                <p class="ks-writing-studio__eyebrow">Inspector</p>
                <h2 class="ks-writing-studio__status-title">
                  {{ draftTitle || "Untitled" }}
                </h2>
                <p class="ks-writing-studio__status-meta">
                  {{ formatTimestamp(lastSavedAt) }}
                </p>
              </div>
              <span
                class="ks-writing-studio__status-pill"
                :class="`is-${saveState}`"
              >
                {{ saveLabel }}
              </span>
            </div>

            <dl class="ks-writing-studio__status-grid">
              <div>
                <dt>Words</dt>
                <dd>{{ currentWordCount }}</dd>
              </div>
              <div>
                <dt>Last saved</dt>
                <dd>{{ formatTimestamp(lastSavedAt) }}</dd>
              </div>
              <div>
                <dt>Images</dt>
                <dd>{{ (draftMarkdown.match(/!\[/g) || []).length }}</dd>
              </div>
              <div>
                <dt>Formulas</dt>
                <dd>{{ formulaCount }}</dd>
              </div>
            </dl>

            <div
              class="ks-writing-studio__panel-switcher"
              role="tablist"
              aria-label="Writing side panel mode"
            >
              <button
                type="button"
                class="ks-writing-studio__panel-tab"
                :class="{ 'is-active': rightRailMode === 'outline' }"
                :aria-selected="rightRailMode === 'outline'"
                data-testid="writing-sidepanel-outline"
                @click="rightRailMode = 'outline'"
              >
                <ListTree :size="15" />
                Outline
              </button>
              <button
                type="button"
                class="ks-writing-studio__panel-tab"
                :class="{ 'is-active': rightRailMode === 'preview' }"
                :aria-selected="rightRailMode === 'preview'"
                data-testid="writing-sidepanel-preview"
                @click="rightRailMode = 'preview'"
              >
                <BookText :size="15" />
                Preview
              </button>
            </div>

            <div class="ks-writing-studio__panel-body">
              <WritingOutlinePane
                v-if="rightRailMode === 'outline'"
                :sections="outlineSections"
                :active-section-id="activeOutlineSectionId"
                @section-click="focusOutlineSection"
              />
              <WritingPreviewPane
                v-else
                :title="draftTitle || 'Untitled'"
                :markdown="draftMarkdown"
              />
            </div>
          </section>
        </aside>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ks-writing-studio {
  min-height: 100dvh;
  padding-bottom: 0.75rem;
  background:
    radial-gradient(
      circle at top left,
      rgba(196, 163, 90, 0.08),
      transparent 20rem
    ),
    radial-gradient(
      circle at top right,
      rgba(13, 115, 119, 0.08),
      transparent 26rem
    ),
    linear-gradient(180deg, #f8f7f3 0%, #f2efe7 100%);
}

.ks-writing-studio__frame {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 1600px;
  margin: 0 auto;
  padding: 0 1.25rem;
}

.ks-writing-studio__header {
  background: transparent;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}

.ks-writing-studio__shell {
  display: grid;
  grid-template-columns: minmax(12.5rem, 14rem) minmax(0, 1fr) minmax(
      19rem,
      21rem
    );
  gap: 1.25rem;
  min-height: calc(100dvh - 12.5rem);
  align-items: stretch;
}

.ks-writing-studio__rail,
.ks-writing-studio__preview-stack {
  position: sticky;
  top: 5.5rem;
  align-self: start;
  min-height: calc(100dvh - 6.25rem);
  max-height: calc(100dvh - 6.25rem);
}

.ks-writing-studio__rail {
  display: flex;
  flex-direction: column;
  padding: 1rem;
  border: 1px solid rgba(232, 229, 224, 0.94);
  border-radius: var(--radius-lg);
  background:
    linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.95),
      rgba(249, 247, 242, 0.94)
    ),
    radial-gradient(circle at top, rgba(196, 163, 90, 0.08), transparent 30%);
  box-shadow: var(--shadow-card);
}

.ks-writing-studio__rail-head,
.ks-writing-studio__status-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.9rem;
}

.ks-writing-studio__eyebrow {
  margin: 0 0 0.3rem;
  font: 700 0.7rem / 1.1 var(--font-sans);
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.ks-writing-studio__rail-title,
.ks-writing-studio__status-title {
  margin: 0;
  font: 700 1.16rem / 1.2 var(--font-display);
  color: var(--color-text);
}

.ks-writing-studio__refresh {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.2rem;
  height: 2.2rem;
  border: 1px solid rgba(232, 229, 224, 0.92);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--color-secondary);
  cursor: pointer;
}

.ks-writing-studio__rail-loading,
.ks-writing-studio__document-list {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  margin-top: 1rem;
}

.ks-writing-studio__preview-stack {
  display: flex;
  flex-direction: column;
}

.ks-writing-studio__document-list {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding-top: 0.375rem;
}

.ks-writing-studio__document-item {
  display: block;
  width: 100%;
  padding: 0.82rem 0.9rem;
  border: 1px solid rgba(232, 229, 224, 0.92);
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.76);
  text-align: left;
  cursor: pointer;
  transition:
    transform var(--duration-fast) var(--ease-smooth),
    border-color var(--duration-fast) var(--ease-smooth),
    background-color var(--duration-fast) var(--ease-smooth);
}

.ks-writing-studio__document-item:hover,
.ks-writing-studio__document-item.is-active {
  transform: translateY(-1px);
  border-color: rgba(13, 115, 119, 0.34);
  background: rgba(13, 115, 119, 0.08);
}

.ks-writing-studio__document-title {
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font: 700 0.92rem / 1.3 var(--font-sans);
  color: var(--color-text);
}

.ks-writing-studio__workspace {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 0;
  min-height: calc(100dvh - 6.25rem);
}

.ks-writing-studio__lead {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.1rem 0;
}

.ks-writing-studio__title-field {
  display: grid;
  gap: 0.45rem;
  flex: 1;
  min-width: 0;
}

.ks-writing-studio__title-label {
  font: 700 0.72rem / 1.1 var(--font-sans);
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--color-secondary);
}

.ks-writing-studio__title-input {
  width: 100%;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--color-text);
  font: 700 clamp(2rem, 2.6vw, 3rem) / 1.02 var(--font-display);
  outline: none;
}

.ks-writing-studio__title-input::placeholder {
  color: rgba(73, 69, 63, 0.42);
}

.ks-writing-studio__lead-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.5rem;
}

.ks-writing-studio__lead-chip,
.ks-writing-studio__status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.55rem 0.8rem;
  border-radius: 999px;
  font: 700 0.73rem / 1.1 var(--font-sans);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.ks-writing-studio__lead-chip {
  background: rgba(255, 255, 255, 0.78);
  color: var(--color-secondary);
  border: 1px solid rgba(232, 229, 224, 0.92);
}

.ks-writing-studio__status-card {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
  padding: 1rem;
  border: 1px solid rgba(232, 229, 224, 0.94);
  border-radius: var(--radius-lg);
  background:
    linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.95),
      rgba(247, 244, 237, 0.95)
    ),
    radial-gradient(
      circle at top right,
      rgba(196, 163, 90, 0.08),
      transparent 32%
    );
  box-shadow: var(--shadow-card);
}

.ks-writing-studio__status-meta {
  margin: 0.28rem 0 0;
  color: var(--color-secondary);
  font: 500 0.82rem / 1.4 var(--font-serif);
}

.ks-writing-studio__status-pill {
  background: rgba(13, 115, 119, 0.1);
  color: var(--color-primary);
}

.ks-writing-studio__status-pill.is-saving {
  background: rgba(196, 163, 90, 0.16);
  color: #7d5a00;
}

.ks-writing-studio__status-pill.is-error {
  background: rgba(139, 58, 24, 0.12);
  color: #8b3a18;
}

.ks-writing-studio__status-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.9rem;
  margin: 1rem 0 0;
}

.ks-writing-studio__status-grid dt {
  margin: 0 0 0.25rem;
  font: 700 0.7rem / 1.1 var(--font-sans);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-secondary);
}

.ks-writing-studio__status-grid dd {
  margin: 0;
  font: 600 0.98rem / 1.3 var(--font-sans);
  color: var(--color-text);
}

.ks-writing-studio__panel-switcher {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.45rem;
  margin-top: 1rem;
  padding: 0.25rem;
  border-radius: 999px;
  background: rgba(247, 243, 235, 0.9);
}

.ks-writing-studio__panel-tab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  width: 100%;
  padding: 0.6rem 0.75rem;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--color-secondary);
  cursor: pointer;
  font: 700 0.74rem / 1.1 var(--font-sans);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  transition:
    background-color var(--duration-fast) var(--ease-smooth),
    color var(--duration-fast) var(--ease-smooth);
}

.ks-writing-studio__panel-tab.is-active {
  background: rgba(255, 255, 255, 0.96);
  color: var(--color-text);
  box-shadow: 0 2px 8px rgba(76, 67, 52, 0.08);
}

.ks-writing-studio__panel-body {
  flex: 1;
  min-height: 0;
  margin-top: 0.85rem;
  overflow: hidden;
}

.ks-writing-studio__save-error {
  margin: 0;
  padding: 0 0.2rem;
  color: #8b3a18;
  font: 600 0.88rem / 1.5 var(--font-sans);
}

@media (max-width: 1280px) {
  .ks-writing-studio__shell {
    grid-template-columns: minmax(12rem, 13.5rem) minmax(0, 1fr);
  }

  .ks-writing-studio__preview-stack {
    position: static;
    grid-column: 1 / -1;
    min-height: auto;
    max-height: none;
  }
}

@media (max-width: 900px) {
  .ks-writing-studio__frame {
    padding: 0 0.85rem;
  }

  .ks-writing-studio__shell {
    grid-template-columns: 1fr;
  }

  .ks-writing-studio__rail {
    position: static;
    min-height: auto;
    max-height: none;
  }

  .ks-writing-studio__lead {
    flex-direction: column;
    align-items: stretch;
    padding: 0.4rem 0.2rem 0;
  }

  .ks-writing-studio__lead-meta {
    justify-content: flex-start;
  }

  .ks-writing-studio__title-input {
    font-size: 2.15rem;
  }
}
</style>
