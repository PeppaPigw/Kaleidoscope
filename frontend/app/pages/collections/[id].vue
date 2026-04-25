<script setup lang="ts">
/**
 * Collections detail page — view and manage papers in a paper group.
 */
import { ArrowLeft, Trash2, ExternalLink, FolderPlus } from "lucide-vue-next";

definePageMeta({ layout: "default" });

const route = useRoute();
const collectionId = route.params.id as string;

const config = useRuntimeConfig();
const apiBase = config.public.apiUrl as string;

interface Paper {
  paper_id: string;
  title: string;
  abstract: string | null;
  arxiv_id: string | null;
  published_at: string | null;
  added_at: string;
}

interface Collection {
  id: string;
  name: string;
  description: string | null;
  paper_count: number;
}

interface Workspace {
  id: string;
  name: string;
}

const collection = ref<Collection | null>(null);
const papers = ref<Paper[]>([]);
const workspaces = ref<Workspace[]>([]);
const loading = ref(true);
const removingId = ref<string | null>(null);
const showWorkspacePicker = ref(false);
const addingToWorkspace = ref<string | null>(null);
const { resolveLocalPaperRoutes, preferredPaperRoute, openPreferredPaper } =
  usePreferredPaperRoute();

useHead(
  computed(() => ({
    title: collection.value
      ? `${collection.value.name} — Kaleidoscope`
      : "Collection",
  })),
);

function _authHeaders(): Record<string, string> | undefined {
  const token = import.meta.client
    ? localStorage.getItem("ks_access_token")
    : null;
  if (token && token !== "single-user-mode") {
    return { Authorization: `Bearer ${token}` };
  }
  return undefined;
}

onMounted(async () => {
  loading.value = true;
  try {
    const [col, paps, wss] = await Promise.all([
      $fetch<Collection>(`${apiBase}/api/v1/collections/${collectionId}`, {
        headers: _authHeaders(),
      }),
      $fetch<Paper[]>(`${apiBase}/api/v1/collections/${collectionId}/papers`, {
        headers: _authHeaders(),
      }),
      $fetch<Workspace[]>(`${apiBase}/api/v1/collections`, {
        params: { kind: "workspace" },
        headers: _authHeaders(),
      }),
    ]);
    collection.value = col;
    papers.value = paps;
    workspaces.value = wss;
    const arxivIds = paps
      .map((paper) => paper.arxiv_id)
      .filter((id): id is string => Boolean(id));
    await resolveLocalPaperRoutes(arxivIds);
  } catch (e) {
    console.error("[collection detail] load error", e);
  } finally {
    loading.value = false;
  }
});

async function removePaper(paperId: string) {
  removingId.value = paperId;
  try {
    await $fetch(
      `${apiBase}/api/v1/collections/${collectionId}/papers/${paperId}`,
      {
        method: "DELETE",
        headers: _authHeaders(),
      },
    );
    papers.value = papers.value.filter((p) => p.paper_id !== paperId);
    if (collection.value) collection.value.paper_count--;
  } catch (e) {
    console.error("[collection detail] remove paper error", e);
  } finally {
    removingId.value = null;
  }
}

async function addToWorkspace(workspaceId: string) {
  addingToWorkspace.value = workspaceId;
  try {
    const paperIds = papers.value.map((p) => p.paper_id);
    await $fetch(`${apiBase}/api/v1/collections/${workspaceId}/papers`, {
      method: "POST",
      body: { paper_ids: paperIds },
      headers: _authHeaders(),
    });
    showWorkspacePicker.value = false;
  } catch (e) {
    console.error("[collection detail] add to workspace error", e);
  } finally {
    addingToWorkspace.value = null;
  }
}
</script>

