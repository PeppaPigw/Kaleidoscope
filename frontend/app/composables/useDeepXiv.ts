/**
 * useDeepXiv — composable for DeepXiv paper search, progressive reading,
 * trending papers, social impact, PMC, web search, and research agent.
 */

// ── Types ─────────────────────────────────────────────

export interface DeepXivSearchResult {
  arxiv_id: string
  title: string
  abstract?: string | null
  authors: string[]
  categories: string[]
  citations: number
  score: number
  token_count?: number | null
}

export interface DeepXivSearchResponse {
  total: number
  results: DeepXivSearchResult[]
}

export interface DeepXivSection {
  name: string
  idx: number
  tldr?: string | null
  token_count: number
}

export interface DeepXivHeadResponse {
  arxiv_id: string
  title: string
  abstract?: string | null
  authors: Array<string | { name: string; orgs?: string[] }>
  sections: DeepXivSection[]
  token_count: number
  citations: number
  publish_at?: string | null
  venue?: string | null
  journal_name?: string | null
  keywords: string[]
  tldr?: string | null
  github_url?: string | null
  src_url?: string | null
  categories: string[]
}

export interface DeepXivBriefResponse {
  arxiv_id: string
  title: string
  tldr?: string | null
  keywords: string[]
  publish_at?: string | null
  citations: number
  src_url?: string | null
  github_url?: string | null
}

export interface DeepXivSectionResponse {
  arxiv_id: string
  section_name: string
  content: string
}

export interface DeepXivPreviewResponse {
  arxiv_id?: string
  text: string
  is_truncated: boolean
  total_characters: number
  preview_characters: number
}

export interface DeepXivSocialImpact {
  arxiv_id: string
  total_tweets: number
  total_likes: number
  total_views: number
  total_replies: number
  first_seen_date?: string | null
  last_seen_date?: string | null
  message?: string | null
}

export interface DeepXivTrendingPaper {
  arxiv_id: string
  rank?: number
  stats?: {
    total_views?: number
    total_likes?: number
    total_mentions?: number
  }
  mentioned_by?: Array<{
    name: string
    username: string
    followers: number
  }>
  [key: string]: unknown
}

export interface DeepXivTrendingResponse {
  days: number
  generated_at?: string | null
  papers: DeepXivTrendingPaper[]
  total: number
}

export interface DeepXivAgentResponse {
  answer: string
  papers_loaded: number
}

export interface DeepXivSearchParams {
  size?: number
  offset?: number
  search_mode?: 'hybrid' | 'bm25' | 'vector'
  bm25_weight?: number
  vector_weight?: number
  categories?: string[]
  authors?: string[]
  min_citation?: number
  date_from?: string
  date_to?: string
}

// ── Composable ────────────────────────────────────────

export function useDeepXiv() {
  const config = useRuntimeConfig()
  const base = `${config.public.apiUrl}/api/v1/deepxiv`

  // ─── Search ──────────────────────────────────────

  async function searchPapers(
    query: string,
    params?: DeepXivSearchParams,
  ): Promise<DeepXivSearchResponse> {
    const sp: Record<string, string> = { q: query }
    if (params?.size) sp.size = String(params.size)
    if (params?.offset) sp.offset = String(params.offset)
    if (params?.search_mode) sp.search_mode = params.search_mode
    if (params?.bm25_weight !== undefined) sp.bm25_weight = String(params.bm25_weight)
    if (params?.vector_weight !== undefined) sp.vector_weight = String(params.vector_weight)
    if (params?.categories?.length) sp.categories = params.categories.join(',')
    if (params?.authors?.length) sp.authors = params.authors.join(',')
    if (params?.min_citation !== undefined) sp.min_citation = String(params.min_citation)
    if (params?.date_from) sp.date_from = params.date_from
    if (params?.date_to) sp.date_to = params.date_to
    return $fetch(`${base}/search`, { params: sp })
  }

  // ─── Progressive paper reading ───────────────────

  async function getPaperHead(arxivId: string): Promise<DeepXivHeadResponse> {
    return $fetch(`${base}/papers/${arxivId}/head`)
  }

  async function getPaperBrief(arxivId: string): Promise<DeepXivBriefResponse> {
    return $fetch(`${base}/papers/${arxivId}/brief`)
  }

  async function getPaperSection(arxivId: string, sectionName: string): Promise<DeepXivSectionResponse> {
    return $fetch(`${base}/papers/${arxivId}/section`, { params: { name: sectionName } })
  }

  async function getPaperPreview(arxivId: string): Promise<DeepXivPreviewResponse> {
    return $fetch(`${base}/papers/${arxivId}/preview`)
  }

  async function getPaperRaw(arxivId: string): Promise<{ arxiv_id: string; content: string }> {
    return $fetch(`${base}/papers/${arxivId}/raw`)
  }

  async function getPaperJson(arxivId: string): Promise<Record<string, unknown>> {
    return $fetch(`${base}/papers/${arxivId}/json`)
  }

  async function getMarkdownUrl(arxivId: string): Promise<{ arxiv_id: string; url: string }> {
    return $fetch(`${base}/papers/${arxivId}/markdown-url`)
  }

  async function getSocialImpact(arxivId: string): Promise<DeepXivSocialImpact> {
    return $fetch(`${base}/papers/${arxivId}/social-impact`)
  }

  // ─── PMC ─────────────────────────────────────────

  async function getPmcHead(pmcId: string): Promise<Record<string, unknown>> {
    return $fetch(`${base}/pmc/${pmcId}/head`)
  }

  async function getPmcFull(pmcId: string): Promise<Record<string, unknown>> {
    return $fetch(`${base}/pmc/${pmcId}/full`)
  }

  // ─── Trending ────────────────────────────────────

  async function getTrending(days: number = 7, limit: number = 30): Promise<DeepXivTrendingResponse> {
    return $fetch(`${base}/trending`, { params: { days, limit } })
  }

  // ─── Web search ──────────────────────────────────

  async function webSearch(query: string): Promise<Record<string, unknown>> {
    return $fetch(`${base}/websearch`, { params: { q: query } })
  }

  // ─── Semantic Scholar ────────────────────────────

  async function semanticScholarLookup(s2Id: string): Promise<Record<string, unknown>> {
    return $fetch(`${base}/semantic-scholar/${s2Id}`)
  }

  // ─── Research Agent ──────────────────────────────

  async function agentQuery(question: string, resetPapers: boolean = false): Promise<DeepXivAgentResponse> {
    return $fetch(`${base}/agent/query`, {
      method: 'POST',
      body: { question, reset_papers: resetPapers },
    })
  }

  return {
    searchPapers,
    getPaperHead,
    getPaperBrief,
    getPaperSection,
    getPaperPreview,
    getPaperRaw,
    getPaperJson,
    getMarkdownUrl,
    getSocialImpact,
    getPmcHead,
    getPmcFull,
    getTrending,
    webSearch,
    semanticScholarLookup,
    agentQuery,
  }
}
