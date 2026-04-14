/**
 * useApi — typed, reactive wrapper around Kaleidoscope backend.
 *
 * Uses Nuxt's `useFetch` with the runtime API URL.
 * Provides paper CRUD, content, collections, and search.
 */

// ─── Types ─────────────────────────────────────────────────────

export interface PaperLabels {
  domain: string[]
  task: string[]
  method: string[]
  data_object: string[]
  application: string[]
  meta: {
    paper_type: string[]
    evaluation_quality: string[]
    resource_constraint: string[]
  }
}

export interface Paper {
  id: string
  title: string
  abstract?: string | null
  doi?: string | null
  arxiv_id?: string | null
  published_at?: string | null
  venue?: string | null
  citation_count?: number | null
  reading_status?: string
  has_full_text?: boolean
  ingestion_status?: string
  remote_urls?: Array<{ url: string; source: string; type: string }>
  raw_metadata?: Record<string, unknown> | null
  keywords?: string[]
  summary?: string | null
  highlights?: string[]
  contributions?: string[]
  limitations?: string[]
  paper_labels?: PaperLabels | null
}

export interface PaperListResponse {
  items: Paper[]
  total: number
  page: number
  per_page: number
}

export interface SearchHit {
  paper_id: string
  doi?: string | null
  arxiv_id?: string | null
  title: string
  abstract?: string | null
  published_at?: string | null
  citation_count?: number | null
  authors: string[]
  venue?: string | null
  score: number
  highlights?: Record<string, string[]> | null
}

export interface SearchResponse {
  hits: SearchHit[]
  total: number
  page: number
  per_page: number
  query: string
  mode: string
  processing_time_ms: number
}

export interface HealthResponse {
  status: string
  version?: string
  timestamp?: string
  services?: Record<string, string>
}

export interface SearchHealthResponse {
  keyword: string
  semantic: string
  degraded_mode: boolean
}

export interface RecentPaperQueueItem {
  id: string
  title: string
  time: string
  mode: string
}

export interface Collection {
  id: string
  name: string
  description?: string | null
  kind?: 'workspace' | 'subscription_collection' | 'paper_group'
  paper_count?: number | null
  color?: string | null
  icon?: string | null
  parent_collection_id?: string | null
  is_smart?: boolean
  created_at?: string
  updated_at?: string
}

export interface Feed {
  id: string
  url: string
  name: string
  publisher?: string | null
  category?: string | null
  is_active: boolean
  last_polled_at?: string | null
  poll_error_count: number
  total_items_discovered: number
  pdf_capability?: string | null
  created_at: string
}

export interface CollectionFeedSubscription {
  id: string
  feed_id: string
  collection_id: string
  feed_name?: string | null
  publisher?: string | null
  category?: string | null
  created_at: string
}

export interface CollectionChatThread {
  id: string
  collection_id: string
  user_id: string
  title?: string | null
  created_at: string
  updated_at?: string | null
}

export interface CollectionChatMessage {
  id: string
  thread_id: string
  user_id: string
  role: string
  content: string
  sources?: { items?: Array<Record<string, unknown>> } | null
  metadata_json?: Record<string, unknown> | null
  created_at: string
}

export interface PaperContent {
  paper_id: string
  title: string | null
  abstract: string | null
  has_full_text: boolean
  markdown: string
  format: 'markdown' | 'reconstructed' | 'abstract_only' | 'metadata_only'
  remote_urls?: Array<{ url: string; source: string; type: string }> | null
  markdown_provenance?: Record<string, unknown> | null
  sections: Array<{
    title: string
    level: number
    paragraphs: string[]
  }>
  figures: Array<{
    figure_id?: string
    caption?: string
    image_url?: string
    page?: number
  }>
}

export interface PaperHighlights {
  paper_id: string
  highlights: string[]
  contributions: string[]
  limitations: string[]
  has_analysis: boolean
}

