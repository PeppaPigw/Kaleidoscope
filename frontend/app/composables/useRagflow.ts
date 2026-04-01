/**
 * useRagflow — composable for RAGFlow-powered Q&A, evidence, and routing.
 *
 * Wraps the /api/v1/ragflow/* endpoints for use in reader, workspace,
 * and evidence Vue pages.
 */

// ─── Types ─────────────────────────────────────────────────────

export interface RagflowAskResponse {
  enabled: boolean
  answer: string | null
  sources: Array<{
    content?: string
    score?: number
    metadata?: Record<string, unknown>
  }>
  latency_ms?: number
  ready?: boolean
  message?: string
  error?: string
}

export interface EvidenceChunk {
  content: string | null
  score: number | null
  metadata: Record<string, unknown>
  paper_metadata: Record<string, unknown>
  graph_boosted?: boolean
}

export interface EvidencePackResponse {
  enabled: boolean
  chunks: EvidenceChunk[]
  total: number
  latency_ms?: number
  ready?: boolean
  error?: string
}

export interface RoutedQueryResponse {
  route: string
  hits: Array<Record<string, unknown>>
  answer: string | null
  sources: Array<Record<string, unknown>>
  latency_ms: number
  total?: number
  graph_expansion?: Array<Record<string, unknown>>
  error?: string
}

export interface SyncStatusResponse {
  enabled: boolean
  freshness_minutes: number
  health: Record<string, unknown> | null
  counts: {
    total_mappings: number
    paper_mappings: number
    collection_mappings: number
    stale_mappings: number
  }
}

export interface GroundingCheckResponse {
  grounded: boolean
  coverage: number
  source_count: number
  sentences_checked: number
  sentences_grounded: number
}

// ─── Composable ────────────────────────────────────────────────

export function useRagflow() {
  const { apiFetch } = useApi()

  /** Ask a grounded question against a workspace/collection */
  async function askWorkspace(
    collectionId: string,
    question: string,
    topK = 10,
  ): Promise<RagflowAskResponse> {
    return apiFetch(`/workspaces/${collectionId}/ask`, {
      method: 'POST',
      body: { question, top_k: topK },
    })
  }

  /** Ask a grounded question against a single paper */
  async function askPaper(
    paperId: string,
    question: string,
    topK = 5,
  ): Promise<RagflowAskResponse> {
    return apiFetch(`/papers/${paperId}/ask`, {
      method: 'POST',
      body: { question, top_k: topK },
    })
  }

  /** Get raw evidence chunks for a workspace question */
  async function getEvidence(
    collectionId: string,
    question: string,
    topK = 15,
  ): Promise<EvidencePackResponse> {
    const params = new URLSearchParams({ q: question, top_k: String(topK) })
    return apiFetch(`/workspaces/${collectionId}/evidence?${params.toString()}`)
  }

  /** Route a query to the best retrieval backend */
  async function routedQuery(
    query: string,
    opts?: {
      collectionId?: string
      paperId?: string
      topK?: number
    },
  ): Promise<RoutedQueryResponse> {
    return apiFetch('/ragflow/query/route', {
      method: 'POST',
      body: {
        query,
        collection_id: opts?.collectionId,
        paper_id: opts?.paperId,
        top_k: opts?.topK ?? 10,
      },
    })
  }

  /** Get sync status overview */
  async function getSyncStatus(): Promise<SyncStatusResponse> {
    return apiFetch('/ragflow/sync/status')
  }

  /** Trigger sync for a collection */
  async function triggerSync(
    collectionId: string,
  ): Promise<{ task_id?: string; queued: boolean; enabled?: boolean }> {
    return apiFetch('/ragflow/sync/trigger', {
      method: 'POST',
      body: { collection_id: collectionId },
    })
  }

  /** Check answer grounding against sources */
  async function checkGrounding(
    answer: string,
    sources: Array<Record<string, unknown>>,
  ): Promise<GroundingCheckResponse> {
    return apiFetch('/ragflow/eval/grounding-check', {
      method: 'POST',
      body: { answer, sources },
    })
  }

  /** Synthesize a structured overview for a topic collection (MVP 3) */
  async function synthesizeTopic(
    collectionId: string,
    topicQuery: string,
    maxPapers = 20,
  ): Promise<Record<string, unknown>> {
    return apiFetch(`/workspaces/${collectionId}/synthesize`, {
      method: 'POST',
      body: { topic_query: topicQuery, max_papers: maxPapers },
    })
  }

  return {
    askWorkspace,
    askPaper,
    getEvidence,
    routedQuery,
    getSyncStatus,
    triggerSync,
    checkGrounding,
    synthesizeTopic,
  }
}
