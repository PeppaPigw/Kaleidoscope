<script setup lang="ts">
/**
 * Research Workspace Page — workspaces/[workspaceId]
 */
import type { CorpusPaper } from "~/components/workspace/CorpusShelf.vue";
import type { ProjectCoverProps } from "~/components/workspace/ProjectCover.vue";
import type { Task } from "~/composables/useApi";

definePageMeta({ layout: "default" });

const { t } = useTranslation();

const route = useRoute();
const { apiFetch, listTasks, completeTask } = useApi();
const workspaceId = computed(() => {
  const p = route.params.workspaceId;
  return Array.isArray(p) ? (p[0] ?? "") : (p ?? "");
});

useHead({
  title: "Research Workspace — Kaleidoscope",
  meta: [
    {
      name: "description",
      content: "Organize papers, research questions, and workflows.",
    },
  ],
});

type CollectionData = {
  name?: string;
  description?: string | null;
  kind?: string | null;
  paper_count?: number | null;
  updated_at?: string | null;
};
type CollectionPaper = {
  id?: string;
  paper_id?: string;
  title?: string | null;
  doi?: string | null;
  reading_status?: string | null;
  published_at?: string | null;
  raw_metadata?: { author_names?: string[] } | null;
};

const collection = ref<CollectionData | null>(null);
const papers = ref<CollectionPaper[]>([]);

const mockPapers: CorpusPaper[] = [
  {
    id: "p1",
    title: "ClaimMiner: Atomic Claim Extraction for Biomedical Papers",
    authors: "Liu et al.",
    year: 2025,
    status: "annotated",
  },
  {
    id: "p2",
    title: "Atomic Facts: Decomposing Knowledge for NLI",
    authors: "Min et al.",
    year: 2024,
    status: "read",
  },
  {
    id: "p3",
    title: "SciBERT: A Pretrained Language Model for Scientific Text",
    authors: "Beltagy et al.",
    year: 2019,
    status: "read",
  },
  {
    id: "p4",
    title: "RAGBench-Sci: Failure Modes of Citation-Grounded Retrieval",
    authors: "Jones et al.",
    year: 2025,
    status: "unread",
  },
  {
    id: "p5",
    title: "ContractNLI: Claim Verification for Legal Documents",
    authors: "Koreeda et al.",
    year: 2023,
    status: "unread",
  },
];
const tasks = ref<Task[]>([]);
const isLoadingTasks = ref(true);

const projectCover = computed<ProjectCoverProps>(() => ({
  name: collection.value?.name || "Claim-Level Scientific NLP",
  description:
    collection.value?.description ||
    "Investigating atomic claim extraction and evidence alignment for biomedical retrieval-augmented generation.",
  paperCount: collection.value?.paper_count ?? mockPapers.length,
  memberCount: 1,
  lastUpdated: collection.value?.updated_at
    ? new Date(collection.value.updated_at).toLocaleDateString()
    : "2 hours ago",
  status: "active",
}));

const corpusPapers = computed<CorpusPaper[]>(() =>
  papers.value?.length
    ? papers.value.map((paper, i) => ({
        id: paper.id || paper.paper_id || `paper-${i}`,
        title: paper.title || paper.doi || "Untitled paper",
        authors:
          paper.raw_metadata?.author_names?.join(", ") || "Unknown authors",
        year: paper.published_at
          ? new Date(paper.published_at).getFullYear()
          : new Date().getFullYear(),
        status:
          paper.reading_status === "read"
            ? "read"
            : paper.reading_status === "archived"
              ? "skipped"
              : paper.reading_status === "annotated"
                ? "annotated"
                : "unread",
      }))
    : mockPapers,
);

function handlePaperClick(paper: CorpusPaper) {
  navigateTo(`/papers/${paper.id}`);
}

async function loadTasks() {
  try {
    tasks.value = (await listTasks()).tasks;
  } catch {
    tasks.value = [];
  } finally {
    isLoadingTasks.value = false;
  }
}

async function handleTaskToggle(task: Task) {
  if (task.completed) return;
  await completeTask(task.id);
  task.completed = true;
}

async function loadWorkspace() {
  try {
    collection.value = await apiFetch<CollectionData>(
      `/collections/${workspaceId.value}`,
    );
    if (collection.value?.kind && collection.value.kind !== "workspace") {
      collection.value = null;
      papers.value = [];
      return;
    }
    papers.value = await apiFetch<CollectionPaper[]>(
      `/collections/${workspaceId.value}/papers`,
    );
  } catch {
    collection.value = null;
    papers.value = [];
  }
}

onMounted(() => {
  void loadWorkspace();
  void loadTasks();
});
</script>

<template>
  <div class="ks-workspace">
    <KsPageHeader
      :title="t('workspaces')"
      :subtitle="`WORKSPACE ${workspaceId}`"
    />

    <div class="ks-workspace__content">
      <WorkspaceProjectCover v-bind="projectCover" />

      <WorkspaceCorpusShelf
        :papers="corpusPapers"
        @paper-click="handlePaperClick"
      />

      <section class="ks-card ks-workspace__tasks">
        <span class="ks-type-eyebrow">Collaboration Tasks</span>
        <KsSkeleton v-if="isLoadingTasks" variant="paragraph" :lines="3" />
        <KsEmptyState
          v-else-if="!tasks.length"
          title="No workspace tasks yet"
          description="Review and screening tasks will appear here."
        />
        <ul v-else class="ks-workspace__task-list">
          <li
            v-for="task in tasks"
            :key="task.id"
            class="ks-workspace__task-item"
          >
            <label class="ks-workspace__task-label">
              <input
                :checked="task.completed"
                type="checkbox"
                @change="handleTaskToggle(task)"
              />
              <span>{{ task.title }}</span>
            </label>
          </li>
        </ul>
      </section>

      <section class="ks-card ks-workspace__ask">
        <span class="ks-type-eyebrow">Ask this Workspace</span>
        <RagflowQAPanel
          :collection-id="workspaceId"
          placeholder="Ask a question about the papers in this workspace..."
        />
      </section>
    </div>
  </div>
</template>

<style scoped>
.ks-workspace {
  min-height: 100vh;
  padding-bottom: 80px;
}

.ks-workspace__content {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.ks-workspace__tasks {
  padding: 24px;
  display: grid;
  gap: 16px;
}

.ks-workspace__task-list {
  display: grid;
  gap: 12px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.ks-workspace__task-label {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ks-workspace__ask {
  padding: 24px;
  display: grid;
  gap: 16px;
}
</style>
