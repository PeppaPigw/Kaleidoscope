<script setup lang="ts">
/**
 * Collections — manage paper groups (bookmarked papers).
 */
import { Bookmark, Plus, Trash2, FolderOpen, FileText } from 'lucide-vue-next'

definePageMeta({ layout: 'default' })

useHead({
  title: 'Collections — Kaleidoscope',
  meta: [{ name: 'description', content: 'Manage your bookmarked paper groups.' }],
})

const config = useRuntimeConfig()
const apiBase = config.public.apiUrl as string

interface Group {
  id: string
  name: string
  description: string | null
  paper_count: number
  created_at: string
  updated_at: string | null
}

const groups = ref<Group[]>([])
const loading = ref(true)
const showCreateModal = ref(false)
const newGroupName = ref('')
const newGroupDesc = ref('')
const creating = ref(false)
const deleteTarget = ref<string | null>(null)

function _authHeaders() {
  const token = import.meta.client ? localStorage.getItem('ks_access_token') : null
  if (token && token !== 'single-user-mode') {
    return { Authorization: `Bearer ${token}` }
  }
  return {}
}

onMounted(loadGroups)

async function loadGroups() {
  loading.value = true
  try {
    const data = await $fetch<Group[]>(`${apiBase}/api/v1/collections`, {
      params: { kind: 'paper_group' },
      headers: _authHeaders(),
    })
    groups.value = data
  }
  catch (e) {
    console.error('[collections] load failed', e)
  }
  finally {
    loading.value = false
  }
}

async function createGroup() {
  const name = newGroupName.value.trim()
  if (!name) return
  creating.value = true
  try {
    const created = await $fetch<Group>(`${apiBase}/api/v1/collections`, {
      method: 'POST',
      body: { name, description: newGroupDesc.value.trim() || undefined, kind: 'paper_group' },
      headers: _authHeaders(),
    })
    groups.value.push(created)
    showCreateModal.value = false
    newGroupName.value = ''
    newGroupDesc.value = ''
  }
  catch (e) {
    console.error('[collections] create failed', e)
  }
  finally {
    creating.value = false
  }
}

async function deleteGroup(id: string) {
  deleteTarget.value = id
  try {
    await $fetch(`${apiBase}/api/v1/collections/${id}`, {
      method: 'DELETE',
      headers: _authHeaders(),
    })
    groups.value = groups.value.filter(g => g.id !== id)
  }
  catch (e) {
    console.error('[collections] delete failed', e)
  }
  finally {
    deleteTarget.value = null
  }
}

function formatDate(dt: string) {
  return new Date(dt).toLocaleDateString()
}
</script>

