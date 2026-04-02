export type AdminMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
type AdminProbeStatus = 'idle' | 'ok' | 'warning' | 'error'
type AdminProbeMode = 'safe' | 'manual' | 'mutating' | 'stream'

interface OpenApiParameter {
  name?: string
  in?: string
  required?: boolean
  description?: string
  schema?: Record<string, unknown>
}

interface OpenApiOperation {
  tags?: string[]
  summary?: string
  description?: string
  operationId?: string
  parameters?: OpenApiParameter[]
  requestBody?: {
    required?: boolean
    content?: Record<string, { schema?: Record<string, unknown>; example?: unknown }>
  }
  responses?: Record<string, unknown>
}

interface OpenApiDocument {
  openapi?: string
  info?: Record<string, unknown>
  paths?: Record<string, Partial<Record<Lowercase<AdminMethod>, OpenApiOperation>>>
}

export interface AdminEndpointParameter {
  name: string
  location: 'path' | 'query' | 'header' | 'cookie'
  required: boolean
  description: string
  schema: Record<string, unknown> | null
  defaultValue: unknown
}

export interface AdminRequestBody {
  required: boolean
  contentTypes: string[]
  schema: Record<string, unknown> | null
  example: unknown
}

export interface AdminEndpoint {
  id: string
  domain: string
  tag: string
  path: string
  method: AdminMethod
  summary: string
  description: string
  operationId: string
  parameters: AdminEndpointParameter[]
  requestBody: AdminRequestBody | null
  responseCodes: string[]
  isMutation: boolean
  isStream: boolean
  probeMode: AdminProbeMode
  autoProbeEligible: boolean
  autoProbePath: string | null
  autoProbeStatus: AdminProbeStatus
  autoProbeDetail: string
  autoProbeDurationMs: number | null
  autoProbeCode: number | null
  autoProbeAt: string | null
}

export interface AdminProbeCard {
  id: string
  title: string
  status: AdminProbeStatus
  value: string
  detail: string
  note?: string
}

export interface AdminRunnerPayload {
  pathParams: Record<string, unknown>
  query: Record<string, unknown>
  body: unknown
}

export interface AdminRunResult {
  ok: boolean
  status: number
  method: AdminMethod
  path: string
  url: string
  durationMs: number
  timestamp: string
  data: unknown
  errorMessage: string | null
}

export interface AdminQuickActionResult extends AdminRunResult {
  label: string
}

export interface AdminSampleContext {
  paperId: string | null
  collectionId: string | null
  authorId: string | null
  topicId: string | null
  tagId: string | null
  experimentId: string | null
  feedId: string | null
  alertRuleId: string | null
  searchId: string | null
  webhookId: string | null
}

export interface AdminRequestHistoryEntry {
  id: string
  label: string
  endpointId: string | null
  method: AdminMethod
  path: string
  status: number
  ok: boolean
  durationMs: number
  timestamp: string
  pathParams: Record<string, unknown>
  query: Record<string, unknown>
  body: unknown
}

export interface AdminAutoProbeQueue {
  blockedCount: number
  readyCount: number
  processedCount: number
  completedCount: number
  succeededCount: number
  failedCount: number
  queuedCount: number
  inFlightCount: number
  progressPct: number
  hasMore: boolean
  nextBatchSize: number
  batchSize: number
}

const METHOD_ORDER: Record<AdminMethod, number> = {
  GET: 0,
  POST: 1,
  PUT: 2,
  PATCH: 3,
  DELETE: 4,
}

const ROUTE_METHODS = ['get', 'post', 'put', 'patch', 'delete'] as const
const REQUEST_HISTORY_KEY = 'ks-admin-request-history'
const MAX_REQUEST_HISTORY = 12
const AUTO_PROBE_BATCH_SIZE = 24
const AUTO_PROBE_CONCURRENCY = 8
const SAFE_PROBE_KEYS = new Set<string>([
  'GET /health',
  'GET /health/services',
  'GET /api/v1/auth/me',
  'GET /api/v1/search/health',
  'GET /api/v1/ragflow/sync/status',
  'GET /api/v1/analytics/data-coverage',
])
const EXCLUDED_PATH_PREFIXES = ['/docs', '/redoc']
const SAMPLE_PARAM_MAP: Partial<Record<string, keyof AdminSampleContext>> = {
  paper_id: 'paperId',
  collection_id: 'collectionId',
  author_id: 'authorId',
  topic_id: 'topicId',
  tag_id: 'tagId',
  experiment_id: 'experimentId',
  feed_id: 'feedId',
  rule_id: 'alertRuleId',
  search_id: 'searchId',
  webhook_id: 'webhookId',
}