export interface BackendClaim {
  id: string
  claim_text: string
  category: string
  confidence: number
  status: string
}

export interface BackendSimilarPaper {
  paper_id: string
  title: string
  score: number
  doi?: string | null
}

export interface ImportUrlRequest {
  url: string
  title?: string
  is_html?: boolean
}

export interface ImportUrlResponse {
  paper_id: string
  title: string
  status: string
  error?: string | null
  markdown_length?: number | null
  sections?: number | null
  references?: number | null
}

export interface ImportStatusResponse {
  paper_id: string
  title?: string | null
  ingestion_status: string
  has_full_text: boolean
  created_at?: string | null
  updated_at?: string | null
  error_message?: string | null
}

export interface Comment {
  id: string
  paper_id: string
  user_id: string
  content: string
  created_at: string
}

export interface Task {
  id: string
  title: string
  description?: string
  completed: boolean
  created_at: string
}

export interface Alert {
  id: string
  title: string
  message: string
  is_read: boolean
  created_at: string
  alert_type?: string
}

export interface AlertRule {
  id: string
  name: string
  condition: string
  is_active: boolean
}

export interface GraphStats {
  paper_count: number
  citation_count: number
  author_count: number
}

export interface ContradictionPair {
  id: string
  claimA: { id?: string, text: string, paper_id?: string, paper?: string, year?: number }
  claimB: { id?: string, text: string, paper_id?: string, paper?: string, year?: number }
  severity: 'high' | 'medium' | 'low'
  resolved: boolean
}

export interface WritingDocument {
  id: string
  user_id: string
  title: string
  markdown_content: string
  plain_text_excerpt: string
  word_count: number
  cover_image_url?: string | null
  created_at: string
  updated_at: string
  last_opened_at?: string | null
}

export interface WritingDocumentListResponse {
  items: WritingDocument[]
  total: number
}

export interface WritingDocumentUpdateInput {
  title?: string
  markdown_content?: string
}

export interface WritingImageUploadResponse {
  url: string
  width?: number | null
  height?: number | null
  alt?: string | null
}

// ─── Composable ────────────────────────────────────────────────

