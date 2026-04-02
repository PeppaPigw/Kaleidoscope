<script setup lang="ts">
import { Clock3, Play, Wrench } from 'lucide-vue-next'

import {
  createHistoryRestoreSeed,
  createRunnerSeed,
  type AdminEndpoint,
  type AdminRequestHistoryEntry,
  type AdminRunResult,
} from '~/composables/useAdminConsole'

const props = defineProps<{
  endpoint: AdminEndpoint | null
  pending?: boolean
  result?: AdminRunResult | null
  history?: AdminRequestHistoryEntry[]
  crossHistory?: AdminRequestHistoryEntry[]
  restoreEntry?: AdminRequestHistoryEntry | null
}>()

const emit = defineEmits<{
  run: [payload: { pathParams: Record<string, unknown>; query: Record<string, unknown>; body: unknown }]
  restore: [entry: AdminRequestHistoryEntry]
  restoreApplied: []
}>()

const pathParamsText = ref('{}')
const queryText = ref('{}')
const bodyText = ref('')
const parseError = ref<string | null>(null)

watch(
  () => props.endpoint,
  endpoint => {
    parseError.value = null
    if (!endpoint) {
      pathParamsText.value = '{}'
      queryText.value = '{}'
      bodyText.value = ''
      return
    }

    const seed = createRunnerSeed(endpoint)
    pathParamsText.value = seed.pathParamsText
    queryText.value = seed.queryText
    bodyText.value = seed.bodyText
  },
  { immediate: true },
)

watch(
  () => props.restoreEntry,
  restoreEntry => {
    if (!restoreEntry || !props.endpoint || restoreEntry.endpointId !== props.endpoint.id) {
      return
    }

    applyHistoryEntry(restoreEntry)
    emit('restoreApplied')
  },
)

function safeParseObject(input: string, label: string) {
  const trimmed = input.trim()
  if (!trimmed) {
    return {}
  }

  const parsed = JSON.parse(trimmed)
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error(`${label} must be a JSON object`)
  }
  return parsed as Record<string, unknown>
}

function safeParseBody(input: string) {
  const trimmed = input.trim()
  if (!trimmed) {
    return null
  }
  return JSON.parse(trimmed)
}

function runSelectedEndpoint() {
  parseError.value = null

  try {
    emit('run', {
      pathParams: safeParseObject(pathParamsText.value, 'Path params'),
      query: safeParseObject(queryText.value, 'Query params'),
      body: safeParseBody(bodyText.value),
    })
  }
  catch (error) {
    parseError.value = error instanceof Error ? error.message : 'Invalid JSON payload'
  }
}

function methodVariant(method: AdminEndpoint['method']) {
  switch (method) {
    case 'GET':
      return 'success'
    case 'POST':
      return 'primary'
    case 'PUT':
      return 'accent'
    case 'PATCH':
      return 'warning'
    case 'DELETE':
      return 'danger'
  }
}

function schemaSummary(schema: Record<string, unknown> | null) {
  if (!schema) {
    return 'Unspecified'
  }

  const type = typeof schema.type === 'string' ? schema.type : null
  const format = typeof schema.format === 'string' ? schema.format : null
  const enumValues = Array.isArray(schema.enum) ? schema.enum : null
  const items = schema.items && typeof schema.items === 'object'
    ? (schema.items as Record<string, unknown>)
    : null

  if (enumValues && enumValues.length > 0) {
    return `enum(${enumValues.join(', ')})`
  }

  if (items && typeof items.type === 'string') {
    return `${type ?? 'array'}<${items.type}>`
  }

  if (format) {
    return `${type ?? 'value'}:${format}`
  }

  return type ?? 'object'
}

function applyHistoryEntry(entry: AdminRequestHistoryEntry) {
  const restored = createHistoryRestoreSeed(entry)
  pathParamsText.value = restored.pathParamsText
  queryText.value = restored.queryText
  bodyText.value = restored.bodyText
  parseError.value = null
}
</script>