function humanizeIdentifier(value: string): string {
  return value
    .replace(/[_-]+/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .trim()
    .replace(/\s+/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase())
}

function inferDomainFromPath(path: string): string {
  const parts = path.split('/').filter(Boolean)

  if (parts[0] === 'api' && parts[1] === 'v1') {
    return parts[2] ?? 'api'
  }

  if (parts[0] === 'api') {
    return 'system'
  }

  return parts[0] ?? 'system'
}

function normalizeParameter(parameter: OpenApiParameter): AdminEndpointParameter | null {
  if (!parameter.name || !parameter.in) {
    return null
  }

  const schema = parameter.schema ?? null
  return {
    name: parameter.name,
    location: parameter.in as AdminEndpointParameter['location'],
    required: Boolean(parameter.required),
    description: parameter.description ?? '',
    schema,
    defaultValue: schema && 'default' in schema ? schema.default : null,
  }
}

function normalizeRequestBody(operation: OpenApiOperation): AdminRequestBody | null {
  const content = operation.requestBody?.content

  if (!content || Object.keys(content).length === 0) {
    return null
  }

  const contentTypes = Object.keys(content)
  const preferredType = content['application/json'] ? 'application/json' : contentTypes[0]!
  const preferred = content[preferredType] ?? {}

  return {
    required: Boolean(operation.requestBody?.required),
    contentTypes,
    schema: preferred.schema ?? null,
    example: preferred.example ?? null,
  }
}

function inferProbeMode(endpoint: Pick<AdminEndpoint, 'method' | 'path' | 'isMutation' | 'isStream' | 'requestBody'>): AdminProbeMode {
  const probeKey = `${endpoint.method} ${endpoint.path}`

  if (endpoint.isStream) {
    return 'stream'
  }

  if (SAFE_PROBE_KEYS.has(probeKey) || (endpoint.method === 'GET' && !endpoint.requestBody)) {
    return 'safe'
  }

  if (endpoint.isMutation) {
    return 'mutating'
  }

  return 'manual'
}

export function normalizeOpenApiCatalog(schema: OpenApiDocument): AdminEndpoint[] {
  const endpoints: AdminEndpoint[] = []

  for (const [path, pathItem] of Object.entries(schema.paths ?? {})) {
    if (EXCLUDED_PATH_PREFIXES.some(prefix => path.startsWith(prefix))) {
      continue
    }

    for (const methodKey of ROUTE_METHODS) {
      const operation = pathItem?.[methodKey]
      if (!operation) {
        continue
      }

      const method = methodKey.toUpperCase() as AdminMethod
      const isMutation = method !== 'GET'
      const isStream = path.startsWith('/api/v1/sse')
      const tag = operation.tags?.[0] ?? inferDomainFromPath(path)
      const domain = path.startsWith('/api/v1/') ? tag : 'system'
      const summary = operation.summary
        ?? (operation.operationId ? humanizeIdentifier(operation.operationId) : `${method} ${path}`)

      const endpoint: AdminEndpoint = {
        id: `${method} ${path}`,
        domain,
        tag,
        path,
        method,
        summary,
        description: operation.description ?? '',
        operationId: operation.operationId ?? `${methodKey}_${path.replace(/[/{}]/g, '_')}`,
        parameters: (operation.parameters ?? [])
          .map(normalizeParameter)
          .filter((parameter): parameter is AdminEndpointParameter => parameter !== null),
        requestBody: normalizeRequestBody(operation),
        responseCodes: Object.keys(operation.responses ?? {}),
        isMutation,
        isStream,
        probeMode: 'manual',
        autoProbeEligible: method === 'GET' && !isStream && !normalizeRequestBody(operation),
        autoProbePath: null,
        autoProbeStatus: 'idle',
        autoProbeDetail: 'Awaiting probe',
        autoProbeDurationMs: null,
        autoProbeCode: null,
        autoProbeAt: null,
      }

      endpoint.probeMode = inferProbeMode(endpoint)
      endpoints.push(endpoint)
    }
  }

  return endpoints.sort((left, right) => {
    if (left.domain !== right.domain) {
      return left.domain.localeCompare(right.domain)
    }
    if (left.path !== right.path) {
      return left.path.localeCompare(right.path)
    }
    return METHOD_ORDER[left.method] - METHOD_ORDER[right.method]
  })
}

function stringifyJson(value: unknown, fallback: string): string {
  if (value === null || value === undefined) {
    return fallback
  }

  try {
    return JSON.stringify(value, null, 2)
  }
  catch {
    return fallback
  }
}

export function createRunnerSeed(endpoint: AdminEndpoint): AdminRunnerPayload & {
  pathParamsText: string
  queryText: string
  bodyText: string
} {
  const pathParams = Object.fromEntries(
    endpoint.parameters
      .filter(parameter => parameter.location === 'path')
      .map(parameter => [parameter.name, parameter.defaultValue ?? '']),
  )

  const queryParams = Object.fromEntries(
    endpoint.parameters
      .filter(parameter => parameter.location === 'query' && parameter.defaultValue !== null)
      .map(parameter => [parameter.name, parameter.defaultValue]),
  )

  const bodyExample = endpoint.requestBody?.example
    ?? (endpoint.requestBody ? {} : null)

  return {
    pathParams,
    query: queryParams,
    body: bodyExample,
    pathParamsText: stringifyJson(pathParams, '{}'),
    queryText: stringifyJson(queryParams, '{}'),
    bodyText: endpoint.requestBody ? stringifyJson(bodyExample, '{}') : '',
  }
}

export function createHistoryRestoreSeed(entry: Pick<AdminRequestHistoryEntry, 'pathParams' | 'query' | 'body'>) {
  return {
    pathParamsText: stringifyJson(entry.pathParams, '{}'),
    queryText: stringifyJson(entry.query, '{}'),
    bodyText: entry.body === null || entry.body === undefined
      ? ''
      : stringifyJson(entry.body, '{}'),
  }
}

export function sliceAutoProbeBatch<T>(
  items: T[],
  cursor: number,
  mode: 'next' | 'all' = 'next',
  batchSize = AUTO_PROBE_BATCH_SIZE,
): { items: T[]; nextCursor: number } {
  const remaining = Math.max(items.length - cursor, 0)
  const size = mode === 'all'
    ? remaining
    : Math.min(batchSize, remaining)

  return {
    items: items.slice(cursor, cursor + size),
    nextCursor: cursor + size,
  }
}

function parseJsonInput(input: string, emptyValue: unknown): unknown {
  const trimmed = input.trim()
  if (!trimmed) {
    return emptyValue
  }
  return JSON.parse(trimmed)
}

function firstIdFromCollection(
  input: unknown,
  keys: string[] = ['id'],
): string | null {
  if (!input) {
    return null
  }

  if (Array.isArray(input)) {
    for (const item of input) {
      const id = firstIdFromCollection(item, keys)
      if (id) {
        return id
      }
    }
    return null
  }

  if (typeof input !== 'object') {
    return null
  }

  const record = input as Record<string, unknown>

  for (const key of keys) {
    const value = record[key]
    if (typeof value === 'string' && value) {
      return value
    }
  }

  return null
}

function summarizeErrorPayload(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object') {
    return fallback
  }

  const record = payload as Record<string, unknown>
  const detail = record.detail
  if (typeof detail === 'string' && detail) {
    return detail
  }
  const message = record.message
  if (typeof message === 'string' && message) {
    return message
  }
  const code = record.code
  if (typeof code === 'string' && code) {
    return code
  }
  return fallback
}

