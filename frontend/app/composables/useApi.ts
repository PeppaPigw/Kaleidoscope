/**
 * useApi — typed, reactive wrapper around Kaleidoscope backend.
 *
 * Uses Nuxt's `useFetch` with the runtime API URL.
 * Provides paper CRUD, content, collections, and search.
 */

// ─── Types ─────────────────────────────────────────────────────

export interface Paper {
  id: string
  title: string
  abstract?: string | null
  doi?: string | null
  arxiv_id?: string | null
  published_at?: string | null
  citation_count?: number | null
  reading_status?: string
  has_full_text?: boolean
  ingestion_status?: string
  remote_urls?: Array<{ url: string; source: string; type: string }>
  keywords?: string[]
  summary?: string | null
  highlights?: string[]
  contributions?: string[]
  limitations?: string[]
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
  paper_count?: number | null
  color?: string | null
  icon?: string | null
  is_smart?: boolean
  created_at?: string
  updated_at?: string
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
    label?: string
    caption?: string
    type?: string
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
    return await $fetch<T>(`${baseUrl}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })
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

  // ── Collections ─────────────────────────────────────────────

  async function listCollections(): Promise<Collection[]> {
    return apiFetch('/collections')
  }

  async function createCollection(req: {
    name: string
    description?: string
  }): Promise<Collection> {
    return apiFetch('/collections', {
      method: 'POST',
      body: req,
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

  async function getAnalyticsTopAuthors(limit = 20): Promise<AnalyticsTopAuthors> {
    return apiFetch(`/analytics/top-authors?limit=${limit}`)
  }

  async function getAnalyticsKeywordCloud(limit = 50): Promise<AnalyticsKeywordCloud> {
    return apiFetch(`/analytics/keyword-cloud?limit=${limit}`)
  }

  async function getAnalyticsCitationNetwork(): Promise<AnalyticsCitationNetwork> {
    return apiFetch('/analytics/citation-network')
  }

  return {
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
    // Search
    searchPapers,
    // Collections
    listCollections,
    createCollection,
    // Intelligence
    getPaperHighlights,
    getSimilarPapers,
    summarizePaper,
    askAboutPaper,
    // Analytics
    getAnalyticsOverview,
    getAnalyticsTimeline,
    getAnalyticsCategories,
    getAnalyticsTopAuthors,
    getAnalyticsKeywordCloud,
    getAnalyticsCitationNetwork,
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
