<script setup lang="ts">
/**
 * Evidence & Methods Lab — analysis/evidence
 */
import type {
  AnalysisMethodsRequest,
  AnalysisMethodsResponse,
  AnalysisMethodsRowSummary,
  AnalysisMatrixRow,
  ContradictionPair,
} from "~/composables/useApi";
import type { EvidenceFilterOption } from "~/components/evidence/FiltersPanel.vue";
import type { MatrixResult } from "~/components/evidence/ResultsMatrix.vue";
import type { Contradiction } from "~/components/evidence/ContradictionsPanel.vue";

definePageMeta({ layout: "default" });

const DEFAULT_RESEARCH_QUESTION =
  "How does claim-level granularity affect retrieval-augmented generation accuracy?";
const DEFAULT_DESCRIPTION =
  "Investigating the trade-off between decomposition granularity and downstream retrieval quality in biomedical NLP.";

const route = useRoute();
const { t } = useTranslation();
const api = useApi();

useHead({
  title: "Evidence Lab — Kaleidoscope",
  meta: [
    {
      name: "description",
      content: "Analyze methods, results, and contradictions across papers.",
    },
  ],
});

const paperCount = ref(0);
const claimCount = ref(0);
const methodsResponse = ref<AnalysisMethodsResponse | null>(null);
const contradictionPairs = ref<ContradictionPair[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

let loadSequence = 0;

function parseQueryList(value: string | string[] | null | undefined): string[] {
  const values = Array.isArray(value)
    ? value
    : typeof value === "string"
      ? [value]
      : [];

  const seen = new Set<string>();
  const output: string[] = [];
  for (const raw of values) {
    for (const part of raw.split(",")) {
      const next = part.trim();
      if (!next || seen.has(next)) continue;
      seen.add(next);
      output.push(next);
    }
  }
  return output;
}

function parseQueryBool(value: string | string[] | null | undefined): boolean {
  const normalized = Array.isArray(value) ? value[0] : value;
  return normalized === "1" || normalized === "true";
}

function queryValue(value: string | string[] | null | undefined): string {
  if (Array.isArray(value)) return value[0] ?? "";
  return typeof value === "string" ? value : "";
}

function cleanQuery(
  input: Record<string, string | undefined>,
): Record<string, string> {
  return Object.fromEntries(
    Object.entries(input).filter((entry): entry is [string, string] => {
      return Boolean(entry[1] && entry[1].trim());
    }),
  );
}

function routeQueryAsStrings(): Record<string, string> {
  return Object.fromEntries(
    Object.entries(route.query).map(([key, value]) => [
      key,
      Array.isArray(value) ? value.join(",") : String(value ?? ""),
    ]),
  );
}

async function updateQuery(patch: Record<string, string | undefined>) {
  await navigateTo(
    {
      query: cleanQuery({
        ...routeQueryAsStrings(),
        ...patch,
      }),
    },
    { replace: true },
  );
}

const methodQuery = computed(() => {
  return queryValue(route.query.method as string | string[] | undefined).trim();
});

const activeCollectionId = computed(() => {
  const value = route.query.collectionId;
  return typeof value === "string" && value.trim() ? value : undefined;
});

const activeDatasetIds = computed(() => {
  return parseQueryList(route.query.datasets as string | string[] | undefined);
});

const activeMetricIds = computed(() => {
  return parseQueryList(route.query.metrics as string | string[] | undefined);
});

const activeResearchQuestion = computed(() => {
  return (
    methodsResponse.value?.research_question ||
    queryValue(route.query.rq as string | string[] | undefined).trim() ||
    DEFAULT_RESEARCH_QUESTION
  );
});

const activeDescription = computed(() => {
  const queryDescription = queryValue(
    route.query.rqDesc as string | string[] | undefined,
  ).trim();
  if (queryDescription) return queryDescription;
  return methodsResponse.value?.scope.type
    ? scopeDescription.value
    : DEFAULT_DESCRIPTION;
});

const requestPayload = computed<AnalysisMethodsRequest>(() => ({
  paper_ids: parseQueryList(
    route.query.paperIds as string | string[] | undefined,
  ),
  collection_id:
    typeof route.query.collectionId === "string" &&
    route.query.collectionId.trim()
      ? route.query.collectionId
      : undefined,
  research_question:
    queryValue(route.query.rq as string | string[] | undefined).trim() ||
    undefined,
  filters: {
    datasets: activeDatasetIds.value,
    metrics: activeMetricIds.value,
    main_results_only: parseQueryBool(
      route.query.mainOnly as string | string[] | undefined,
    ),
    include_uncomparable: parseQueryBool(
      route.query.includeUncomparable as string | string[] | undefined,
    ),
  },
}));

const requestKey = computed(() => JSON.stringify(requestPayload.value));

const scopeDescription = computed(() => {
  const scope = methodsResponse.value?.scope;
  if (!scope) return DEFAULT_DESCRIPTION;

  if (scope.type === "recent") {
    return `Analyzing the ${scope.paper_count} most recently parsed papers with live method and result aggregation.`;
  }
  if (scope.type === "collection") {
    return `Analyzing ${scope.paper_count} parsed papers from the selected collection with vector-backed evidence lookup.`;
  }
  return `Analyzing ${scope.paper_count} selected papers with cross-paper method and result normalization.`;
});

const datasetOptions = computed<EvidenceFilterOption[]>(() => {
  const counts = new Map<string, number>();
  for (const method of methodsResponse.value?.methods ?? []) {
    for (const dataset of method.datasets) {
      counts.set(dataset, (counts.get(dataset) ?? 0) + 1);
    }
  }
  return (methodsResponse.value?.datasets ?? []).map((dataset) => ({
    id: dataset,
    label: dataset,
    count: counts.get(dataset) ?? 0,
  }));
});

const metricOptions = computed<EvidenceFilterOption[]>(() => {
  const counts = new Map<string, number>();
  for (const method of methodsResponse.value?.methods ?? []) {
    for (const metric of method.metrics) {
      counts.set(metric, (counts.get(metric) ?? 0) + 1);
    }
  }
  return (methodsResponse.value?.metrics ?? []).map((metric) => ({
    id: metric,
    label: metric,
    count: counts.get(metric) ?? 0,
  }));
});

const filteredMatrixRows = computed<AnalysisMatrixRow[]>(() => {
  const rows = methodsResponse.value?.matrix.rows ?? [];
  const query = methodQuery.value.toLowerCase();
  if (!query) return rows;

  return rows.filter((row) => {
    return (
      row.method.toLowerCase().includes(query) ||
      row.paper_title.toLowerCase().includes(query) ||
      row.source.toLowerCase().includes(query)
    );
  });
});

const filteredMethodSummaries = computed<AnalysisMethodsRowSummary[]>(() => {
  const visibleRowIds = new Set(filteredMatrixRows.value.map((row) => row.id));
  return (methodsResponse.value?.methods ?? []).filter((method) =>
    visibleRowIds.has(method.id),
  );
});

const metricNames = computed(() => {
  return methodsResponse.value?.matrix.metric_names ?? [];
});

const results = computed<MatrixResult[]>(() => {
  return filteredMatrixRows.value.map((row) => ({
    id: row.id,
    method: row.method,
    metrics: row.metrics,
    isBest: row.is_best,
    source: row.source,
  }));
});

const contradictions = computed<Contradiction[]>(() => {
  return contradictionPairs.value.map((pair) => ({
    id: pair.id,
    claimA: {
      text: pair.claimA.text,
      paper: pair.claimA.paper || pair.claimA.paper_id || "Unknown",
      year: pair.claimA.year || 0,
    },
    claimB: {
      text: pair.claimB.text,
      paper: pair.claimB.paper || pair.claimB.paper_id || "Unknown",
      year: pair.claimB.year || 0,
    },
    severity: pair.severity,
    resolved: pair.resolved,
  }));
});

const warnings = computed(() => methodsResponse.value?.warnings ?? []);

const hasMatrixData = computed(() => {
  return results.value.length > 0 && metricNames.value.length > 0;
});

const hasAnyResults = computed(() => {
  return (methodsResponse.value?.matrix.rows.length ?? 0) > 0;
});

const hasContradictions = computed(() => contradictions.value.length > 0);

const hasActiveFilters = computed(() => {
  return (
    activeDatasetIds.value.length > 0 ||
    activeMetricIds.value.length > 0 ||
    Boolean(methodQuery.value)
  );
});

const coveragePct = computed(() => {
  return Math.round((methodsResponse.value?.coverage.overall ?? 0) * 100);
});

const exportFilenameBase = computed(() => {
  const date = new Date().toISOString().slice(0, 10);
  return `evidence-lab-${date}`;
});

const qaPlaceholder = computed(() => {
  if (activeCollectionId.value) {
    return "Ask a question about the papers in this evidence scope...";
  }
  return "Search for evidence across your corpus...";
});

const exportJsonData = computed(() => {
  return {
    generated_at: new Date().toISOString(),
    research_question: activeResearchQuestion.value,
    description: activeDescription.value,
    scope: methodsResponse.value?.scope ?? null,
    filters: {
      datasets: activeDatasetIds.value,
      metrics: activeMetricIds.value,
      method: methodQuery.value,
    },
    coverage: methodsResponse.value?.coverage ?? null,
    warnings: warnings.value,
    results: filteredMethodSummaries.value,
    matrix: {
      metric_names: metricNames.value,
      rows: filteredMatrixRows.value,
    },
    contradictions: contradictionPairs.value,
  };
});

const exportCsvContent = computed(() => {
  const escape = (value: string) => {
    const normalized = value.replaceAll('"', '""');
    return `"${normalized}"`;
  };

  const header = [
    "Method",
    "Paper",
    "Source",
    "Confidence",
    ...metricNames.value,
  ];
  const rows = filteredMatrixRows.value.map((row) => [
    row.method,
    row.paper_title,
    row.source,
    row.confidence == null ? "" : String(row.confidence),
    ...metricNames.value.map((metric) => row.metrics[metric] ?? ""),
  ]);
  return [header, ...rows]
    .map((line) => line.map((cell) => escape(String(cell))).join(","))
    .join("\n");
});

async function loadEvidenceLab() {
  const sequence = ++loadSequence;
  loading.value = true;
  error.value = null;

  try {
    const [methodsResult, overviewResult, claimsResult, contradictionsResult] =
      await Promise.allSettled([
        api.getAnalysisMethods(requestPayload.value),
        api.getAnalyticsOverview(),
        api.getClaimsStats(),
        api.getContradictions(10),
      ]);

    if (sequence !== loadSequence) return;

    if (methodsResult.status === "rejected") {
      throw methodsResult.reason;
    }
    methodsResponse.value = methodsResult.value;

    if (overviewResult.status === "fulfilled") {
      paperCount.value =
        methodsResult.value.scope.paper_count ||
        overviewResult.value.total_papers ||
        0;
    } else {
      paperCount.value = methodsResult.value.scope.paper_count || 0;
    }

    if (claimsResult.status === "fulfilled") {
      claimCount.value = claimsResult.value.total_claims ?? 0;
    } else {
      claimCount.value = 0;
    }

    if (contradictionsResult.status === "fulfilled") {
      contradictionPairs.value =
        contradictionsResult.value.contradictions ?? [];
    } else {
      contradictionPairs.value = [];
    }
  } catch (err: unknown) {
    if (sequence !== loadSequence) return;
    methodsResponse.value = null;
    contradictionPairs.value = [];
    paperCount.value = 0;
    claimCount.value = 0;
    error.value = extractErrorMessage(err);
  } finally {
    if (sequence === loadSequence) {
      loading.value = false;
    }
  }
}

function extractErrorMessage(err: unknown): string {
  if (!err || typeof err !== "object") {
    return "Failed to load Evidence Lab analysis.";
  }

  const record = err as {
    message?: unknown;
    data?: {
      message?: unknown;
      detail?: unknown;
    };
  };
  const detail = record.data?.detail;
  const nestedMessage =
    detail && typeof detail === "object"
      ? (detail as { message?: unknown }).message
      : undefined;

  const candidate =
    record.data?.message ?? nestedMessage ?? detail ?? record.message;

  return typeof candidate === "string" && candidate.trim()
    ? candidate
    : "Failed to load Evidence Lab analysis.";
}

watch(requestKey, loadEvidenceLab, { immediate: true });

async function handleRQSave(payload: {
  question: string;
  description: string;
}) {
  await updateQuery({
    rq: payload.question || undefined,
    rqDesc: payload.description || undefined,
  });
}

async function handleDatasetsChange(values: string[]) {
  await updateQuery({
    datasets: values.length ? values.join(",") : undefined,
  });
}

async function handleMetricsChange(values: string[]) {
  await updateQuery({
    metrics: values.length ? values.join(",") : undefined,
  });
}

async function handleMethodQueryChange(value: string) {
  await updateQuery({
    method: value || undefined,
  });
}

async function clearFilters() {
  await updateQuery({
    datasets: undefined,
    metrics: undefined,
    method: undefined,
  });
}
</script>

<template>
  <div class="ks-evidence-lab">
    <KsPageHeader
      :title="t('evidenceLab')"
      :subtitle="t('evidenceLabSubtitle')"
    />

    <div class="ks-evidence-lab__content">
      <template v-if="loading">
        <section class="ks-evidence-lab__skeleton-header ks-card">
          <KsSkeleton variant="line" width="160px" />
          <KsSkeleton variant="line" width="72%" height="28px" />
          <KsSkeleton variant="paragraph" :lines="3" />
        </section>

        <section class="ks-evidence-lab__skeleton-row">
          <div class="ks-card ks-evidence-lab__skeleton-card">
            <KsSkeleton variant="line" width="180px" />
            <KsSkeleton variant="line" width="120px" />
          </div>
          <div class="ks-card ks-evidence-lab__skeleton-card">
            <KsSkeleton variant="line" width="160px" />
            <KsSkeleton variant="paragraph" :lines="3" />
          </div>
        </section>

        <section class="ks-evidence-lab__skeleton-card ks-card">
          <KsSkeleton variant="line" width="220px" />
          <KsSkeleton variant="paragraph" :lines="6" />
        </section>

        <section class="ks-evidence-lab__skeleton-card ks-card">
          <KsSkeleton variant="line" width="180px" />
          <KsSkeleton variant="paragraph" :lines="4" />
        </section>
      </template>

      <template v-else>
        <EvidenceRQHeader
          :question="activeResearchQuestion"
          :description="activeDescription"
          :paper-count="paperCount"
          :claim-count="claimCount"
          @save="handleRQSave"
        />

        <KsErrorAlert
          v-if="error"
          :message="error"
          retryable
          @retry="loadEvidenceLab"
        />

        <template v-else>
          <section
            class="ks-card ks-evidence-lab__overview"
            aria-labelledby="evidence-overview-title"
          >
            <div class="ks-evidence-lab__overview-header">
              <div>
                <p id="evidence-overview-title" class="ks-type-eyebrow">
                  Analysis Coverage
                </p>
                <p class="ks-evidence-lab__overview-copy">
                  {{ coveragePct }}% normalized coverage across
                  {{ methodsResponse?.coverage.papers_total ?? 0 }} papers
                </p>
              </div>
              <ExportButton
                :filename-base="exportFilenameBase"
                :json-data="exportJsonData"
                :csv-content="exportCsvContent"
                :disabled="!hasAnyResults"
              />
            </div>

            <div class="ks-evidence-lab__coverage-bar">
              <div
                class="ks-evidence-lab__coverage-fill"
                :style="{ width: `${coveragePct}%` }"
              />
            </div>

            <div class="ks-evidence-lab__coverage-grid">
              <div class="ks-evidence-lab__coverage-item">
                <span class="ks-evidence-lab__coverage-value">
                  {{ methodsResponse?.coverage.records_total ?? 0 }}
                </span>
                <span class="ks-type-data">records</span>
              </div>
              <div class="ks-evidence-lab__coverage-item">
                <span class="ks-evidence-lab__coverage-value">
                  {{ methodsResponse?.coverage.papers_with_records ?? 0 }}
                </span>
                <span class="ks-type-data">papers with results</span>
              </div>
              <div class="ks-evidence-lab__coverage-item">
                <span class="ks-evidence-lab__coverage-value">
                  {{ methodsResponse?.coverage.papers_with_scope_hits ?? 0 }}
                </span>
                <span class="ks-type-data">papers with evidence hits</span>
              </div>
              <div class="ks-evidence-lab__coverage-item">
                <span class="ks-evidence-lab__coverage-value">
                  {{ metricNames.length }}
                </span>
                <span class="ks-type-data">matrix columns</span>
              </div>
            </div>
          </section>

          <section
            v-if="warnings.length"
            class="ks-card ks-evidence-lab__warnings"
            aria-labelledby="evidence-analysis-notes"
          >
            <div class="ks-evidence-lab__warnings-header">
              <p id="evidence-analysis-notes" class="ks-type-eyebrow">
                Analysis Notes
              </p>
              <KsTag variant="warning">{{ warnings.length }} warnings</KsTag>
            </div>
            <ul class="ks-evidence-lab__warning-list">
              <li v-for="warning in warnings" :key="warning">
                {{ warning }}
              </li>
            </ul>
          </section>

          <FiltersPanel
            :datasets="datasetOptions"
            :metrics="metricOptions"
            :active-datasets="activeDatasetIds"
            :active-metrics="activeMetricIds"
            :method-query="methodQuery"
            :visible-count="results.length"
            :total-count="methodsResponse?.matrix.rows.length ?? 0"
            @update:datasets="handleDatasetsChange"
            @update:metrics="handleMetricsChange"
            @update:method-query="handleMethodQueryChange"
            @clear="clearFilters"
          />

          <EvidenceResultsMatrix
            v-if="hasMatrixData"
            :results="results"
            :metric-names="metricNames"
            title="Cross-Paper Results Comparison"
          />
          <KsEmptyState
            v-else-if="hasAnyResults"
            title="No rows match the current filters"
            description="Try clearing one or more filters to restore method rows in the matrix."
          >
            <template #action>
              <KsButton
                v-if="hasActiveFilters"
                variant="secondary"
                @click="clearFilters"
              >
                Clear filters
              </KsButton>
            </template>
          </KsEmptyState>
          <KsEmptyState
            v-else
            title="No comparable results yet"
            description="The selected scope does not have enough normalized experiment records to render a comparison matrix."
          />

          <EvidenceContradictionsPanel
            v-if="hasContradictions"
            :contradictions="contradictions"
          />
          <KsEmptyState
            v-else
            title="No contradictions detected"
            description="No conflicting claim pairs were surfaced for the current scope."
          />

          <section class="ks-card ks-evidence-lab__ragflow">
            <span class="ks-type-eyebrow">RAGFlow Evidence Retrieval</span>
            <RagflowQAPanel
              :collection-id="activeCollectionId"
              :placeholder="qaPlaceholder"
            />
          </section>
        </template>
      </template>
    </div>
  </div>
</template>

<style scoped>
.ks-evidence-lab {
  min-height: 100vh;
  padding-bottom: 80px;
}

.ks-evidence-lab__content {
  max-width: 1040px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.ks-evidence-lab__skeleton-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.ks-evidence-lab__skeleton-header,
.ks-evidence-lab__skeleton-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ks-evidence-lab__overview {
  padding: 18px 20px 20px;
}

.ks-evidence-lab__overview-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.ks-evidence-lab__overview-copy {
  margin-top: 4px;
  color: var(--color-secondary);
  font: 400 0.875rem / 1.5 var(--font-serif);
}

.ks-evidence-lab__coverage-bar {
  margin-top: 18px;
  height: 10px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.12);
  overflow: hidden;
}

.ks-evidence-lab__coverage-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--color-primary), var(--color-accent));
}

.ks-evidence-lab__coverage-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 18px;
}

.ks-evidence-lab__coverage-item {
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.02);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ks-evidence-lab__coverage-value {
  font: 700 1.125rem / 1 var(--font-mono);
  color: var(--color-primary);
}

.ks-evidence-lab__warnings {
  padding: 18px 20px;
}

.ks-evidence-lab__warnings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.ks-evidence-lab__warning-list {
  margin: 10px 0 0;
  padding-left: 18px;
  color: var(--color-secondary);
  font: 400 0.875rem / 1.6 var(--font-serif);
}

.ks-evidence-lab__warning-list li + li {
  margin-top: 4px;
}

.ks-evidence-lab__ragflow {
  padding: 24px;
  display: grid;
  gap: 16px;
}

@media (max-width: 768px) {
  .ks-evidence-lab__skeleton-row,
  .ks-evidence-lab__coverage-grid {
    grid-template-columns: 1fr;
  }

  .ks-evidence-lab__overview-header {
    flex-direction: column;
  }
}
</style>