function canAutoProbe(endpoint: AdminEndpoint): boolean {
  return endpoint.probeMode === 'safe' && endpoint.autoProbeEligible
}

export function resolveAutoProbePath(
  endpoint: AdminEndpoint,
  samples: AdminSampleContext,
): { path: string | null; detail: string } {
  if (!canAutoProbe(endpoint)) {
    return {
      path: null,
      detail: endpoint.probeMode === 'mutating'
        ? 'Mutation routes are excluded from automatic probes'
        : endpoint.probeMode === 'stream'
            ? 'Stream routes require manual inspection'
            : 'Not eligible for automatic probing',
    }
  }

  const pathParams: Record<string, unknown> = {}
  const missing: string[] = []

  for (const parameter of endpoint.parameters) {
    if (parameter.location === 'path') {
      const sampleKey = SAMPLE_PARAM_MAP[parameter.name]
      const sampleValue = sampleKey ? samples[sampleKey] : null
      if (!sampleValue) {
        missing.push(parameter.name)
        continue
      }
      pathParams[parameter.name] = sampleValue
      continue
    }

    if (parameter.location === 'query' && parameter.required && parameter.defaultValue === null) {
      missing.push(parameter.name)
    }
  }

  if (missing.length > 0) {
    return {
      path: null,
      detail: `Missing sample values for ${missing.join(', ')}`,
    }
  }

  const requiredQueryDefaults = Object.fromEntries(
    endpoint.parameters
      .filter(parameter => parameter.location === 'query' && parameter.defaultValue !== null)
      .map(parameter => [parameter.name, parameter.defaultValue]),
  )

  const resolvedPath = appendQuery(
    replacePathParams(endpoint.path, pathParams),
    requiredQueryDefaults,
  )

  return {
    path: resolvedPath,
    detail: pathParams && Object.keys(pathParams).length > 0
      ? `Auto probe uses sampled identifiers`
      : 'Auto probe uses the route directly',
  }
}

function replacePathParams(path: string, params: Record<string, unknown>): string {
  return path.replace(/\{([^}]+)\}/g, (_, key: string) => {
    const value = params[key]
    return encodeURIComponent(value === undefined || value === null ? '' : String(value))
  })
}

