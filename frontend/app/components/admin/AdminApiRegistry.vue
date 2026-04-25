<script setup lang="ts">
import type {
  AdminAutoProbeQueue,
  AdminEndpoint,
  AdminMethod,
} from "~/composables/useAdminConsole";

defineProps<{
  groupedEndpoints: Record<string, AdminEndpoint[]>;
  totalRoutes: number;
  filteredRoutes: number;
  domainOptions: string[];
  query: string;
  domain: string;
  method: "all" | AdminMethod;
  autoProbeQueue: AdminAutoProbeQueue;
  autoProbePending?: boolean;
  selectedEndpointId?: string | null;
}>();

const emit = defineEmits<{
  "update:query": [value: string];
  "update:domain": [value: string];
  "update:method": [value: "all" | AdminMethod];
  selectEndpoint: [endpointId: string];
  probeNextBatch: [];
  probeAll: [];
}>();

const methodOptions: Array<"all" | AdminMethod> = [
  "all",
  "GET",
  "POST",
  "PUT",
  "PATCH",
  "DELETE",
];

function probeLabel(mode: AdminEndpoint["probeMode"]) {
  switch (mode) {
    case "safe":
      return "auto";
    case "mutating":
      return "write";
    case "stream":
      return "stream";
    default:
      return "manual";
  }
}

function probeVariant(mode: AdminEndpoint["probeMode"]) {
  switch (mode) {
    case "safe":
      return "success";
    case "mutating":
      return "warning";
    case "stream":
      return "accent";
    default:
      return "neutral";
  }
}

function methodVariant(method: AdminEndpoint["method"]) {
  switch (method) {
    case "GET":
      return "success";
    case "POST":
      return "primary";
    case "PUT":
      return "accent";
    case "PATCH":
      return "warning";
    case "DELETE":
      return "danger";
  }
}

function probeStatusVariant(status: AdminEndpoint["autoProbeStatus"]) {
  switch (status) {
    case "ok":
      return "success";
    case "warning":
      return "accent";
    case "error":
      return "danger";
    default:
      return "neutral";
  }
}

function probeStatusLabel(endpoint: AdminEndpoint) {
  if (endpoint.probeMode !== "safe") {
    return probeLabel(endpoint.probeMode);
  }

  switch (endpoint.autoProbeStatus) {
    case "ok":
      return "healthy";
    case "warning":
      return endpoint.autoProbePath ? "degraded" : "blocked";
    case "error":
      return "broken";
    default:
      return endpoint.autoProbePath ? "pending" : "awaiting";
  }
}
</script>

<template>
  <section class="admin-registry">
    <div class="admin-registry__head">
      <div>
        <p class="ks-type-eyebrow">Full Surface</p>
        <h2 class="ks-type-section-title admin-registry__title">
          API Registry
        </h2>
      </div>
      <p class="ks-type-data admin-registry__meta">
        {{ filteredRoutes }} shown / {{ totalRoutes }} total
      </p>
    </div>

    <KsCard padding="sm" :static="true" class="admin-registry__controls">
      <input
        :value="query"
        class="admin-registry__search"
        type="search"
        placeholder="Filter by path, summary, tag, or operation id"
        @input="emit('update:query', ($event.target as HTMLInputElement).value)"
      />

      <select
        :value="domain"
        class="admin-registry__select"
        @change="
          emit('update:domain', ($event.target as HTMLSelectElement).value)
        "
      >
        <option v-for="option in domainOptions" :key="option" :value="option">
          {{ option === "all" ? "All domains" : option }}
        </option>
      </select>

      <div class="admin-registry__methods">
        <button
          v-for="option in methodOptions"
          :key="option"
          type="button"
          class="admin-registry__method"
          :class="{ 'admin-registry__method--active': option === method }"
          @click="emit('update:method', option)"
        >
          {{ option }}
        </button>
      </div>
    </KsCard>

    <KsCard padding="sm" :static="true" class="admin-registry__probe-panel">
      <div class="admin-registry__probe-head">
        <div>
          <p class="ks-type-label">Auto probe queue</p>
          <p class="ks-type-data admin-registry__probe-meta">
            {{ autoProbeQueue.completedCount }} completed /
            {{ autoProbeQueue.readyCount }} runnable
            <template v-if="autoProbeQueue.blockedCount > 0">
              · {{ autoProbeQueue.blockedCount }} blocked</template
            >
          </p>
        </div>
        <div class="admin-registry__probe-actions">
          <KsButton
            variant="ghost"
            size="sm"
            :disabled="!autoProbeQueue.hasMore"
            :loading="autoProbePending"
            @click="emit('probeNextBatch')"
          >
            Probe next
            {{ autoProbeQueue.nextBatchSize || autoProbeQueue.batchSize }}
          </KsButton>
          <KsButton
            variant="secondary"
            size="sm"
            :disabled="!autoProbeQueue.hasMore"
            :loading="autoProbePending"
            @click="emit('probeAll')"
          >
            Probe all remaining
          </KsButton>
        </div>
      </div>

      <div
        class="admin-registry__probe-progress"
        role="progressbar"
        :aria-valuenow="autoProbeQueue.progressPct"
        aria-valuemin="0"
        aria-valuemax="100"
        :aria-label="`Auto probe progress ${autoProbeQueue.progressPct}%`"
      >
        <div
          class="admin-registry__probe-progress-fill"
          :style="{ width: `${autoProbeQueue.progressPct}%` }"
        />
      </div>

      <div class="admin-registry__probe-stats">
        <KsTag variant="success"
          >{{ autoProbeQueue.succeededCount }} healthy</KsTag
        >
        <KsTag variant="danger">{{ autoProbeQueue.failedCount }} broken</KsTag>
        <KsTag variant="neutral">{{ autoProbeQueue.queuedCount }} queued</KsTag>
        <KsTag v-if="autoProbeQueue.inFlightCount > 0" variant="accent">
          {{ autoProbeQueue.inFlightCount }} in flight
        </KsTag>
      </div>
    </KsCard>

    <div v-if="filteredRoutes === 0" class="admin-registry__empty ks-card">
      No endpoints match the current filter.
    </div>

    <div v-else class="admin-registry__groups">
      <section
        v-for="(group, domainName) in groupedEndpoints"
        :key="domainName"
        class="admin-registry__group"
      >
        <div class="admin-registry__group-head">
          <h3 class="ks-type-label">{{ domainName }}</h3>
          <KsTag variant="neutral">{{ group.length }} routes</KsTag>
        </div>

        <div class="admin-registry__rows">
          <button
            v-for="endpoint in group"
            :key="endpoint.id"
            type="button"
            class="admin-registry__row"
            :class="{
              'admin-registry__row--active': endpoint.id === selectedEndpointId,
            }"
            @click="emit('selectEndpoint', endpoint.id)"
          >
            <div class="admin-registry__row-main">
              <div class="admin-registry__row-meta">
                <KsTag :variant="methodVariant(endpoint.method)">{{
                  endpoint.method
                }}</KsTag>
                <KsTag :variant="probeVariant(endpoint.probeMode)">{{
                  probeLabel(endpoint.probeMode)
                }}</KsTag>
                <KsTag
                  v-if="endpoint.probeMode === 'safe'"
                  :variant="probeStatusVariant(endpoint.autoProbeStatus)"
                >
                  {{ probeStatusLabel(endpoint) }}
                </KsTag>
                <span class="ks-type-data admin-registry__operation">{{
                  endpoint.operationId
                }}</span>
              </div>
              <div class="admin-registry__path">{{ endpoint.path }}</div>
            </div>
            <div class="admin-registry__summary">
              <span class="ks-type-label">{{ endpoint.summary }}</span>
              <span
                v-if="endpoint.description"
                class="ks-type-body-sm admin-registry__description"
              >
                {{ endpoint.description }}
              </span>
              <span
                v-if="endpoint.probeMode === 'safe'"
                class="ks-type-data admin-registry__probe-detail"
              >
                {{ endpoint.autoProbeDetail }}
              </span>
            </div>
          </button>
        </div>
      </section>
    </div>
  </section>
