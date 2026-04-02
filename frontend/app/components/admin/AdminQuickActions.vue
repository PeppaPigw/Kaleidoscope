<script setup lang="ts">
import { RefreshCcw, RotateCw, ShieldAlert, Workflow } from 'lucide-vue-next'

import type { AdminQuickActionResult } from '~/composables/useAdminConsole'

const props = defineProps<{
  samplePaperId?: string | null
  sampleCollectionId?: string | null
  pending?: boolean
  result?: AdminQuickActionResult | null
}>()

const emit = defineEmits<{
  refresh: []
  reprocess: [payload: { limit: number; parserVersionLt?: string }]
  sync: [payload: { mode: 'collection' | 'paper'; targetId: string }]
  retraction: [payload: { paperId: string }]
}>()

const reprocessLimit = ref(10)
const reprocessVersion = ref('')
const syncMode = ref<'collection' | 'paper'>('collection')
const syncTargetId = ref('')
const retractionPaperId = ref('')

watch(
  () => props.sampleCollectionId,
  sampleCollectionId => {
    if (syncMode.value === 'collection' && !syncTargetId.value && sampleCollectionId) {
      syncTargetId.value = sampleCollectionId
    }
  },
  { immediate: true },
)

watch(
  () => props.samplePaperId,
  samplePaperId => {
    if (!retractionPaperId.value && samplePaperId) {
      retractionPaperId.value = samplePaperId
    }
    if (syncMode.value === 'paper' && !syncTargetId.value && samplePaperId) {
      syncTargetId.value = samplePaperId
    }
  },
  { immediate: true },
)

watch(syncMode, mode => {
  syncTargetId.value = mode === 'collection'
    ? (props.sampleCollectionId ?? '')
    : (props.samplePaperId ?? '')
})
</script>

<template>
  <section class="admin-actions">
    <div class="admin-actions__head">
      <div>
        <p class="ks-type-eyebrow">Operator Console</p>
        <h2 class="ks-type-section-title admin-actions__title">Quick Actions</h2>
      </div>
      <KsButton variant="secondary" :loading="pending" @click="emit('refresh')">
        <template #icon-left><RefreshCcw :size="16" /></template>
        Refresh All
      </KsButton>
    </div>

    <div class="admin-actions__grid">
      <KsCard variant="gold-top" class="admin-actions__card">
        <div class="admin-actions__card-head">
          <RotateCw :size="18" />
          <span class="ks-type-label">Bulk Reprocess</span>
        </div>
        <label class="admin-actions__field">
          <span class="ks-type-data">Limit</span>
          <input v-model.number="reprocessLimit" class="admin-actions__input" type="number" min="1" max="500">
        </label>
        <label class="admin-actions__field">
          <span class="ks-type-data">Parser version lower than</span>
          <input
            v-model="reprocessVersion"
            class="admin-actions__input"
            type="text"
            placeholder="Optional version string"
          >
        </label>
        <KsButton
          variant="primary"
          :loading="pending"
          @click="emit('reprocess', { limit: Math.max(1, Number(reprocessLimit) || 1), parserVersionLt: reprocessVersion || undefined })"
        >
          Queue Reprocess
        </KsButton>
      </KsCard>

      <KsCard variant="teal-top" class="admin-actions__card">
        <div class="admin-actions__card-head">
          <Workflow :size="18" />
          <span class="ks-type-label">RAGFlow Sync</span>
        </div>
        <label class="admin-actions__field">
          <span class="ks-type-data">Mode</span>
          <select v-model="syncMode" class="admin-actions__input">
            <option value="collection">Collection</option>
            <option value="paper">Paper</option>
          </select>
        </label>
        <label class="admin-actions__field">
          <span class="ks-type-data">Target ID</span>
          <input
            v-model="syncTargetId"
            class="admin-actions__input"
            type="text"
            :placeholder="syncMode === 'collection' ? 'Collection UUID' : 'Paper UUID'"
          >
        </label>
        <p class="ks-type-data admin-actions__hint">
          Sample: {{ syncMode === 'collection' ? (sampleCollectionId ?? 'none loaded') : (samplePaperId ?? 'none loaded') }}
        </p>
        <KsButton
          variant="primary"
          :disabled="!syncTargetId"
          :loading="pending"
          @click="emit('sync', { mode: syncMode, targetId: syncTargetId })"
        >
          Trigger Sync
        </KsButton>
      </KsCard>

      <KsCard class="admin-actions__card">
        <div class="admin-actions__card-head">
          <ShieldAlert :size="18" />
          <span class="ks-type-label">Retraction Check</span>
        </div>
        <label class="admin-actions__field">
          <span class="ks-type-data">Paper ID</span>
          <input
            v-model="retractionPaperId"
            class="admin-actions__input"
            type="text"
            placeholder="Paper UUID"
          >
        </label>
        <p class="ks-type-data admin-actions__hint">
          Sample: {{ samplePaperId ?? 'none loaded' }}
        </p>
        <KsButton
          variant="secondary"
          :disabled="!retractionPaperId"
          :loading="pending"
          @click="emit('retraction', { paperId: retractionPaperId })"
        >
          Check Paper
        </KsButton>
      </KsCard>
    </div>

    <KsCard v-if="props.result" padding="sm" class="admin-actions__result" :static="true">
      <div class="admin-actions__result-head">
        <p class="ks-type-label">{{ props.result.label }}</p>
        <KsTag :variant="props.result.ok ? 'success' : 'danger'">
          HTTP {{ props.result.status || 0 }}
        </KsTag>
      </div>
      <p class="ks-type-data admin-actions__result-meta">
        {{ props.result.method }} {{ props.result.path }} · {{ props.result.durationMs }} ms
      </p>
      <pre class="admin-actions__result-body">{{ JSON.stringify(props.result.data, null, 2) }}</pre>
    </KsCard>
  </section>
</template>

<style scoped>
.admin-actions {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.admin-actions__head {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 16px;
}

.admin-actions__title {
  margin-top: 6px;
}

.admin-actions__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.admin-actions__card {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.admin-actions__card-head {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--color-text);
}

.admin-actions__field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.admin-actions__input {
  width: 100%;
  min-height: 40px;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  font: 500 0.9rem / 1.4 var(--font-sans);
  color: var(--color-text);
}

.admin-actions__hint {
  color: var(--color-secondary);
}

.admin-actions__result {
  overflow: hidden;
}

.admin-actions__result-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.admin-actions__result-meta {
  margin-top: 8px;
  color: var(--color-secondary);
}

.admin-actions__result-body {
  margin-top: 12px;
  max-height: 240px;
  overflow: auto;
  padding: 14px;
  background: rgba(26, 26, 26, 0.03);
  font: 500 0.78rem / 1.55 var(--font-mono);
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 1120px) {
  .admin-actions__grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .admin-actions__head {
    flex-direction: column;
    align-items: start;
  }
}
</style>