function appendQuery(path: string, query: Record<string, unknown>): string {
  const url = new URL(path, 'http://placeholder.local')

  for (const [key, rawValue] of Object.entries(query)) {
    if (rawValue === '' || rawValue === null || rawValue === undefined) {
      continue
    }

    if (Array.isArray(rawValue)) {
      for (const item of rawValue) {
        url.searchParams.append(key, String(item))
      }
      continue
    }

    if (typeof rawValue === 'object') {
      url.searchParams.set(key, JSON.stringify(rawValue))
      continue
    }

    url.searchParams.set(key, String(rawValue))
  }

  return `${url.pathname}${url.search}`
}

function summarizeServiceMatrix(services: Record<string, string> | undefined): Pick<AdminProbeCard, 'status' | 'value' | 'detail'> {
  const pairs = Object.entries(services ?? {})

  if (pairs.length === 0) {
    return {
      status: 'warning',
      value: '0/0',
      detail: 'No dependency services reported',
    }
  }

  const okCount = pairs.filter(([, value]) => value === 'ok').length
  const hasHardFailure = pairs.some(([, value]) => value.startsWith('error'))

  return {
    status: hasHardFailure ? 'error' : okCount === pairs.length ? 'ok' : 'warning',
    value: `${okCount}/${pairs.length}`,
    detail: pairs.map(([name, value]) => `${name}: ${value}`).join(' · '),
  }
}

function statusFromCoverage(fields: Array<{ pct: number }> | undefined): AdminProbeStatus {
  if (!fields || fields.length === 0) {
    return 'warning'
  }

  const avgCoverage = fields.reduce((sum, field) => sum + field.pct, 0) / fields.length
  if (avgCoverage >= 80) return 'ok'
  if (avgCoverage >= 45) return 'warning'
  return 'error'
}