<template>
  <div class="ks-col">
    <!-- Header -->
    <div class="ks-col__header">
      <div class="ks-col__header-text">
        <p class="ks-col__eyebrow">
          <Bookmark :size="12" :stroke-width="2" /> COLLECTIONS
        </p>
        <h1 class="ks-col__title">Paper Groups</h1>
        <p class="ks-col__desc">Organize bookmarked papers into named groups for easy retrieval and AI chat.</p>
      </div>
      <button type="button" class="ks-btn-primary" @click="showCreateModal = true">
        <Plus :size="14" :stroke-width="2.5" /> New Group
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="ks-col__loading">
      Loading collections…
    </div>

    <!-- Empty state -->
    <div v-else-if="groups.length === 0" class="ks-col__empty">
      <FolderOpen :size="40" :stroke-width="1.2" class="ks-col__empty-icon" />
      <p class="ks-col__empty-title">No groups yet</p>
      <p class="ks-col__empty-desc">Save papers from DeepXiv search and reader using the bookmark icon.</p>
      <button type="button" class="ks-btn-primary" @click="showCreateModal = true">
        <Plus :size="14" /> Create your first group
      </button>
    </div>

    <!-- Grid -->
    <div v-else class="ks-col__grid">
      <NuxtLink
        v-for="group in groups"
        :key="group.id"
        :to="`/collections/${group.id}`"
        class="ks-col__card"
      >
        <div class="ks-col__card-icon">
          <Bookmark :size="18" :stroke-width="1.8" />
        </div>
        <div class="ks-col__card-body">
          <h3 class="ks-col__card-name">{{ group.name }}</h3>
          <p v-if="group.description" class="ks-col__card-desc">{{ group.description }}</p>
          <div class="ks-col__card-meta">
            <span class="ks-col__card-count">
              <FileText :size="12" :stroke-width="2" /> {{ group.paper_count }} papers
            </span>
            <span class="ks-col__card-date">{{ formatDate(group.created_at) }}</span>
          </div>
        </div>
        <button
          type="button"
          class="ks-col__card-delete"
          aria-label="Delete group"
          :disabled="deleteTarget === group.id"
          @click.prevent="deleteGroup(group.id)"
        >
          <Trash2 :size="14" :stroke-width="2" />
        </button>
      </NuxtLink>
    </div>

    <!-- Create modal -->
    <Teleport v-if="showCreateModal" to="body">
      <div class="ks-col-modal-overlay" @click.self="showCreateModal = false">
        <div class="ks-col-modal" role="dialog" aria-modal="true" aria-label="Create group">
          <h2 class="ks-col-modal-title">New Paper Group</h2>
          <div class="ks-col-modal-fields">
            <div class="ks-col-modal-field">
              <label class="ks-col-modal-label">Name</label>
              <input
                v-model="newGroupName"
                type="text"
                class="ks-col-modal-input"
                placeholder="e.g. LLM Safety Papers"
                :disabled="creating"
                autofocus
                @keydown.enter="createGroup"
              >
            </div>
            <div class="ks-col-modal-field">
              <label class="ks-col-modal-label">Description (optional)</label>
              <input
                v-model="newGroupDesc"
                type="text"
                class="ks-col-modal-input"
                placeholder="Brief description…"
                :disabled="creating"
              >
            </div>
          </div>
          <div class="ks-col-modal-actions">
            <button type="button" class="ks-btn-ghost" @click="showCreateModal = false">Cancel</button>
            <button type="button" class="ks-btn-primary" :disabled="!newGroupName.trim() || creating" @click="createGroup">
              {{ creating ? 'Creating…' : 'Create' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.ks-col {
  max-width: 900px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.ks-col__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.ks-col__eyebrow {
  display: flex;
  align-items: center;
  gap: 6px;
  font: 700 0.6875rem / 1 var(--font-sans);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-primary);
  margin: 0 0 8px;
}

.ks-col__title {
  font: 700 1.75rem / 1.1 var(--font-display);
  color: var(--color-text);
  margin: 0 0 6px;
  letter-spacing: -0.03em;
}

.ks-col__desc {
  font: 400 0.9rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
}

.ks-col__loading {
  font: 400 0.9rem / 1 var(--font-sans);
  color: var(--color-secondary);
  padding: 40px 0;
  text-align: center;
}

.ks-col__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 40px;
  background: var(--color-surface);
  border: 1px dashed var(--color-border);
  border-radius: 10px;
  text-align: center;
}

.ks-col__empty-icon {
  color: var(--color-secondary);
  opacity: 0.5;
}

.ks-col__empty-title {
  font: 600 1.125rem / 1 var(--font-display);
  color: var(--color-text);
  margin: 0;
}

.ks-col__empty-desc {
  font: 400 0.875rem / 1.5 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
  max-width: 360px;
}

.ks-col__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.ks-col__card {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  text-decoration: none;
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.15s;
}

.ks-col__card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  transform: translateY(-1px);
}

.ks-col__card-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: 8px;
}

.ks-col__card-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ks-col__card-name {
  font: 600 0.9375rem / 1.2 var(--font-display);
  color: var(--color-text);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ks-col__card-desc {
  font: 400 0.8rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ks-col__card-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
}

.ks-col__card-count {
  display: flex;
  align-items: center;
  gap: 4px;
  font: 500 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-col__card-date {
  font: 400 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
  margin-left: auto;
}

.ks-col__card-delete {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  background: none;
  border: none;
  border-radius: 4px;
  color: var(--color-secondary);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s, background-color 0.15s, color 0.15s;
}

.ks-col__card:hover .ks-col__card-delete {
  opacity: 1;
}

.ks-col__card-delete:hover {
  background: rgba(220, 38, 38, 0.08);
  color: #dc2626;
}

/* Modal */
.ks-col-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(10, 10, 10, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.ks-col-modal {
  width: min(100%, 420px);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.16);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ks-col-modal-title {
  font: 700 1.25rem / 1 var(--font-display);
  color: var(--color-text);
  margin: 0;
}

.ks-col-modal-fields {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ks-col-modal-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ks-col-modal-label {
  font: 600 0.75rem / 1 var(--font-sans);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-secondary);
}

.ks-col-modal-input {
  padding: 9px 12px;
  border: 1.5px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg);
  font: 400 0.9rem / 1.4 var(--font-sans);
  color: var(--color-text);
  outline: none;
  transition: border-color 0.15s;
}

.ks-col-modal-input:focus {
  border-color: var(--color-primary);
}

.ks-col-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.ks-btn-ghost {
  padding: 9px 18px;
  background: none;
  border: 1.5px solid var(--color-border);
  border-radius: 6px;
  font: 500 0.875rem / 1 var(--font-sans);
  color: var(--color-text);
  cursor: pointer;
  transition: background-color 0.15s;
}

.ks-btn-ghost:hover {
  background: var(--color-bg);
}

.ks-btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 20px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  font: 600 0.875rem / 1 var(--font-sans);
  cursor: pointer;
  transition: opacity 0.15s;
  white-space: nowrap;
}

.ks-btn-primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
