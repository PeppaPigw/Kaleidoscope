<script setup lang="ts">
definePageMeta({
  layout: "default",
  title: "Admin Console",
});

useHead({
  title: "Admin Console — Kaleidoscope",
  meta: [
    {
      name: "description",
      content:
        "Operational console for API health, route inventory, and admin actions.",
    },
  ],
});

const config = useRuntimeConfig();
const {
  catalogError,
  catalogPending,
  probes,
  probesPending,
  lastLoadedAt,
  samples,
  selectedEndpointId,
  registryQuery,
  activeDomain,
  activeMethod,
  runnerPending,
  runnerResult,
  runnerRestoreEntry,
  quickActionPending,
  quickActionResult,
  selectedEndpointHistory,
  crossEndpointHistory,
  routeProbePending,
  autoProbeQueue,
  domainOptions,
  summary,
  filteredEndpoints,
  groupedEndpoints,
  selectedEndpoint,
  refreshAll,
  runQuickAction,
  runEndpoint,
  runNextRouteProbeBatch,
  runAllRouteProbes,
  restoreHistoryEntry,
  clearRunnerRestoreEntry,
} = useAdminConsole();

const summaryItems = computed(() => [
  {
    label: "Registered routes",
    value: summary.value.totalRoutes,
    detail: "Live count derived from OpenAPI",
  },
  {
    label: "Domains",
    value: summary.value.domainCount,
    detail: "Grouped by router tag",
  },
  {
    label: "Auto candidates",
    value: summary.value.autoCandidates,
    detail: "GET routes eligible for automatic probing",
  },
  {
    label: "Auto verified",
    value: summary.value.autoVerified,
    detail: "Automatic probes that currently succeed",
  },
  {
    label: "Auto failing",
    value: summary.value.autoFailing + summary.value.blockedAuto,
    detail: "Broken or blocked automatic probes",
  },
]);

const docsUrl = computed(() => `${config.public.apiUrl}/docs`);
const openApiUrl = computed(() => `${config.public.apiUrl}/api/openapi.json`);

async function handleRunEndpoint(payload: {
  pathParams: Record<string, unknown>;
  query: Record<string, unknown>;
  body: unknown;
}) {
  if (!selectedEndpoint.value) {
    return;
  }

  await runEndpoint(selectedEndpoint.value, payload);
}

async function handleReprocess(payload: {
  limit: number;
  parserVersionLt?: string;
}) {
  const params = new URLSearchParams({
    limit: String(payload.limit),
  });
  if (payload.parserVersionLt) {
    params.set("parser_version_lt", payload.parserVersionLt);
  }
  await runQuickAction(
    "Bulk Reprocess",
    `/api/v1/admin/reprocess?${params.toString()}`,
    {
      method: "POST",
    },
    {
      endpointId: "POST /api/v1/admin/reprocess",
      query: {
        limit: payload.limit,
        ...(payload.parserVersionLt
          ? { parser_version_lt: payload.parserVersionLt }
          : {}),
      },
      body: null,
    },
  );
}

async function handleSync(payload: {
  mode: "collection" | "paper";
  targetId: string;
}) {
  const body =
    payload.mode === "collection"
      ? { collection_id: payload.targetId }
      : { paper_id: payload.targetId };
  await runQuickAction(
    "RAGFlow Sync",
    "/api/v1/ragflow/sync/trigger",
    {
      method: "POST",
      body,
    },
    {
      endpointId: "POST /api/v1/ragflow/sync/trigger",
      body,
    },
  );
}

async function handleRetraction(payload: { paperId: string }) {
  await runQuickAction(
    "Retraction Check",
    `/api/v1/admin/papers/${payload.paperId}/retraction-check`,
    { method: "POST" },
    {
      endpointId: "POST /api/v1/admin/papers/{paper_id}/retraction-check",
      pathParams: { paper_id: payload.paperId },
      body: null,
    },
  );
}

function selectEndpoint(endpointId: string) {
  selectedEndpointId.value = endpointId;
}

async function handleRestoreHistory(
  entry: Parameters<typeof restoreHistoryEntry>[0],
) {
  await restoreHistoryEntry(entry);
}
</script>

