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
  }): Promise<{ papers: Paper[] }> {
    const query = new URLSearchParams()
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    const qs = query.toString()
    return apiFetch(`/papers${qs ? `?${qs}` : ''}`)
  }

  async function getPaper(paperId: string): Promise<Paper> {
    return apiFetch(`/papers/${paperId}`)
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

  // ── Search ──────────────────────────────────────────────────

  async function searchPapers(query: string, limit = 20): Promise<{ results: Paper[] }> {
    return apiFetch(`/search?q=${encodeURIComponent(query)}&limit=${limit}`)
  }

  // ── Collections ─────────────────────────────────────────────

  async function listCollections(): Promise<{ collections: unknown[] }> {
    return apiFetch('/collections')
  }

  // ── Intelligence ────────────────────────────────────────────

  async function summarizePaper(paperId: string): Promise<{ summary: string }> {
    return apiFetch(`/intelligence/papers/${paperId}/summarize`, {
      method: 'POST',
    })
  }

  async function askAboutPaper(
    paperId: string,
    question: string,
  ): Promise<{ answer: string }> {
    return apiFetch(`/intelligence/papers/${paperId}/ask`, {
      method: 'POST',
      body: { question },
    })
  }

  return {
    // Papers
    listPapers,
    getPaper,
    // Content
    getPaperContent,
    importFromUrl,
    reparsePaper,
    // Search
    searchPapers,
    // Collections
    listCollections,
    // Intelligence
    summarizePaper,
    askAboutPaper,
  }
}