<template>
  <div class="ks-col-detail">
    <!-- Back link -->
    <NuxtLink to="/collections" class="ks-col-detail__back">
      <ArrowLeft :size="14" :stroke-width="2" /> All Collections
    </NuxtLink>

    <div v-if="loading" class="ks-col-detail__loading">Loading…</div>

    <template v-else-if="collection">
      <!-- Header -->
      <div class="ks-col-detail__header">
        <div class="ks-col-detail__header-text">
          <h1 class="ks-col-detail__title">{{ collection.name }}</h1>
          <p v-if="collection.description" class="ks-col-detail__desc">
            {{ collection.description }}
          </p>
          <p class="ks-col-detail__count">
            {{ collection.paper_count }} papers
          </p>
        </div>
        <div class="ks-col-detail__actions">
          <button
            type="button"
            class="ks-btn-outline"
            @click="showWorkspacePicker = !showWorkspacePicker"
          >
            <FolderPlus :size="14" :stroke-width="2" />
            Add to Workspace
          </button>
        </div>
      </div>

      <!-- Workspace picker dropdown -->
      <div v-if="showWorkspacePicker" class="ks-col-detail__ws-picker">
        <p class="ks-col-detail__ws-label">
          Select a workspace to add all papers:
        </p>
        <div v-if="workspaces.length === 0" class="ks-col-detail__ws-empty">
          No workspaces found. Create one at /workspaces.
        </div>
        <button
          v-for="ws in workspaces"
          :key="ws.id"
          type="button"
          class="ks-col-detail__ws-item"
          :disabled="addingToWorkspace === ws.id"
          @click="addToWorkspace(ws.id)"
        >
          {{ ws.name }}
          <span v-if="addingToWorkspace === ws.id">…</span>
        </button>
      </div>

      <!-- Paper list -->
      <div v-if="papers.length === 0" class="ks-col-detail__empty">
        No papers in this group yet. Bookmark papers from DeepXiv search or
        reader.
      </div>

      <div v-else class="ks-col-detail__papers">
        <div
          v-for="paper in papers"
          :key="paper.paper_id"
          class="ks-col-detail__paper"
        >
          <div class="ks-col-detail__paper-body">
            <h3 class="ks-col-detail__paper-title">{{ paper.title }}</h3>
            <p v-if="paper.abstract" class="ks-col-detail__paper-abstract">
              {{ paper.abstract.slice(0, 200)
              }}{{ paper.abstract.length > 200 ? "…" : "" }}
            </p>
            <div class="ks-col-detail__paper-meta">
              <span v-if="paper.arxiv_id" class="ks-col-detail__paper-id">{{
                paper.arxiv_id
              }}</span>
              <span v-if="paper.published_at" class="ks-col-detail__paper-date">
                {{ new Date(paper.published_at).getFullYear() }}
              </span>
            </div>
          </div>
          <div class="ks-col-detail__paper-actions">
            <NuxtLink
              v-if="paper.arxiv_id"
              :to="preferredPaperRoute(paper.arxiv_id)"
              class="ks-col-detail__paper-btn"
              :aria-label="`Open paper ${paper.title}`"
              @click.prevent="openPreferredPaper(paper.arxiv_id)"
            >
              <ExternalLink :size="14" :stroke-width="2" />
            </NuxtLink>
            <button
              type="button"
              class="ks-col-detail__paper-btn ks-col-detail__paper-btn--danger"
              :disabled="removingId === paper.paper_id"
              :aria-label="`Remove ${paper.title}`"
              @click="removePaper(paper.paper_id)"
            >
              <Trash2 :size="14" :stroke-width="2" />
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.ks-col-detail {
  max-width: 760px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.ks-col-detail__back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font: 500 0.8125rem / 1 var(--font-sans);
  color: var(--color-secondary);
  text-decoration: none;
  transition: color 0.15s;
}

.ks-col-detail__back:hover {
  color: var(--color-primary);
}

.ks-col-detail__loading {
  font: 400 0.9rem / 1 var(--font-sans);
  color: var(--color-secondary);
  padding: 40px 0;
}

.ks-col-detail__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.ks-col-detail__title {
  font: 700 1.75rem / 1.1 var(--font-display);
  color: var(--color-text);
  margin: 0 0 4px;
  letter-spacing: -0.03em;
}

.ks-col-detail__desc {
  font: 400 0.9rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  margin: 0 0 6px;
}

.ks-col-detail__count {
  font: 500 0.8125rem / 1 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
}

.ks-col-detail__actions {
  flex-shrink: 0;
}

.ks-btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 16px;
  border: 1.5px solid var(--color-border);
  border-radius: 6px;
  background: none;
  font: 500 0.875rem / 1 var(--font-sans);
  color: var(--color-text);
  cursor: pointer;
  transition:
    border-color 0.15s,
    color 0.15s;
  white-space: nowrap;
}

.ks-btn-outline:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* Workspace picker */
.ks-col-detail__ws-picker {
  padding: 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ks-col-detail__ws-label {
  font: 500 0.8125rem / 1 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
}

.ks-col-detail__ws-empty {
  font: 400 0.8125rem / 1 var(--font-sans);
  color: var(--color-secondary);
  font-style: italic;
}

.ks-col-detail__ws-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font: 500 0.875rem / 1 var(--font-sans);
  color: var(--color-text);
  cursor: pointer;
  transition:
    border-color 0.15s,
    background-color 0.15s;
  text-align: left;
}

.ks-col-detail__ws-item:hover:not(:disabled) {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
  color: var(--color-primary);
}

/* Empty state */
.ks-col-detail__empty {
  padding: 40px;
  text-align: center;
  font: 400 0.9rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  background: var(--color-surface);
  border: 1px dashed var(--color-border);
  border-radius: 8px;
  font-style: italic;
}

/* Papers list */
.ks-col-detail__papers {
  display: flex;
  flex-direction: column;
  gap: 0;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
}

.ks-col-detail__paper {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-border);
  transition: background-color 0.12s;
}

.ks-col-detail__paper:last-child {
  border-bottom: none;
}

.ks-col-detail__paper:hover {
  background: var(--color-bg);
}

.ks-col-detail__paper-body {
  flex: 1;
  min-width: 0;
}

.ks-col-detail__paper-title {
  font: 600 0.9375rem / 1.3 var(--font-display);
  color: var(--color-text);
  margin: 0 0 4px;
}

.ks-col-detail__paper-abstract {
  font: 400 0.8125rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  margin: 0 0 6px;
}

.ks-col-detail__paper-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ks-col-detail__paper-id {
  font: 500 0.75rem / 1 var(--font-mono);
  color: var(--color-primary);
}

.ks-col-detail__paper-date {
  font: 400 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-col-detail__paper-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.ks-col-detail__paper-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 5px;
  color: var(--color-secondary);
  text-decoration: none;
  cursor: pointer;
  transition:
    background-color 0.15s,
    color 0.15s,
    border-color 0.15s;
}

.ks-col-detail__paper-btn:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.ks-col-detail__paper-btn--danger:hover {
  background: rgba(220, 38, 38, 0.06);
  color: #dc2626;
  border-color: rgba(220, 38, 38, 0.3);
}
</style>