<template>
  <div class="admin-console">
    <KsPageHeader title="Admin Console" section="Ops" :heading-level="1">
      <template #meta
        >API truth surface · health, inventory, and control</template
      >
      <template #actions>
        <KsButton
          variant="ghost"
          as="a"
          :href="openApiUrl"
          target="_blank"
          rel="noreferrer"
        >
          OpenAPI
        </KsButton>
        <KsButton
          variant="secondary"
          as="a"
          :href="docsUrl"
          target="_blank"
          rel="noreferrer"
        >
          API Docs
        </KsButton>
      </template>
    </KsPageHeader>

    <section class="admin-console__hero">
      <div class="admin-console__hero-copy">
        <p class="ks-type-eyebrow">
          Single Place To Inspect What Actually Works
        </p>
        <h1 class="admin-console__headline">
          See which APIs are healthy, which capabilities are degraded, and which
          routes still need manual validation.
        </h1>
      </div>
      <div class="admin-console__hero-stats">
        <KsCard
          v-for="item in summaryItems"
          :key="item.label"
          variant="gold-top"
          class="admin-console__stat"
          :static="true"
        >
          <p class="ks-type-data admin-console__stat-label">{{ item.label }}</p>
          <p class="admin-console__stat-value">{{ item.value }}</p>
          <p class="ks-type-body-sm admin-console__stat-detail">
            {{ item.detail }}
          </p>
        </KsCard>
      </div>
    </section>

    <KsErrorAlert v-if="catalogError" :message="catalogError" />

    <AdminHealthDeck
      :probes="probes"
      :pending="probesPending || catalogPending"
      :last-loaded-at="lastLoadedAt"
    />

    <AdminQuickActions
      :sample-paper-id="samples.paperId"
      :sample-collection-id="samples.collectionId"
      :pending="quickActionPending"
      :result="quickActionResult"
      @refresh="refreshAll"
      @reprocess="handleReprocess"
      @sync="handleSync"
      @retraction="handleRetraction"
    />

    <section class="admin-console__workspace">
      <div class="admin-console__workspace-main">
        <AdminApiRegistry
          :grouped-endpoints="groupedEndpoints"
          :total-routes="summary.totalRoutes"
          :filtered-routes="filteredEndpoints.length"
          :domain-options="domainOptions"
          :query="registryQuery"
          :domain="activeDomain"
          :method="activeMethod"
          :auto-probe-queue="autoProbeQueue"
          :auto-probe-pending="routeProbePending"
          :selected-endpoint-id="selectedEndpointId"
          @update:query="registryQuery = $event"
          @update:domain="activeDomain = $event"
          @update:method="activeMethod = $event"
          @select-endpoint="selectEndpoint"
          @probe-next-batch="runNextRouteProbeBatch"
          @probe-all="runAllRouteProbes"
        />
      </div>

      <div class="admin-console__workspace-side">
        <AdminEndpointRunner
          :endpoint="selectedEndpoint"
          :history="selectedEndpointHistory"
          :cross-history="crossEndpointHistory"
          :restore-entry="runnerRestoreEntry"
          :pending="runnerPending"
          :result="runnerResult"
          @run="handleRunEndpoint"
          @restore="handleRestoreHistory"
          @restore-applied="clearRunnerRestoreEntry"
        />
      </div>
    </section>
  </div>
</template>

<style scoped>
.admin-console {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.admin-console__hero {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 0.8fr);
  gap: 22px;
  padding: 18px 0 4px;
}

.admin-console__hero-copy {
  position: relative;
  padding: 28px 30px 30px;
  background:
    radial-gradient(
      circle at top left,
      rgba(13, 115, 119, 0.12),
      transparent 32%
    ),
    linear-gradient(135deg, rgba(255, 255, 255, 0.8), rgba(250, 250, 247, 1));
  border: 1px solid var(--color-border);
}

.admin-console__headline {
  max-width: 17ch;
  margin-top: 12px;
  font: 600 clamp(2rem, 4vw, 3.45rem) / 1.02 var(--font-display);
  letter-spacing: -0.03em;
  color: var(--color-text);
}

.admin-console__hero-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.admin-console__stat {
  min-height: 150px;
}

.admin-console__stat-label {
  color: var(--color-secondary);
}

.admin-console__stat-value {
  margin-top: 16px;
  font: 600 clamp(1.6rem, 3vw, 2.5rem) / 1 var(--font-display);
}

.admin-console__stat-detail {
  margin-top: 12px;
  color: var(--color-secondary);
}

.admin-console__workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(360px, 0.85fr);
  gap: 22px;
  align-items: start;
}

.admin-console__workspace-side {
  position: sticky;
  top: 74px;
}

@media (max-width: 1280px) {
  .admin-console__hero {
    grid-template-columns: 1fr;
  }

  .admin-console__workspace {
    grid-template-columns: 1fr;
  }

  .admin-console__workspace-side {
    position: static;
  }
}

@media (max-width: 720px) {
  .admin-console__hero-copy {
    padding: 22px 20px 24px;
  }

  .admin-console__headline {
    max-width: none;
  }

  .admin-console__hero-stats {
    grid-template-columns: 1fr;
  }
}
</style>
