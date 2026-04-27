<script setup lang="ts">
/**
 * GroupPickerModal — choose a paper_group collection to save a paper to.
 * Opens as a teleport overlay. Fetches user's groups from the API.
 */
import { X, Plus, Check, Bookmark } from "lucide-vue-next";
import { withKaleidoscopeAuthHeaders } from "~/utils/apiKey";

const props = defineProps<{
  arxivId: string;
  title: string;
}>();

const emit = defineEmits<{ close: []; saved: [groupId: string] }>();

const config = useRuntimeConfig();
const apiBase = config.public.apiUrl as string;

interface Group {
  id: string;
  name: string;
  paper_count: number;
}

const groups = ref<Group[]>([]);
const loadingGroups = ref(true);
const saving = ref<string | null>(null); // collection_id being saved
const savedSet = ref<Set<string>>(new Set());
const showNewGroupForm = ref(false);
const newGroupName = ref("");
const creatingGroup = ref(false);

function _authHeaders(): Record<string, string> {
  return withKaleidoscopeAuthHeaders();
}

onMounted(async () => {
  await loadGroups();
});

async function loadGroups() {
  loadingGroups.value = true;
  try {
    const data = await $fetch<Group[]>(`${apiBase}/api/v1/collections`, {
      params: { kind: "paper_group" },
      headers: _authHeaders(),
    });
    groups.value = data;
  } catch (e) {
    console.error("[GroupPickerModal] failed to load groups", e);
  } finally {
    loadingGroups.value = false;
  }
}

async function handleSelect(groupId: string) {
  if (savedSet.value.has(groupId) || saving.value === groupId) return;
  saving.value = groupId;
  try {
    await $fetch(`${apiBase}/api/v1/deepxiv/papers/${props.arxivId}/bookmark`, {
      method: "POST",
      body: { collection_id: groupId },
      headers: _authHeaders(),
    });
    savedSet.value.add(groupId);
    emit("saved", groupId);
    // Auto-close after short delay
    setTimeout(() => emit("close"), 1200);
  } catch (e) {
    console.error("[GroupPickerModal] bookmark failed", e);
  } finally {
    saving.value = null;
  }
}