export function useApi() {
  const config = useRuntimeConfig()
  const baseUrl = `${config.public.apiUrl}/api/v1`

  /**
   * Typed fetch helper with error handling.
   */
  async function apiFetch<T>(
    path: string,
    options: Parameters<typeof $fetch>[1] = {},
  ): Promise<T> {
    const token = import.meta.client ? localStorage.getItem('ks_access_token') : null
    const isFormDataBody = typeof FormData !== 'undefined' && options.body instanceof FormData
    const baseHeaders: Record<string, string> = {
      ...(token && token !== 'single-user-mode'
        ? { Authorization: `Bearer ${token}` }
        : {}),
      ...((options.headers as Record<string, string> | undefined) ?? {}),
    }
    const headers = isFormDataBody
      ? baseHeaders
      : { 'Content-Type': 'application/json', ...baseHeaders }
    return await $fetch<T>(`${baseUrl}${path}`, {
      ...options,
      headers,
    })
  }

  async function rawFetch<T>(
    path: string,
    options: Parameters<typeof $fetch>[1] = {},
  ): Promise<T> {
    return $fetch<T>(`${config.public.apiUrl}${path}`, options)
  }

  // ── Papers ──────────────────────────────────────────────────

  async function listPapers(params?: {
    limit?: number
    offset?: number
  }): Promise<PaperListResponse> {
    const query = new URLSearchParams()
    if (params?.limit) query.set('per_page', String(params.limit))
    if (params?.limit && params?.offset !== undefined) {
      query.set('page', String(Math.floor(params.offset / params.limit) + 1))
    }
    const qs = query.toString()
    return apiFetch(`/papers${qs ? `?${qs}` : ''}`)
  }

  async function getPaper(paperId: string): Promise<Paper> {
    return apiFetch(`/papers/${paperId}`)
  }

  async function getClaimsForPaper(
    paperId: string,
  ): Promise<{ claims: BackendClaim[] }> {
    return apiFetch(`/claims/papers/${paperId}`)
  }

  async function listRecentPapers(): Promise<RecentPaperQueueItem[]> {
    const response = await apiFetch<PaperListResponse>(
      '/papers?page=1&per_page=5&sort_by=created_at&order=desc',
    )

    return response.items.map(paper => ({
      id: paper.id,
      title: paper.title,
      time: '~10 min',
      mode: 'read',
    }))
  }

  // ── Paper Content (Markdown) ────────────────────────────────

  async function getPaperContent(paperId: string): Promise<PaperContent> {
    return apiFetch(`/papers/${paperId}/content`)
  }

  async function importFromUrl(req: ImportUrlRequest): Promise<ImportUrlResponse> {
    return apiFetch('/papers/import-url', {
      method: 'POST',
      body: req,
    })
  }

  async function reparsePaper(
    paperId: string,
    req?: { url?: string; is_html?: boolean },
  ): Promise<ImportUrlResponse> {
    return apiFetch(`/papers/${paperId}/reparse`, {
      method: 'POST',
      body: req || {},
    })
  }

  async function getImportStatus(paperId: string): Promise<ImportStatusResponse> {
    return apiFetch(`/papers/${paperId}/import-status`)
  }

  async function importPaper(req: {
    identifier: string
    identifier_type: 'doi' | 'arxiv' | 'pmid' | 'url' | 'title'
  }): Promise<{ paper_id: string | null; identifier: string; status: string; message: string | null }> {
    return apiFetch('/papers/import', {
      method: 'POST',
      body: req,
    })
  }

  // ── Search ──────────────────────────────────────────────────

  async function searchPapers(
    query: string,
    params?: { mode?: string; page?: number; per_page?: number },
  ): Promise<SearchResponse> {
    const searchParams = new URLSearchParams({ q: query })
    if (params?.mode) searchParams.set('mode', params.mode)
    if (params?.page !== undefined) searchParams.set('page', String(params.page))
    if (params?.per_page !== undefined) {
      searchParams.set('per_page', String(params.per_page))
    }
    return apiFetch(`/search?${searchParams.toString()}`)
  }

  async function getHealth(): Promise<HealthResponse> {
    return rawFetch('/health')
  }

  async function getSearchHealth(): Promise<SearchHealthResponse> {
    return rawFetch('/api/v1/search/health')
  }

  // ── Collections ─────────────────────────────────────────────

  async function listCollections(params?: {
    kind?: Collection['kind']
    parentCollectionId?: string
  }): Promise<Collection[]> {
    const searchParams = new URLSearchParams()
    if (params?.kind) searchParams.set('kind', params.kind)
    if (params?.parentCollectionId) {
      searchParams.set('parent_collection_id', params.parentCollectionId)
    }
    const qs = searchParams.toString()
    return apiFetch(`/collections${qs ? `?${qs}` : ''}`)
  }

  async function createCollection(req: {
    name: string
    description?: string
    kind?: Collection['kind']
    parent_collection_id?: string
    color?: string
    icon?: string
  }): Promise<Collection> {
    return apiFetch('/collections', {
      method: 'POST',
      body: req,
    })
  }

  async function getCollection(collectionId: string): Promise<Collection> {
    return apiFetch(`/collections/${collectionId}`)
  }

  async function getCollectionPapers(collectionId: string): Promise<{ papers: Paper[] }> {
    const papers = await apiFetch<Array<Paper & { paper_id?: string }>>(
      `/collections/${collectionId}/papers`,
    )
    return {
      papers: papers.map(paper => ({ ...paper, id: paper.id || paper.paper_id || '' })),
    }
  }

  async function addPapersToCollection(
    collectionId: string,
    paperIds: string[],
    note?: string,
  ): Promise<{ added: number; total: number }> {
    return apiFetch(`/collections/${collectionId}/papers`, {
      method: 'POST',
      body: { paper_ids: paperIds, note },
    })
  }

  async function listCollectionChildren(
    collectionId: string,
    params?: { kind?: Collection['kind'] },
  ): Promise<Collection[]> {
    const searchParams = new URLSearchParams()
    if (params?.kind) searchParams.set('kind', params.kind)
    const qs = searchParams.toString()
    return apiFetch(`/collections/${collectionId}/children${qs ? `?${qs}` : ''}`)
  }

  async function listFeeds(): Promise<{ items: Feed[]; total: number }> {
    return apiFetch('/feeds')
  }

  async function attachCollectionFeeds(
    collectionId: string,
    feedIds: string[],
  ): Promise<CollectionFeedSubscription[]> {
    return apiFetch(`/collections/${collectionId}/feeds`, {
      method: 'POST',
      body: { feed_ids: feedIds },
    })
  }

  async function listCollectionFeeds(
    collectionId: string,
  ): Promise<CollectionFeedSubscription[]> {
    return apiFetch(`/collections/${collectionId}/feeds`)
  }

  async function createCollectionThread(
    collectionId: string,
    title?: string,
  ): Promise<CollectionChatThread> {
    return apiFetch(`/collections/${collectionId}/threads`, {
      method: 'POST',
      body: { title },
    })
  }

  async function listCollectionThreads(
    collectionId: string,
  ): Promise<CollectionChatThread[]> {
    return apiFetch(`/collections/${collectionId}/threads`)
  }

  async function listCollectionThreadMessages(
    collectionId: string,
    threadId: string,
  ): Promise<CollectionChatMessage[]> {
    return apiFetch(`/collections/${collectionId}/threads/${threadId}/messages`)
  }

  async function askCollectionThread(
    collectionId: string,
    threadId: string,
    content: string,
    topK = 10,
  ): Promise<{
    thread_id: string
    user_message: CollectionChatMessage
    assistant_message: CollectionChatMessage
  }> {
    return apiFetch(`/collections/${collectionId}/threads/${threadId}/ask`, {
      method: 'POST',
      body: { content, top_k: topK },
    })
  }

  async function triggerCollectionSync(
    collectionId: string,
  ): Promise<{ task_id?: string; queued: boolean; enabled?: boolean }> {
    return apiFetch('/ragflow/sync/trigger', {
      method: 'POST',
      body: { collection_id: collectionId },
    })
  }

  async function getResearcherProfile(researcherId: string): Promise<unknown> {
    return apiFetch(`/researchers/${researcherId}/profile`)
  }

  // ── Writing ────────────────────────────────────────────────

  async function listWritingDocuments(): Promise<WritingDocumentListResponse> {
    return apiFetch('/writing/documents')
  }

  async function createWritingDocument(): Promise<WritingDocument> {
    return apiFetch('/writing/documents', {
      method: 'POST',
    })
  }

  async function getWritingDocument(documentId: string): Promise<WritingDocument> {
    return apiFetch(`/writing/documents/${documentId}`)
  }

  async function updateWritingDocument(
    documentId: string,
    input: WritingDocumentUpdateInput,
  ): Promise<WritingDocument> {
    return apiFetch(`/writing/documents/${documentId}`, {
      method: 'PATCH',
      body: input,
    })
  }

  async function deleteWritingDocument(documentId: string): Promise<void> {
    await apiFetch(`/writing/documents/${documentId}`, {
      method: 'DELETE',
    })
  }

  async function uploadWritingImage(file: File): Promise<WritingImageUploadResponse> {
    const body = new FormData()
    body.append('file', file)

    return apiFetch('/writing/images', {
      method: 'POST',
      body,
      headers: {},
    })
  }

  // ── Intelligence ────────────────────────────────────────────

  async function getPaperHighlights(paperId: string): Promise<PaperHighlights> {
    return apiFetch(`/intelligence/papers/${paperId}/highlights`)
  }

  async function getSimilarPapers(
    paperId: string,
    topK = 5,
  ): Promise<{ similar_papers: BackendSimilarPaper[] }> {
    return apiFetch(`/intelligence/papers/${paperId}/similar?top_k=${topK}`)
  }

  async function summarizePaper(paperId: string): Promise<{ summary: string }> {
    return apiFetch(`/intelligence/papers/${paperId}/summarize`, {
      method: 'POST',
    })
  }

  async function askAboutPaper(
    paperId: string,
    question: string,
  ): Promise<{ answer: string; paper_id?: string; question?: string }> {
    return apiFetch(`/intelligence/papers/${paperId}/ask`, {
      method: 'POST',
      body: { question },
    })
  }

  // ── Trends & Claims ────────────────────────────────────────

  async function getTrendingKeywords(limit = 10): Promise<{
    keywords: Array<{
      keyword: string
      total_count: number
      growth_rate: number
      trend: string
    }>
  }> {
    return apiFetch(`/trends/hot-keywords?limit=${limit}`)
  }

  async function getTrendTopics(limit = 20): Promise<{
    topics: Array<{
      id: string
      label: string
      keywords: string[]
      paper_count: number
      trend_direction: string
    }>
  }> {
    return apiFetch(`/trends/topics?limit=${limit}`)
  }

  async function getClaimsStats(): Promise<{
    total_claims: number
    by_status: Record<string, number>
  }> {
    return apiFetch('/claims/stats')
  }

  function normalizeTask(task: {
    id: string
    title?: string
    description?: string | null
    completed?: boolean
    created_at: string
    task_type?: string
    notes?: string | null
    status?: string
  }): Task {
    return {
      id: task.id,
      title: task.title || task.task_type || 'Task',
      description: task.description || task.notes || undefined,
      completed: task.completed ?? task.status === 'done',
      created_at: task.created_at,
    }
  }

  async function getComments(paperId: string): Promise<{ comments: Comment[] }> {
    const response = await apiFetch<{ comments?: Comment[] } | Comment[]>(
      `/collaboration/comments/${paperId}`,
    )
    return { comments: Array.isArray(response) ? response : (response.comments ?? []) }
  }

  async function addComment(paperId: string, content: string): Promise<Comment> {
    return apiFetch('/collaboration/comments', {
      method: 'POST',
      body: { paper_id: paperId, content },
    })
  }

  async function listTasks(): Promise<{ tasks: Task[] }> {
    const response = await apiFetch<{ tasks?: Task[] } | Task[]>(
      '/collaboration/tasks',
    )
    const tasks = Array.isArray(response) ? response : (response.tasks ?? [])
    return { tasks: tasks.map(normalizeTask) }
  }

  async function createTask(title: string, description?: string): Promise<Task> {
    const task = await apiFetch<Task>('/collaboration/tasks', {
      method: 'POST',
      body: { title, description },
    })
    return normalizeTask(task)
  }

  async function completeTask(taskId: string): Promise<void> {
    await apiFetch(`/collaboration/tasks/${taskId}/complete`, { method: 'PATCH' })
  }

  async function getAlerts(
    unreadOnly = false,
    limit = 50,
  ): Promise<{ alerts: Alert[]; unread_count: number }> {
    const query = new URLSearchParams({ limit: String(limit) })
    if (unreadOnly) query.set('unread', 'true')
    const response = await apiFetch<{
      alerts: Array<Alert & { body?: string }>
      unread_count?: number
    }>(`/alerts?${query.toString()}`)
    return {
      unread_count: response.unread_count ?? 0,
      alerts: (response.alerts ?? []).map(alert => ({
        ...alert,
        message: alert.message || alert.body || '',
      })),
    }
  }

  async function createAlertRule(input: {
    name: string
    keywords: string[]
  }): Promise<AlertRule> {
    const rule = await apiFetch<AlertRule & { condition: unknown }>('/alerts/rules', {
      method: 'POST',
      body: {
        name: input.name,
        rule_type: 'keyword_match',
        condition: { keywords: input.keywords },
        actions: ['in_app'],
      },
    })
    return {
      ...rule,
      condition: typeof rule.condition === 'string'
        ? rule.condition
        : JSON.stringify(rule.condition ?? {}),
    }
  }

  async function getGraphStats(): Promise<GraphStats> {
    return apiFetch('/graph/stats')
  }

  async function markAlertRead(alertId: string): Promise<void> {
    await apiFetch(`/alerts/${alertId}/read`, { method: 'PATCH' })
  }

  async function markAllAlertsRead(): Promise<void> {
    await apiFetch('/alerts/mark-all-read', { method: 'POST' })
  }

  async function getAlertRules(): Promise<{ rules: AlertRule[] }> {
    const response = await apiFetch<{ rules: Array<AlertRule & { condition: unknown }> }>(
      '/alerts/rules',
    )
    return {
      rules: (response.rules ?? []).map(rule => ({
        ...rule,
        condition: typeof rule.condition === 'string'
          ? rule.condition
          : JSON.stringify(rule.condition ?? {}),
      })),
    }
  }

  async function getContradictions(
    limit = 20,
  ): Promise<{ contradictions: ContradictionPair[] }> {
    return apiFetch(`/cross-paper/contradictions?limit=${limit}`)
  }

  // ── Analytics ───────────────────────────────────────────────

  async function getAnalyticsOverview(): Promise<AnalyticsOverview> {
    return apiFetch('/analytics/overview')
  }

  async function getAnalyticsTimeline(days = 90): Promise<AnalyticsTimeline> {
    return apiFetch(`/analytics/timeline?days=${days}`)
  }

  async function getAnalyticsCategories(limit = 20): Promise<AnalyticsCategories> {
    return apiFetch(`/analytics/categories?limit=${limit}`)
  }

  async function getAnalyticsVenues(limit = 20): Promise<AnalyticsVenues> {
    return apiFetch(`/analytics/venues?limit=${limit}`)
  }

  async function getAnalyticsTopAuthors(limit = 20): Promise<AnalyticsTopAuthors> {
    return apiFetch(`/analytics/top-authors?limit=${limit}`)
  }

  async function getAnalyticsKeywordCloud(limit = 50): Promise<AnalyticsKeywordCloud> {
    return apiFetch(`/analytics/keyword-cloud?limit=${limit}`)
  }

  async function getAnalyticsCitationNetwork(): Promise<AnalyticsCitationNetwork> {
    return apiFetch('/analytics/citation-network')
  }

  // ── OpenAlex ────────────────────────────────────────────────

  async function searchOpenAlex(
    q: string,
    params?: { limit?: number; focal_id?: string },
  ): Promise<OpenAlexSearchResponse> {
    const sp = new URLSearchParams({ q })
    if (params?.limit) sp.set('limit', String(params.limit))
    if (params?.focal_id) sp.set('focal_id', params.focal_id)
    return apiFetch(`/openalex/search?${sp.toString()}`)
  }

  async function buildOpenAlexGraph(paperIds: string[]): Promise<OpenAlexGraphResponse> {
    return apiFetch('/openalex/graph', {
      method: 'POST',
      body: { paper_ids: paperIds },
    })
  }

  return {
    apiFetch,
    rawFetch,
    // Papers
    listPapers,
    getPaper,
    getClaimsForPaper,
    listRecentPapers,
    // Content
    getPaperContent,
    importFromUrl,
    reparsePaper,
    getImportStatus,
    importPaper,
    // Search
    searchPapers,
    getHealth,
    getSearchHealth,
    // Collections
    listCollections,
    createCollection,
    getCollection,
    getCollectionPapers,
    addPapersToCollection,
    listCollectionChildren,
    listFeeds,
    attachCollectionFeeds,
    listCollectionFeeds,
    createCollectionThread,
    listCollectionThreads,
    listCollectionThreadMessages,
    askCollectionThread,
    triggerCollectionSync,
    getResearcherProfile,
    // Writing
    listWritingDocuments,
    createWritingDocument,
    getWritingDocument,
    updateWritingDocument,
    deleteWritingDocument,
    uploadWritingImage,
    // Intelligence
    getPaperHighlights,
    getSimilarPapers,
    summarizePaper,
    askAboutPaper,
    // Trends & Claims
    getTrendingKeywords,
    getTrendTopics,
    getClaimsStats,
    // Collaboration
    getComments,
    addComment,
    listTasks,
    createTask,
    completeTask,
    // Alerts
    getAlerts,
    createAlertRule,
    markAlertRead,
    markAllAlertsRead,
    getAlertRules,
    getGraphStats,
    // Cross-paper
    getContradictions,
    // Analytics
    getAnalyticsOverview,
    getAnalyticsTimeline,
    getAnalyticsCategories,
    getAnalyticsVenues,
    getAnalyticsTopAuthors,
    getAnalyticsKeywordCloud,
    getAnalyticsCitationNetwork,
    // OpenAlex
    searchOpenAlex,
    buildOpenAlexGraph,
  }
}

