<script setup lang="ts">
/**
 * Workspaces Listing Page — workspaces/index
 *
 * Shows all research workspaces as interactive cards with progress bars,
 * member counts, and quick-action buttons. Users can create new workspaces
 * or navigate into existing ones.
 */

definePageMeta({ layout: 'default' })

const { t } = useTranslation()

useHead({
  title: 'Workspaces — Kaleidoscope',
  meta: [{ name: 'description', content: 'Manage your research projects, paper collections, and collaboration spaces.' }],
})

interface Workspace {
  id: string
  name: string
  description: string
  paperCount: number
  memberCount: number
  status: 'active' | 'archived' | 'draft'
  progress: number
  lastUpdated: string
  tags: string[]
}

const workspaces = ref<Workspace[]>([
  {
    id: 'ws-1',
    name: 'Claim-Level Scientific NLP',
    description: 'Investigating atomic claim extraction and evidence alignment for biomedical retrieval-augmented generation.',
    paperCount: 5,
    memberCount: 3,
    status: 'active',
    progress: 43,
    lastUpdated: '2 hours ago',
    tags: ['NLP', 'biomedical', 'claims'],
  },
  {
    id: 'ws-2',
    name: 'Clinical Multimodal Reasoning',
    description: 'Survey and benchmark audit of vision-language models for clinical diagnosis workflows.',
    paperCount: 12,
    memberCount: 4,
    status: 'active',
    progress: 68,
    lastUpdated: '1 day ago',
    tags: ['VLM', 'clinical', 'multimodal'],
  },
  {
    id: 'ws-3',
    name: 'Long-Context Benchmark Audit',
    description: 'Systematic evaluation of benchmark contamination and evaluation failure modes in 128K+ context models.',
    paperCount: 8,
    memberCount: 2,
    status: 'active',
    progress: 22,
    lastUpdated: '3 days ago',
    tags: ['benchmark', 'evaluation', 'long-context'],
  },
  {
    id: 'ws-4',
    name: 'Citation-Aware Retrieval Agents',
    description: 'Building research agents that ground outputs in verifiable citations from scientific literature.',
    paperCount: 18,
    memberCount: 5,
    status: 'active',
    progress: 85,
    lastUpdated: '5 hours ago',
    tags: ['RAG', 'agents', 'citations'],
  },
  {
    id: 'ws-5',
    name: 'Previous: Protein Folding Survey',
    description: 'Archived survey of deep learning approaches to protein structure prediction. Published as review.',
    paperCount: 34,
    memberCount: 3,
    status: 'archived',
    progress: 100,
    lastUpdated: '2 months ago',
    tags: ['protein', 'survey', 'completed'],
  },
])

const showCreateModal = ref(false)
const newWsName = ref('')
const newWsDesc = ref('')

const statusOrder: Record<string, number> = { active: 0, draft: 1, archived: 2 }
const sortedWorkspaces = computed(() =>
  [...workspaces.value].sort((a, b) => (statusOrder[a.status] ?? 9) - (statusOrder[b.status] ?? 9))
)

function handleWorkspaceClick(ws: Workspace) {
  navigateTo(`/workspaces/${ws.id}`)
}

function handleCreateWorkspace() {
  if (!newWsName.value.trim()) return
  const newWs: Workspace = {
    id: `ws-${Date.now()}`,
    name: newWsName.value.trim(),
    description: newWsDesc.value.trim() || 'New research workspace',
    paperCount: 0,
    memberCount: 1,
    status: 'draft',
    progress: 0,
    lastUpdated: 'just now',
    tags: [],
  }
  workspaces.value.unshift(newWs)
  newWsName.value = ''
  newWsDesc.value = ''
  showCreateModal.value = false
}

function statusColor(status: string) {
  if (status === 'active') return 'var(--color-primary)'
  if (status === 'archived') return 'var(--color-secondary)'
  return 'var(--color-accent)'
}
</script>