export function useAdminConsole() {
  const config = useRuntimeConfig()

  const endpoints = ref<AdminEndpoint[]>([])
  const catalogPending = ref(false)
  const catalogError = ref<string | null>(null)

  const probes = ref<AdminProbeCard[]>([])
  const probesPending = ref(false)
  const lastLoadedAt = ref<string | null>(null)

  const samples = ref<AdminSampleContext>({
    paperId: null,
    collectionId: null,
    authorId: null,
    topicId: null,
    tagId: null,
    experimentId: null,
    feedId: null,
    alertRuleId: null,
    searchId: null,
    webhookId: null,
  })

  const selectedEndpointId = ref<string | null>(null)
  const registryQuery = ref('')
  const activeDomain = ref<'all' | string>('all')
  const activeMethod = ref<'all' | AdminMethod>('all')

  const runnerPending = ref(false)
  const runnerResult = ref<AdminRunResult | null>(null)
  const requestHistory = ref<AdminRequestHistoryEntry[]>([])
  const runnerRestoreEntry = ref<AdminRequestHistoryEntry | null>(null)
  const quickActionPending = ref(false)
  const quickActionResult = ref<AdminQuickActionResult | null>(null)
  const routeProbePending = ref(false)
  const routeProbeCursor = ref(0)
  const routeProbeReadyIds = ref<string[]>([])
  const routeProbeGeneration = ref(0)

  function loadHistory() {
    if (!import.meta.client) {
      return
    }

    try {
      const raw = localStorage.getItem(REQUEST_HISTORY_KEY)
      if (!raw) {
        return
      }
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed)) {
        requestHistory.value = parsed as AdminRequestHistoryEntry[]
      }
    }
    catch {
      requestHistory.value = []
    }
  }

  function persistHistory() {
    if (!import.meta.client) {
      return
    }

    try {
      localStorage.setItem(REQUEST_HISTORY_KEY, JSON.stringify(requestHistory.value))
    }
    catch {
      // Ignore storage failures in restricted browser contexts.
    }
  }

  function recordHistory(
    label: string,
    result: AdminRunResult,
    payload: AdminRunnerPayload,
    endpointId: string | null,
  ) {
    requestHistory.value = [
      {
        id: `${result.timestamp}-${Math.random().toString(36).slice(2, 8)}`,
        label,
        endpointId,
        method: result.method,
        path: result.path,
        status: result.status,
        ok: result.ok,
        durationMs: result.durationMs,
        timestamp: result.timestamp,
        pathParams: payload.pathParams,
        query: payload.query,
        body: payload.body,
      },
      ...requestHistory.value,
    ].slice(0, MAX_REQUEST_HISTORY)
    persistHistory()
  }

  function authHeaders(includeJson = false): Record<string, string> {
    const headers: Record<string, string> = {
      Accept: 'application/json',
    }

    if (includeJson) {
      headers['Content-Type'] = 'application/json'
    }

    if (import.meta.client) {
      const token = localStorage.getItem('ks_access_token')
      if (token && token !== 'single-user-mode') {
        headers.Authorization = `Bearer ${token}`
      }
    }

    return headers
  }

  async function requestRaw(
    path: string,
    options: {
      method?: AdminMethod | 'GET'
      body?: unknown
    } = {},
  ): Promise<AdminRunResult> {
    const startedAt = Date.now()
    const targetUrl = `${config.public.apiUrl}${path}`

    try {
      const response = await $fetch.raw(targetUrl, {
        method: options.method ?? 'GET',
        body: options.body as BodyInit | Record<string, unknown> | null | undefined,
        headers: authHeaders(options.body !== undefined),
      })

      return {
        ok: response.status < 400,
        status: response.status,
        method: (options.method ?? 'GET') as AdminMethod,
        path,
        url: targetUrl,
        durationMs: Date.now() - startedAt,
        timestamp: new Date().toISOString(),
        data: response._data,
        errorMessage: null,
      }
    }
    catch (error: unknown) {
      const fetchError = error as {
        message?: string
        data?: unknown
        response?: { status?: number; _data?: unknown }
      }

      return {
        ok: false,
        status: fetchError.response?.status ?? 0,
        method: (options.method ?? 'GET') as AdminMethod,
        path,
        url: targetUrl,
        durationMs: Date.now() - startedAt,
        timestamp: new Date().toISOString(),
        data: fetchError.response?._data ?? fetchError.data ?? null,
        errorMessage: fetchError.message ?? 'Request failed',
      }
    }
  }

  async function loadCatalog() {
    catalogPending.value = true
    catalogError.value = null

    const result = await requestRaw('/api/openapi.json')
    if (!result.ok) {
      catalogError.value = result.errorMessage ?? `Failed to load OpenAPI (${result.status})`
      endpoints.value = []
      catalogPending.value = false
      return
    }

    endpoints.value = normalizeOpenApiCatalog(result.data as OpenApiDocument)
    selectedEndpointId.value = selectedEndpointId.value && endpoints.value.some(endpoint => endpoint.id === selectedEndpointId.value)
      ? selectedEndpointId.value
      : (endpoints.value.find(endpoint => endpoint.id === 'GET /health')?.id ?? endpoints.value[0]?.id ?? null)
    catalogPending.value = false
  }

  async function loadSamples() {
    const [
      paperResult,
      collectionResult,
      authorResult,
      topicResult,
      tagResult,
      experimentResult,
      feedResult,
      alertRuleResult,
      searchResult,
      webhookResult,
    ] = await Promise.all([
      requestRaw('/api/v1/papers?page=1&per_page=1'),
      requestRaw('/api/v1/collections'),
      requestRaw('/api/v1/researchers/emerging?top_k=1'),
      requestRaw('/api/v1/trends/topics?limit=1'),
      requestRaw('/api/v1/tags'),
      requestRaw('/api/v1/experiments?limit=1'),
      requestRaw('/api/v1/feeds'),
      requestRaw('/api/v1/alerts/rules'),
      requestRaw('/api/v1/governance/searches'),
      requestRaw('/api/v1/governance/webhooks'),
    ])

    samples.value = {
      paperId: paperResult.ok
        ? ((paperResult.data as { items?: Array<{ id?: string }> }).items?.[0]?.id ?? null)
        : null,
      collectionId: collectionResult.ok
        ? ((collectionResult.data as Array<{ id?: string }>)?.[0]?.id ?? null)
        : null,
      authorId: authorResult.ok
        ? firstIdFromCollection((authorResult.data as { authors?: unknown[] } | undefined)?.authors, ['id', 'author_id'])
        : null,
      topicId: topicResult.ok
        ? firstIdFromCollection((topicResult.data as { topics?: unknown[] } | undefined)?.topics)
        : null,
      tagId: tagResult.ok
        ? firstIdFromCollection(tagResult.data)
        : null,
      experimentId: experimentResult.ok
        ? firstIdFromCollection(experimentResult.data)
        : null,
      feedId: feedResult.ok
        ? firstIdFromCollection((feedResult.data as { items?: unknown[] } | undefined)?.items)
        : null,
      alertRuleId: alertRuleResult.ok
        ? firstIdFromCollection((alertRuleResult.data as { rules?: unknown[] } | undefined)?.rules)
        : null,
      searchId: searchResult.ok
        ? firstIdFromCollection(searchResult.data)
        : null,
      webhookId: webhookResult.ok
        ? firstIdFromCollection(webhookResult.data)
        : null,
    }
  }

  function findEndpoint(endpointId: string | null) {
    if (!endpointId) {
      return null
    }

    return endpoints.value.find(endpoint => endpoint.id === endpointId) ?? null
  }

  function initializeRouteProbes() {
    routeProbeGeneration.value += 1
    routeProbeCursor.value = 0
    routeProbeReadyIds.value = []
    routeProbePending.value = false

    const candidates = endpoints.value.filter(endpoint => canAutoProbe(endpoint))

    for (const endpoint of candidates) {
      const target = resolveAutoProbePath(endpoint, samples.value)
      endpoint.autoProbePath = target.path
      endpoint.autoProbeDetail = target.detail
      endpoint.autoProbeDurationMs = null
      endpoint.autoProbeCode = null
      endpoint.autoProbeAt = null
      endpoint.autoProbeStatus = target.path ? 'idle' : 'warning'
    }
    routeProbeReadyIds.value = candidates
      .filter(endpoint => endpoint.autoProbePath)
      .map(endpoint => endpoint.id)
  }

  async function loadRouteProbes(mode: 'next' | 'all' = 'next') {
    if (routeProbePending.value) {
      return
    }

    const generation = routeProbeGeneration.value
    const batch = sliceAutoProbeBatch(routeProbeReadyIds.value, routeProbeCursor.value, mode)

    if (batch.items.length === 0) {
      return
    }

    routeProbeCursor.value = batch.nextCursor
    routeProbePending.value = true

    try {
      for (let index = 0; index < batch.items.length; index += AUTO_PROBE_CONCURRENCY) {
        const endpointIds = batch.items.slice(index, index + AUTO_PROBE_CONCURRENCY)

        await Promise.all(endpointIds.map(async endpointId => {
          const endpoint = findEndpoint(endpointId)
          if (!endpoint?.autoProbePath || generation !== routeProbeGeneration.value) {
            return
          }

          const result = await requestRaw(endpoint.autoProbePath)

          if (generation !== routeProbeGeneration.value) {
            return
          }

          endpoint.autoProbeStatus = result.ok ? 'ok' : 'error'
          endpoint.autoProbeDurationMs = result.durationMs
          endpoint.autoProbeCode = result.status
          endpoint.autoProbeAt = result.timestamp
          endpoint.autoProbeDetail = result.ok
            ? `HTTP ${result.status} in ${result.durationMs} ms`
            : summarizeErrorPayload(
                result.data,
                result.errorMessage ?? `HTTP ${result.status}`,
              )
        }))
      }
    }
    finally {
      if (generation === routeProbeGeneration.value) {
        routeProbePending.value = false
      }
    }
  }

  async function loadProbes() {
    probesPending.value = true

    const [healthResult, servicesResult, authResult, searchResult, ragflowResult, coverageResult] = await Promise.all([
      requestRaw('/health'),
      requestRaw('/health/services'),
      requestRaw('/api/v1/auth/me'),
      requestRaw('/api/v1/search/health'),
      requestRaw('/api/v1/ragflow/sync/status'),
      requestRaw('/api/v1/analytics/data-coverage'),
    ])

    const serviceSummary = summarizeServiceMatrix(
      (servicesResult.data as { services?: Record<string, string> } | undefined)?.services,
    )
    const searchHealth = searchResult.data as {
      keyword?: string
      semantic?: string
      degraded_mode?: boolean
    } | undefined
    const ragflowHealth = ragflowResult.data as {
      enabled?: boolean
      health?: { status?: string; error?: string } | null
      counts?: { stale_mappings?: number; total_mappings?: number }
      freshness_minutes?: number
    } | undefined
    const coverage = coverageResult.data as {
      total_papers?: number
      fields?: Array<{ field: string; pct: number }>
      institution_coverage_note?: string
    } | undefined
    const authMe = authResult.data as { mode?: string; user_id?: string } | undefined

    probes.value = [
      {
        id: 'api',
        title: 'API Server',
        status: healthResult.ok && (healthResult.data as { status?: string })?.status === 'ok' ? 'ok' : 'error',
        value: healthResult.ok ? String((healthResult.data as { version?: string })?.version ?? 'up') : 'down',
        detail: healthResult.ok
          ? `Status ${(healthResult.data as { status?: string })?.status ?? 'unknown'}`
          : (healthResult.errorMessage ?? `HTTP ${healthResult.status}`),
        note: `${healthResult.durationMs} ms`,
      },
      {
        id: 'services',
        title: 'Dependencies',
        status: servicesResult.ok ? serviceSummary.status : 'error',
        value: servicesResult.ok ? serviceSummary.value : '0/0',
        detail: servicesResult.ok
          ? serviceSummary.detail
          : (servicesResult.errorMessage ?? `HTTP ${servicesResult.status}`),
        note: servicesResult.ok ? 'Derived from /health/services' : undefined,
      },
      {
        id: 'auth',
        title: 'Auth Mode',
        status: authResult.ok ? 'ok' : 'warning',
        value: authResult.ok ? String(authMe?.mode ?? 'unknown') : 'unverified',
        detail: authResult.ok
          ? `Current user ${authMe?.user_id ?? 'unknown'}`
          : (authResult.errorMessage ?? `HTTP ${authResult.status}`),
      },
      {
        id: 'search',
        title: 'Search Stack',
        status: !searchResult.ok
          ? 'error'
          : searchHealth?.degraded_mode
              ? 'warning'
              : 'ok',
        value: searchResult.ok
          ? `${searchHealth?.keyword ?? 'unknown'} / ${searchHealth?.semantic ?? 'unknown'}`
          : 'offline',
        detail: searchResult.ok
          ? searchHealth?.degraded_mode
              ? 'Keyword or semantic search is degraded'
              : 'Keyword and semantic search are available'
          : (searchResult.errorMessage ?? `HTTP ${searchResult.status}`),
      },
      {
        id: 'ragflow',
        title: 'RAGFlow',
        status: !ragflowResult.ok
          ? 'error'
          : ragflowHealth?.enabled
              ? ragflowHealth.health?.status === 'ok'
                  ? 'ok'
                  : 'warning'
              : 'warning',
        value: ragflowResult.ok
          ? ragflowHealth?.enabled
              ? String(ragflowHealth.health?.status ?? 'enabled')
              : 'disabled'
          : 'offline',
        detail: ragflowResult.ok
          ? ragflowHealth?.enabled
              ? `${ragflowHealth.counts?.stale_mappings ?? 0} stale / ${ragflowHealth.counts?.total_mappings ?? 0} mapped`
              : 'Sync pipeline is disabled in settings'
          : (ragflowResult.errorMessage ?? `HTTP ${ragflowResult.status}`),
        note: ragflowHealth?.enabled
          ? `Freshness ${ragflowHealth.freshness_minutes ?? '?'} min`
          : undefined,
      },
      {
        id: 'coverage',
        title: 'Data Coverage',
        status: coverageResult.ok ? statusFromCoverage(coverage?.fields) : 'error',
        value: coverageResult.ok
          ? `${coverage?.total_papers ?? 0} papers`
          : 'offline',
        detail: coverageResult.ok
          ? coverage?.institution_coverage_note ?? 'Coverage matrix loaded'
          : (coverageResult.errorMessage ?? `HTTP ${coverageResult.status}`),
        note: coverageResult.ok && coverage?.fields
          ? coverage.fields.slice(0, 3).map(field => `${field.field} ${field.pct}%`).join(' · ')
          : undefined,
      },
    ]

    lastLoadedAt.value = new Date().toISOString()
    probesPending.value = false
  }

  async function refreshAll() {
    await Promise.all([loadCatalog(), loadSamples()])
    initializeRouteProbes()
    await Promise.all([loadProbes(), loadRouteProbes()])
  }

  const domainOptions = computed(() => {
    return ['all', ...new Set(endpoints.value.map(endpoint => endpoint.domain))] as Array<'all' | string>
  })

  const summary = computed(() => {
    const domainCount = new Set(endpoints.value.map(endpoint => endpoint.domain)).size
    const autoCandidates = endpoints.value.filter(endpoint => endpoint.probeMode === 'safe').length
    const autoVerified = endpoints.value.filter(endpoint => endpoint.autoProbeStatus === 'ok').length
    const autoFailing = endpoints.value.filter(endpoint => endpoint.autoProbeStatus === 'error').length
    const blockedAuto = endpoints.value.filter(
      endpoint => endpoint.probeMode === 'safe' && endpoint.autoProbeStatus === 'warning' && !endpoint.autoProbePath,
    ).length
    return {
      totalRoutes: endpoints.value.length,
      domainCount,
      autoCandidates,
      autoVerified,
      autoFailing,
      blockedAuto,
      manualOnly: endpoints.value.filter(endpoint => endpoint.probeMode !== 'safe').length,
    }
  })

  const filteredEndpoints = computed(() => {
    const query = registryQuery.value.trim().toLowerCase()

    return endpoints.value.filter(endpoint => {
      if (activeDomain.value !== 'all' && endpoint.domain !== activeDomain.value) {
        return false
      }

      if (activeMethod.value !== 'all' && endpoint.method !== activeMethod.value) {
        return false
      }

      if (!query) {
        return true
      }

      return [
        endpoint.path,
        endpoint.summary,
        endpoint.description,
        endpoint.domain,
        endpoint.tag,
        endpoint.operationId,
      ].some(value => value.toLowerCase().includes(query))
    })
  })

  const groupedEndpoints = computed(() => {
    return filteredEndpoints.value.reduce<Record<string, AdminEndpoint[]>>((groups, endpoint) => {
      groups[endpoint.domain] ||= []
      groups[endpoint.domain]!.push(endpoint)
      return groups
    }, {})
  })

  const selectedEndpoint = computed(() => {
    return endpoints.value.find(endpoint => endpoint.id === selectedEndpointId.value) ?? null
  })

  const selectedEndpointHistory = computed(() => {
    if (!selectedEndpointId.value) {
      return requestHistory.value.slice(0, 6)
    }

    return requestHistory.value
      .filter(entry => entry.endpointId === selectedEndpointId.value)
      .slice(0, 6)
  })

  const crossEndpointHistory = computed(() => {
    return requestHistory.value
      .filter(entry => entry.endpointId && entry.endpointId !== selectedEndpointId.value)
      .slice(0, 6)
  })

  const autoProbeQueue = computed<AdminAutoProbeQueue>(() => {
    const readyCount = endpoints.value.filter(
      endpoint => endpoint.probeMode === 'safe' && Boolean(endpoint.autoProbePath),
    ).length
    const blockedCount = endpoints.value.filter(
      endpoint => endpoint.probeMode === 'safe' && !endpoint.autoProbePath,
    ).length
    const succeededCount = endpoints.value.filter(endpoint => endpoint.autoProbeStatus === 'ok').length
    const failedCount = endpoints.value.filter(endpoint => endpoint.autoProbeStatus === 'error').length
    const completedCount = succeededCount + failedCount
    const processedCount = Math.min(routeProbeCursor.value, readyCount)
    const queuedCount = Math.max(readyCount - processedCount, 0)
    const inFlightCount = Math.max(processedCount - completedCount, 0)
    const nextBatchSize = Math.min(AUTO_PROBE_BATCH_SIZE, queuedCount)

    return {
      blockedCount,
      readyCount,
      processedCount,
      completedCount,
      succeededCount,
      failedCount,
      queuedCount,
      inFlightCount,
      progressPct: readyCount === 0 ? 100 : Math.round((processedCount / readyCount) * 100),
      hasMore: queuedCount > 0,
      nextBatchSize,
      batchSize: AUTO_PROBE_BATCH_SIZE,
    }
  })

  async function runQuickAction(
    label: string,
    path: string,
    options: {
      method?: AdminMethod
      body?: unknown
    } = {},
    historyContext: Partial<AdminRunnerPayload> & { endpointId?: string | null } = {},
  ) {
    quickActionPending.value = true
    const result = await requestRaw(path, {
      method: options.method ?? 'GET',
      body: options.body,
    })
    recordHistory(
      label,
      result,
      {
        pathParams: historyContext.pathParams ?? {},
        query: historyContext.query ?? {},
        body: historyContext.body ?? options.body ?? null,
      },
      historyContext.endpointId ?? null,
    )
    quickActionResult.value = { ...result, label }
    quickActionPending.value = false
    return result
  }

  async function runEndpoint(endpoint: AdminEndpoint, payload: AdminRunnerPayload) {
    runnerPending.value = true

    const withPathParams = replacePathParams(endpoint.path, payload.pathParams)
    const finalPath = appendQuery(withPathParams, payload.query)
    const body = endpoint.method === 'GET' || payload.body === null || payload.body === undefined
      ? undefined
      : payload.body

    const result = await requestRaw(finalPath, {
      method: endpoint.method,
      body,
    })
    recordHistory(endpoint.summary, result, payload, endpoint.id)
    runnerResult.value = result
    runnerPending.value = false
    return result
  }

  async function runNextRouteProbeBatch() {
    await loadRouteProbes('next')
  }

  async function runAllRouteProbes() {
    await loadRouteProbes('all')
  }

  async function restoreHistoryEntry(entry: AdminRequestHistoryEntry) {
    const endpoint = findEndpoint(entry.endpointId)

    if (!endpoint) {
      return false
    }

    selectedEndpointId.value = endpoint.id
    await nextTick()
    runnerRestoreEntry.value = { ...entry }
    return true
  }

  function clearRunnerRestoreEntry() {
    runnerRestoreEntry.value = null
  }

  onMounted(() => {
    loadHistory()
    refreshAll()
  })

  return {
    endpoints,
    catalogPending,
    catalogError,
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
    quickActionPending,
    quickActionResult,
    requestHistory,
    runnerRestoreEntry,
    selectedEndpointHistory,
    crossEndpointHistory,
    routeProbePending,
    autoProbeQueue,
    domainOptions,
    summary,
    filteredEndpoints,
    groupedEndpoints,
    selectedEndpoint,
    parseJsonInput,
    createRunnerSeed,
    loadCatalog,
    loadSamples,
    loadProbes,
    refreshAll,
    runQuickAction,
    runEndpoint,
    runNextRouteProbeBatch,
    runAllRouteProbes,
    restoreHistoryEntry,
    clearRunnerRestoreEntry,
  }
}