async function createGroup() {
  const name = newGroupName.value.trim();
  if (!name) return;
  creatingGroup.value = true;
  try {
    const created = await $fetch<Group>(`${apiBase}/api/v1/collections`, {
      method: "POST",
      body: { name, kind: "paper_group" },
      headers: _authHeaders(),
    });
    groups.value.push(created);
    showNewGroupForm.value = false;
    newGroupName.value = "";
    // Immediately save to the newly created group
    await handleSelect(created.id);
  } catch (e) {
    console.error("[GroupPickerModal] create group failed", e);
  } finally {
    creatingGroup.value = false;
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="ks-gpm-overlay" @click.self="emit('close')">
      <div
        class="ks-gpm"
        role="dialog"
        aria-modal="true"
        aria-label="Save to group"
      >
        <!-- Header -->
        <div class="ks-gpm-header">
          <div class="ks-gpm-header-icon">
            <Bookmark :size="16" :stroke-width="2" />
          </div>
          <div class="ks-gpm-header-text">
            <h3 class="ks-gpm-title">Save to group</h3>
            <p class="ks-gpm-subtitle" :title="title">
              {{ title.length > 60 ? title.slice(0, 60) + "…" : title }}
            </p>
          </div>
          <button
            class="ks-gpm-close"
            aria-label="Close"
            @click="emit('close')"
          >
            <X :size="16" :stroke-width="2" />
          </button>
        </div>

        <!-- Group list -->
        <div class="ks-gpm-body">
          <div v-if="loadingGroups" class="ks-gpm-loading">Loading groups…</div>
          <template v-else>
            <button
              v-for="group in groups"
              :key="group.id"
              type="button"
              :class="[
                'ks-gpm-group',
                { 'ks-gpm-group--saved': savedSet.has(group.id) },
              ]"
              :disabled="saving === group.id || savedSet.has(group.id)"
              @click="handleSelect(group.id)"
            >
              <span class="ks-gpm-group-name">{{ group.name }}</span>
              <span class="ks-gpm-group-count"
                >{{ group.paper_count }} papers</span
              >
              <Check
                v-if="savedSet.has(group.id)"
                :size="14"
                :stroke-width="2.5"
                class="ks-gpm-group-check"
              />
              <span
                v-else-if="saving === group.id"
                class="ks-gpm-group-spinner"
              />
            </button>

            <p
              v-if="groups.length === 0 && !showNewGroupForm"
              class="ks-gpm-empty"
            >
              No groups yet. Create one below.
            </p>
          </template>
        </div>

        <!-- New group form -->
        <div class="ks-gpm-footer">
          <template v-if="showNewGroupForm">
            <div class="ks-gpm-new-form">
              <input
                v-model="newGroupName"
                type="text"
                class="ks-gpm-new-input"
                placeholder="Group name…"
                :disabled="creatingGroup"
                autofocus
                @keydown.enter="createGroup"
                @keydown.esc="showNewGroupForm = false"
              >
              <button
                type="button"
                class="ks-gpm-new-save"
                :disabled="!newGroupName.trim() || creatingGroup"
                @click="createGroup"
              >
                {{ creatingGroup ? "…" : "Create" }}
              </button>
              <button
                type="button"
                class="ks-gpm-new-cancel"
                @click="showNewGroupForm = false"
              >
                <X :size="14" />
              </button>
            </div>
          </template>
          <button
            v-else
            type="button"
            class="ks-gpm-new-btn"
            @click="showNewGroupForm = true"
          >
            <Plus :size="14" :stroke-width="2.5" /> New Group
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.ks-gpm-overlay {
  position: fixed;
  inset: 0;
  z-index: 300;
  background: rgba(10, 10, 10, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.ks-gpm {
  width: min(100%, 360px);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.16);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ks-gpm-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 16px 16px 12px;
  border-bottom: 1px solid var(--color-border);
}

.ks-gpm-header-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: 6px;
}

.ks-gpm-header-text {
  flex: 1;
  min-width: 0;
}

.ks-gpm-title {
  font: 600 0.9rem / 1.2 var(--font-sans);
  color: var(--color-text);
  margin: 0 0 2px;
}

.ks-gpm-subtitle {
  font: 400 0.75rem / 1.3 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ks-gpm-close {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: none;
  border: none;
  border-radius: 4px;
  color: var(--color-secondary);
  cursor: pointer;
  transition: background-color 0.15s;
}

.ks-gpm-close:hover {
  background: var(--color-bg);
}

.ks-gpm-body {
  flex: 1;
  overflow-y: auto;
  max-height: 280px;
  padding: 6px 0;
}

.ks-gpm-loading {
  padding: 16px;
  font: 400 0.875rem / 1 var(--font-sans);
  color: var(--color-secondary);
  text-align: center;
}

.ks-gpm-group {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 16px;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.12s;
}

.ks-gpm-group:hover:not(:disabled) {
  background: var(--color-primary-light);
}

.ks-gpm-group--saved {
  background: rgba(13, 115, 119, 0.05);
}

.ks-gpm-group:disabled {
  cursor: default;
}

.ks-gpm-group-name {
  flex: 1;
  font: 500 0.875rem / 1 var(--font-sans);
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ks-gpm-group-count {
  font: 400 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
  white-space: nowrap;
}

.ks-gpm-group-check {
  color: var(--color-primary);
  flex-shrink: 0;
}

.ks-gpm-group-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: ks-gpm-spin 0.6s linear infinite;
  flex-shrink: 0;
}

@keyframes ks-gpm-spin {
  to {
    transform: rotate(360deg);
  }
}

.ks-gpm-empty {
  padding: 16px;
  font: 400 0.8125rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
  text-align: center;
  font-style: italic;
}

.ks-gpm-footer {
  padding: 10px 16px;
  border-top: 1px solid var(--color-border);
}

.ks-gpm-new-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  font: 500 0.8125rem / 1 var(--font-sans);
  color: var(--color-primary);
  cursor: pointer;
  padding: 4px 0;
  transition: opacity 0.15s;
}

.ks-gpm-new-btn:hover {
  opacity: 0.75;
}

.ks-gpm-new-form {
  display: flex;
  gap: 6px;
  align-items: center;
}

.ks-gpm-new-input {
  flex: 1;
  padding: 7px 10px;
  border: 1.5px solid var(--color-primary);
  border-radius: 5px;
  background: var(--color-bg);
  font: 400 0.8125rem / 1 var(--font-sans);
  color: var(--color-text);
  outline: none;
}

.ks-gpm-new-save {
  padding: 7px 12px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: 5px;
  font: 600 0.8125rem / 1 var(--font-sans);
  cursor: pointer;
  transition: opacity 0.15s;
  white-space: nowrap;
}

.ks-gpm-new-save:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ks-gpm-new-cancel {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 5px;
  color: var(--color-secondary);
  cursor: pointer;
}
</style>