// ─── Analytics Types ────────────────────────────────────────────

export interface AnalyticsOverview {
  total_papers: number
  with_fulltext: number
  by_status: Record<string, number>
  by_source_type: Record<string, number>
  avg_citation_count: number
  total_authors: number
  total_references: number
}

export interface AnalyticsTimeline {
  points: Array<{ date: string; count: number }>
  granularity: string
}

export interface AnalyticsCategories {
  categories: Array<{ name: string; count: number }>
  total: number
}

export interface AnalyticsVenues {
  venues: Array<{ name: string; count: number }>
  total: number
}

export interface AnalyticsTopAuthors {
  authors: Array<{
    id: string
    name: string
    paper_count: number
    total_citations: number
  }>
}

export interface AnalyticsKeywordCloud {
  keywords: Array<{ keyword: string; count: number }>
  total_papers_with_keywords: number
}

// ─── OpenAlex Types ─────────────────────────────────────────────

export interface OpenAlexAuthorship {
  name: string
  openalex_id: string
  orcid?: string | null
  position?: string
  institutions?: string[]
}

export interface OpenAlexPaper {
  openalex_id: string
  openalex_url?: string
  title: string
  year?: number | null
  authors: string[]
  authorships?: OpenAlexAuthorship[]
  abstract?: string
  cited_by_count?: number
  primary_topic?: string | null
  topics?: Array<{ id: string; display_name: string; score?: number }>
  keywords?: Array<{ id?: string; display_name: string }>
  concepts?: Array<{ id: string; display_name: string; score?: number }>
  venue?: string | null
  oa_url?: string | null
  doi?: string | null
  fwci?: number | null
  language?: string | null
  similarity_score?: number
}

export interface OpenAlexEdge {
  source: string
  target: string
}

export interface OpenAlexSearchResponse {
  query: string
  focal_id: string | null
  total: number
  papers: OpenAlexPaper[]
  edges: OpenAlexEdge[]
}

export interface OpenAlexGraphNode extends OpenAlexPaper {
  is_origin: boolean
}

export interface OpenAlexGraphResponse {
  nodes: OpenAlexGraphNode[]
  edges: OpenAlexEdge[]
  origin_count: number
  ref_count: number
  isolated_count: number
}

export interface AnalyticsCitationNetwork {
  total_nodes: number
  total_edges: number
  resolved_edges: number
  avg_references_per_paper: number
  top_cited: Array<{
    paper_id: string
    title: string
    internal_citations: number
  }>
}