<template>
  <section class="admin-runner">
    <div class="admin-runner__head">
      <div>
        <p class="ks-type-eyebrow">Manual Invocation</p>
        <h2 class="ks-type-section-title admin-runner__title">Endpoint Runner</h2>
      </div>
      <p class="ks-type-data admin-runner__meta">
        {{ endpoint ? 'Use JSON objects for path/query params and body' : 'Select an endpoint to begin' }}
      </p>
    </div>

    <KsCard class="admin-runner__panel" :static="true">
      <template v-if="endpoint">
        <div class="admin-runner__endpoint">
          <div class="admin-runner__endpoint-head">
            <div class="admin-runner__endpoint-badges">
              <KsTag :variant="methodVariant(endpoint.method)">{{ endpoint.method }}</KsTag>
              <KsTag variant="neutral">{{ endpoint.domain }}</KsTag>
              <KsTag v-if="endpoint.requestBody" variant="accent">body</KsTag>
            </div>
            <div class="admin-runner__endpoint-path">{{ endpoint.path }}</div>
          </div>
          <div class="admin-runner__endpoint-copy">
            <p class="ks-type-label">{{ endpoint.summary }}</p>
            <p v-if="endpoint.description" class="ks-type-body-sm admin-runner__description">
              {{ endpoint.description }}
            </p>
          </div>
        </div>

        <div class="admin-runner__grid">
          <label class="admin-runner__field">
            <span class="ks-type-data">Path params JSON</span>
            <textarea
              v-model="pathParamsText"
              class="admin-runner__textarea"
              rows="6"
              spellcheck="false"
            />
          </label>

          <label class="admin-runner__field">
            <span class="ks-type-data">Query params JSON</span>
            <textarea
              v-model="queryText"
              class="admin-runner__textarea"
              rows="6"
              spellcheck="false"
            />
          </label>

          <label class="admin-runner__field admin-runner__field--wide">
            <span class="ks-type-data">Request body JSON</span>
            <textarea
              v-model="bodyText"
              class="admin-runner__textarea admin-runner__textarea--body"
              rows="9"
              spellcheck="false"
              :placeholder="endpoint.requestBody ? '{}' : 'No request body required for this endpoint'"
            />
          </label>
        </div>

        <div class="admin-runner__schema-grid">
          <KsCard padding="sm" :static="true" class="admin-runner__schema-card">
            <p class="ks-type-label">Parameter schema</p>
            <div v-if="endpoint.parameters.length > 0" class="admin-runner__schema-list">
              <div
                v-for="parameter in endpoint.parameters"
                :key="`${parameter.location}-${parameter.name}`"
                class="admin-runner__schema-item"
              >
                <div class="admin-runner__schema-item-head">
                  <span class="ks-type-label">{{ parameter.name }}</span>
                  <div class="admin-runner__schema-badges">
                    <KsTag variant="neutral">{{ parameter.location }}</KsTag>
                    <KsTag :variant="parameter.required ? 'warning' : 'success'">
                      {{ parameter.required ? 'required' : 'optional' }}
                    </KsTag>
                  </div>
                </div>
                <p class="ks-type-data">{{ schemaSummary(parameter.schema) }}</p>
                <p v-if="parameter.description" class="ks-type-body-sm admin-runner__schema-copy">
                  {{ parameter.description }}
                </p>
              </div>
            </div>
            <p v-else class="ks-type-data admin-runner__schema-empty">No parameters declared for this endpoint.</p>
          </KsCard>

          <KsCard padding="sm" :static="true" class="admin-runner__schema-card">
            <p class="ks-type-label">Request body schema</p>
            <div v-if="endpoint.requestBody" class="admin-runner__body-schema">
              <div class="admin-runner__schema-badges">
                <KsTag :variant="endpoint.requestBody.required ? 'warning' : 'success'">
                  {{ endpoint.requestBody.required ? 'required body' : 'optional body' }}
                </KsTag>
                <KsTag variant="accent">{{ endpoint.requestBody.contentTypes.join(', ') }}</KsTag>
              </div>
              <p class="ks-type-data admin-runner__schema-copy">
                {{ schemaSummary(endpoint.requestBody.schema) }}
              </p>
              <pre class="admin-runner__schema-json">{{ JSON.stringify(endpoint.requestBody.schema ?? {}, null, 2) }}</pre>
            </div>
            <p v-else class="ks-type-data admin-runner__schema-empty">No request body for this endpoint.</p>
          </KsCard>
        </div>

        <div class="admin-runner__actions">
          <p v-if="parseError" class="admin-runner__error">{{ parseError }}</p>
          <KsButton variant="primary" :loading="pending" @click="runSelectedEndpoint">
            <template #icon-left><Play :size="16" /></template>
            Run Request
          </KsButton>
        </div>
      </template>

      <div v-else class="admin-runner__empty">
        <Wrench :size="18" />
        <span class="ks-type-label">Choose an endpoint from the registry to inspect and execute it.</span>
      </div>
    </KsCard>

    <KsCard v-if="result" padding="sm" :static="true" class="admin-runner__result">
      <div class="admin-runner__result-head">
        <div>
          <p class="ks-type-label">{{ result.method }} {{ result.path }}</p>
          <p class="ks-type-data admin-runner__result-meta">
            HTTP {{ result.status || 0 }} · {{ result.durationMs }} ms · {{ new Date(result.timestamp).toLocaleTimeString() }}
          </p>
        </div>
        <KsTag :variant="result.ok ? 'success' : 'danger'">
          {{ result.ok ? 'success' : 'failed' }}
        </KsTag>
      </div>
      <pre class="admin-runner__result-body">{{ JSON.stringify(result.data, null, 2) }}</pre>
    </KsCard>

    <KsCard v-if="history && history.length > 0" padding="sm" :static="true" class="admin-runner__history">
      <div class="admin-runner__history-head">
        <div>
          <p class="ks-type-label">Endpoint request history</p>
          <p class="ks-type-data admin-runner__result-meta">Stored locally for the current endpoint.</p>
        </div>
        <Clock3 :size="16" />
      </div>
      <div class="admin-runner__history-list">
        <button
          v-for="entry in history"
          :key="entry.id"
          type="button"
          class="admin-runner__history-item"
          @click="applyHistoryEntry(entry)"
        >
          <div class="admin-runner__history-item-head">
            <span class="ks-type-label">{{ entry.label }}</span>
            <KsTag :variant="entry.ok ? 'success' : 'danger'">HTTP {{ entry.status || 0 }}</KsTag>
          </div>
          <p class="ks-type-data admin-runner__history-meta">
            {{ entry.method }} {{ entry.path }} · {{ entry.durationMs }} ms · {{ new Date(entry.timestamp).toLocaleString() }}
          </p>
        </button>
      </div>
    </KsCard>

    <KsCard
      v-if="crossHistory && crossHistory.length > 0"
      padding="sm"
      :static="true"
      class="admin-runner__history"
    >
      <div class="admin-runner__history-head">
        <div>
          <p class="ks-type-label">Cross-endpoint restore</p>
          <p class="ks-type-data admin-runner__result-meta">Jump to a different endpoint and restore its last payload.</p>
        </div>
        <Clock3 :size="16" />
      </div>
      <div class="admin-runner__history-list">
        <button
          v-for="entry in crossHistory"
          :key="entry.id"
          type="button"
          class="admin-runner__history-item"
          @click="emit('restore', entry)"
        >
          <div class="admin-runner__history-item-head">
            <span class="ks-type-label">{{ entry.label }}</span>
            <KsTag :variant="entry.ok ? 'success' : 'danger'">HTTP {{ entry.status || 0 }}</KsTag>
          </div>
          <p class="ks-type-data admin-runner__history-meta">
            {{ entry.method }} {{ entry.path }} · {{ entry.durationMs }} ms · {{ new Date(entry.timestamp).toLocaleString() }}
          </p>
        </button>
      </div>
    </KsCard>
  </section>