<template>
  <div class="ks-workspaces">
    <KsPageHeader :title="t('workspaces')" :subtitle="t('research')" />

    <div class="ks-workspaces__content">
      <!-- Toolbar -->
      <div class="ks-workspaces__toolbar">
        <p class="ks-type-body-sm" style="color: var(--color-secondary);">
          {{ workspaces.length }} {{ t('workspaces').toLowerCase() }}
        </p>
        <button
          type="button"
          class="ks-workspaces__create-btn"
          @click="showCreateModal = true"
        >
          {{ t('newWorkspace') }}
        </button>
      </div>

      <!-- Workspace cards grid -->
      <div class="ks-workspaces__grid">
        <button
          v-for="ws in sortedWorkspaces"
          :key="ws.id"
          type="button"
          class="ks-card ks-workspaces__card ks-motion-paper-reveal"
          :class="{ 'ks-workspaces__card--archived': ws.status === 'archived' }"
          @click="handleWorkspaceClick(ws)"
        >
          <div class="ks-workspaces__card-header">
            <h3 class="ks-workspaces__card-name">{{ ws.name }}</h3>
            <span
              class="ks-workspaces__card-status"
              :style="{ color: statusColor(ws.status) }"
            >
              {{ ws.status }}
            </span>
          </div>

          <p class="ks-workspaces__card-desc">{{ ws.description }}</p>

          <!-- Progress bar -->
          <div class="ks-workspaces__progress-wrap">
            <div class="ks-workspaces__progress-bar">
              <div
                class="ks-workspaces__progress-fill"
                :style="{ width: `${ws.progress}%` }"
              />
            </div>
            <span class="ks-type-data">{{ ws.progress }}%</span>
          </div>

          <!-- Meta row -->
          <div class="ks-workspaces__card-meta">
            <span class="ks-type-data">{{ ws.paperCount }} {{ t('papers') }}</span>
            <span class="ks-type-data">{{ ws.memberCount }} {{ t('members') }}</span>
            <span class="ks-type-data" style="margin-left: auto;">{{ ws.lastUpdated }}</span>
          </div>

          <!-- Tags -->
          <div class="ks-workspaces__card-tags">
            <KsTag v-for="tag in ws.tags" :key="tag" variant="neutral">{{ tag }}</KsTag>
          </div>
        </button>
      </div>
    </div>

    <!-- Create workspace modal -->
    <Teleport to="body">
      <Transition name="ks-fade">
        <div
          v-if="showCreateModal"
          class="ks-workspaces__overlay"
          @click.self="showCreateModal = false"
        >
          <div class="ks-workspaces__modal ks-motion-paper-reveal" role="dialog" aria-modal="true" :aria-label="t('createNewWorkspace')">
            <h2 class="ks-type-section-title">{{ t('createNewWorkspace') }}</h2>

            <label class="ks-workspaces__field">
              <span class="ks-type-eyebrow">{{ t('name') }}</span>
              <input
                v-model="newWsName"
                type="text"
                class="ks-workspaces__input"
                placeholder="e.g. Clinical Reasoning Review"
                @keydown.enter="handleCreateWorkspace"
              />
            </label>

            <label class="ks-workspaces__field">
              <span class="ks-type-eyebrow">{{ t('description') }}</span>
              <textarea
                v-model="newWsDesc"
                class="ks-workspaces__textarea"
                placeholder="Briefly describe the research focus…"
                rows="3"
              />
            </label>

            <div class="ks-workspaces__modal-actions">
              <button
                type="button"
                class="ks-workspaces__modal-btn ks-workspaces__modal-btn--secondary"
                @click="showCreateModal = false"
              >
                {{ t('cancel') }}
              </button>
              <button
                type="button"
                class="ks-workspaces__modal-btn ks-workspaces__modal-btn--primary"
                :disabled="!newWsName.trim()"
                @click="handleCreateWorkspace"
              >
                {{ t('createBtn') }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.ks-workspaces {
  min-height: 100vh;
  padding-bottom: 80px;
}

.ks-workspaces__content {
  max-width: 1040px;
  margin: 0 auto;
  padding: 0 24px;
}

.ks-workspaces__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.ks-workspaces__create-btn {
  padding: 10px 20px;
  background: var(--color-primary);
  color: var(--color-bg);
  border: none;
  border-radius: 6px;
  font: 600 0.875rem / 1 var(--font-sans);
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-smooth),
              transform var(--duration-fast) var(--ease-smooth);
}

.ks-workspaces__create-btn:hover {
  background: var(--color-primary-dark, #0a8a8e);
  transform: translateY(-1px);
}

.ks-workspaces__create-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-workspaces__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}

.ks-workspaces__card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 24px;
  text-align: left;
  cursor: pointer;
  transition: transform var(--duration-normal) var(--ease-spring),
              box-shadow var(--duration-normal) var(--ease-smooth);
}

.ks-workspaces__card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(26, 26, 26, 0.06);
}

.ks-workspaces__card:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-workspaces__card--archived {
  opacity: 0.6;
}

.ks-workspaces__card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.ks-workspaces__card-name {
  font: 600 1.125rem / 1.3 var(--font-serif);
  color: var(--color-text);
}

.ks-workspaces__card-status {
  font: 600 0.6875rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  flex-shrink: 0;
}

.ks-workspaces__card-desc {
  font: 400 0.8125rem / 1.5 var(--font-serif);
  color: var(--color-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ks-workspaces__progress-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ks-workspaces__progress-bar {
  flex: 1;
  height: 6px;
  background: var(--color-primary-light);
  border-radius: 3px;
  overflow: hidden;
}

.ks-workspaces__progress-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 3px;
  transition: width var(--duration-normal) var(--ease-smooth);
}

.ks-workspaces__card-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-top: 8px;
  border-top: 1px solid var(--color-border);
}

.ks-workspaces__card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* ─── Create Modal ─────────────────────────────────────── */
.ks-workspaces__overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(26, 26, 26, 0.24);
  backdrop-filter: blur(4px);
}

.ks-workspaces__modal {
  width: min(90vw, 480px);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: var(--shadow-float);
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ks-workspaces__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ks-workspaces__input,
.ks-workspaces__textarea {
  padding: 10px 14px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font: 400 0.9375rem / 1.5 var(--font-serif);
  color: var(--color-text);
  transition: border-color var(--duration-fast) var(--ease-smooth);
}

.ks-workspaces__input:focus,
.ks-workspaces__textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
}

.ks-workspaces__textarea {
  resize: vertical;
}

.ks-workspaces__modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 8px;
}

.ks-workspaces__modal-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font: 600 0.875rem / 1 var(--font-sans);
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-smooth),
              opacity var(--duration-fast) var(--ease-smooth);
}

.ks-workspaces__modal-btn--secondary {
  background: var(--color-surface);
  color: var(--color-secondary);
  border: 1px solid var(--color-border);
}

.ks-workspaces__modal-btn--secondary:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.ks-workspaces__modal-btn--primary {
  background: var(--color-primary);
  color: var(--color-bg);
}

.ks-workspaces__modal-btn--primary:hover {
  background: var(--color-primary-dark, #0a8a8e);
}

.ks-workspaces__modal-btn--primary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .ks-workspaces__grid {
    grid-template-columns: 1fr;
  }
}
</style>