</template>

<style scoped>
.admin-registry {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.admin-registry__head {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 16px;
}

.admin-registry__title {
  margin-top: 6px;
}

.admin-registry__meta {
  color: var(--color-secondary);
}

.admin-registry__controls {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) 220px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
}

.admin-registry__search,
.admin-registry__select {
  width: 100%;
  min-height: 40px;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  font: 500 0.9rem / 1.4 var(--font-sans);
  color: var(--color-text);
}

.admin-registry__methods {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.admin-registry__method {
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  font: 600 0.74rem / 1 var(--font-sans);
  letter-spacing: 0.06em;
  color: var(--color-secondary);
  cursor: pointer;
}

.admin-registry__method--active {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.admin-registry__empty {
  padding: 18px 22px;
  border: 1px dashed var(--color-border);
  color: var(--color-secondary);
}

.admin-registry__groups {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.admin-registry__probe-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.admin-registry__probe-head {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 16px;
}

.admin-registry__probe-meta {
  margin-top: 6px;
  color: var(--color-secondary);
}

.admin-registry__probe-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.admin-registry__probe-progress {
  width: 100%;
  height: 10px;
  overflow: hidden;
  background: var(--color-overlay-medium);
}

.admin-registry__probe-progress-fill {
  height: 100%;
  background: linear-gradient(
    90deg,
    var(--color-primary),
    rgba(13, 115, 119, 0.28)
  );
  transition: width 180ms ease;
}

.admin-registry__probe-stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.admin-registry__group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.admin-registry__group-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.admin-registry__rows {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
}

.admin-registry__row {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.85fr);
  gap: 18px;
  width: 100%;
  padding: 16px 18px;
  border-bottom: 1px solid var(--color-border);
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.admin-registry__row:last-child {
  border-bottom: none;
}

.admin-registry__row:hover,
.admin-registry__row--active {
  background: rgba(13, 115, 119, 0.05);
}

.admin-registry__row-main,
.admin-registry__summary {
  min-width: 0;
}

.admin-registry__row-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.admin-registry__operation {
  color: var(--color-secondary);
}

.admin-registry__path {
  margin-top: 12px;
  font: 600 0.83rem / 1.55 var(--font-mono);
  word-break: break-all;
}

.admin-registry__summary {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
}

.admin-registry__description {
  color: var(--color-secondary);
}

.admin-registry__probe-detail {
  color: var(--color-secondary);
}

@media (max-width: 1100px) {
  .admin-registry__controls {
    grid-template-columns: 1fr;
  }

  .admin-registry__probe-head {
    flex-direction: column;
  }

  .admin-registry__row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .admin-registry__head {
    flex-direction: column;
    align-items: start;
  }
}
</style>