</template>

<style scoped>
.admin-runner {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.admin-runner__head {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 16px;
}

.admin-runner__title {
  margin-top: 6px;
}

.admin-runner__meta {
  color: var(--color-secondary);
}

.admin-runner__panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.admin-runner__endpoint {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.admin-runner__endpoint-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.admin-runner__endpoint-path {
  margin-top: 12px;
  font: 600 0.84rem / 1.55 var(--font-mono);
  word-break: break-all;
}

.admin-runner__description {
  margin-top: 6px;
  color: var(--color-secondary);
}

.admin-runner__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.admin-runner__schema-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.admin-runner__field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.admin-runner__field--wide {
  grid-column: 1 / -1;
}

.admin-runner__textarea {
  width: 100%;
  min-height: 120px;
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  font: 500 0.8rem / 1.6 var(--font-mono);
  color: var(--color-text);
  resize: vertical;
}

.admin-runner__textarea--body {
  min-height: 180px;
}

.admin-runner__actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.admin-runner__error {
  color: #B54A4A;
  font: 500 0.82rem / 1.4 var(--font-sans);
}

.admin-runner__schema-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.admin-runner__schema-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.admin-runner__schema-item {
  padding: 12px;
  border: 1px solid var(--color-border);
  background: rgba(13, 115, 119, 0.03);
}

.admin-runner__schema-item-head,
.admin-runner__schema-badges,
.admin-runner__history-item-head,
.admin-runner__history-head {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 10px;
  flex-wrap: wrap;
}

.admin-runner__schema-copy {
  margin-top: 6px;
  color: var(--color-secondary);
}

.admin-runner__schema-empty {
  color: var(--color-secondary);
}

.admin-runner__schema-json {
  max-height: 200px;
  overflow: auto;
  padding: 12px;
  background: rgba(26, 26, 26, 0.03);
  font: 500 0.75rem / 1.55 var(--font-mono);
  white-space: pre-wrap;
  word-break: break-word;
}

.admin-runner__empty {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--color-secondary);
}

.admin-runner__result-head {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 12px;
}

.admin-runner__result-meta {
  margin-top: 6px;
  color: var(--color-secondary);
}

.admin-runner__result-body {
  margin-top: 12px;
  max-height: 360px;
  overflow: auto;
  padding: 14px;
  background: rgba(26, 26, 26, 0.03);
  font: 500 0.78rem / 1.55 var(--font-mono);
  white-space: pre-wrap;
  word-break: break-word;
}

.admin-runner__history {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.admin-runner__history-list {
  display: flex;
  flex-direction: column;
}

.admin-runner__history-item {
  width: 100%;
  padding: 12px 0;
  border: none;
  border-top: 1px solid var(--color-border);
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.admin-runner__history-item:first-child {
  border-top: none;
}

.admin-runner__history-meta {
  margin-top: 6px;
  color: var(--color-secondary);
}

@media (max-width: 980px) {
  .admin-runner__grid,
  .admin-runner__schema-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .admin-runner__head,
  .admin-runner__actions,
  .admin-runner__result-head {
    flex-direction: column;
    align-items: start;
  }
}
</style>
