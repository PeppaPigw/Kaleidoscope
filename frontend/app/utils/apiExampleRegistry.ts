import { getRuntimeApiExampleProfile } from "./apiRuntimeExamples";

export interface ApiExampleProfile {
  pathParams?: Record<string, unknown>;
  query?: Record<string, unknown>;
  body?: unknown;
  responseShape?: unknown;
  notes?: string[];
}

const PAPER_ID = "31a1d910-a440-4a71-8614-93bc570f7a5d";
const TOPIC = "Dual-View Training for Instruction-Following Information Retrieval";
const ARXIV_ID = "2604.18845";
const QUESTION = TOPIC;
const ABSTRACT_SNIPPET =
  "Instruction-following information retrieval (IF-IR) studies retrieval systems that must not only find documents relevant to a query, but also obey explicit user constraints such as required attributes, exclusions, or output preferences.";
const INTRO_SNIPPET =
  "Instruction-following information retrieval extends traditional semantic matching by requiring systems to adhere to both a query and explicit user-defined constraints that specify relevance criteria.";
const RESULT_SNIPPET =
  "FollowIR p-MRR increases from 5.21 to 7.57 (+45%), surpassing general-purpose embedding models of comparable or larger scale.";

const liveEvidenceItem = {
  id: "69d83c03-d35d-4deb-b084-d842a36a64ac",
  paper_id: PAPER_ID,
  paper_title: TOPIC,
  section_title: "Abstract",
  content: ABSTRACT_SNIPPET,
  score: 1,
  source: "paper_chunk",
  arxiv_id: ARXIV_ID,
  anchor: "E1",
  provenance: {
    table: "paper_chunks",
    chunk_id: "69d83c03-d35d-4deb-b084-d842a36a64ac",
    order_index: 1,
  },
};

const liveEvidenceResponse = {
  query: QUESTION,
  scope: { paper_ids: [PAPER_ID], collection_id: null },
  total: 5,
  evidence: [
    liveEvidenceItem,
    {
      ...liveEvidenceItem,
      id: "b7f4ea05-e82d-4a62-824a-11d4fcbba95c",
      section_title: "1 Introduction",
      content: INTRO_SNIPPET,
      anchor: "E2",
      provenance: {
        table: "paper_chunks",
        chunk_id: "b7f4ea05-e82d-4a62-824a-11d4fcbba95c",
        order_index: 2,
      },
    },
    {
      ...liveEvidenceItem,
      id: "1377dc95-2ac9-4fd3-821e-7b3949cef741",
      section_title: "4 Results and Analysis",
      content: RESULT_SNIPPET,
      score: 0.86,
      anchor: "E3",
      provenance: {
        table: "paper_chunks",
        chunk_id: "1377dc95-2ac9-4fd3-821e-7b3949cef741",
        order_index: 5,
      },
    },
  ],
  diagnostics: {
    backend: "local_sql",
    query_terms: [
      "dual-view",
      "training",
      "instruction-following",
      "information",
      "retrieval",
    ],
    candidate_count: 17,
    top_k: 5,
  },
};

const agentEnvelope = (data: Record<string, unknown>): Record<string, unknown> => ({
  data,
  meta: {
    request_id: "req_...",
    api_version: "v1",
    source: "local_runtime",
    generated_at: "2026-04-26T00:00:00Z",
    implementation_status: "production",
  },
  warnings: [],
  provenance: [
    {
      source: "kaleidoscope.local_runtime",
      confidence: 1,
    },
  ],
});

const agentBody = (
  input: Record<string, unknown> = {},
  scope: Record<string, unknown> = { paper_ids: [PAPER_ID], topic: TOPIC },
): Record<string, unknown> => ({
  scope,
  language: "auto",
  token_budget: 2048,
  include_provenance: true,
  include_confidence: true,
  async: false,
  input: {
    query: TOPIC,
    ...input,
  },
});

export const API_EXAMPLE_REGISTRY: Record<string, ApiExampleProfile> = {
  "GET /api/v1/agent/manifest": {
    responseShape: {
      schema_version: "1.0.0",
      service: { name: "Kaleidoscope", api_version: "v1" },
      tools: [],
      rest_capabilities: [],
      recommended_workflows: [],
    },
    notes: ["Use this first when building an agent client."],
  },
  "GET /api/v1/agent/capabilities": {
    responseShape: agentEnvelope({
      capabilities: [
        {
          id: "J10",
          method: "GET",
          path: "/api/v1/agent/capabilities",
          status: "production",
          request_example: {
            scope: { paper_ids: [PAPER_ID], topic: TOPIC },
            input: { query: TOPIC },
          },
        },
      ],
      input_schema: "AgentApiRequest",
      output_schema: "AgentApiEnvelope",
    }),
    notes: ["Lists readiness status and runnable examples for agent routes."],
  },
  "POST /api/v1/agent/resolve/identifier": {
    body: agentBody({
      identifier: ARXIV_ID,
    }),
    responseShape: agentEnvelope({
      canonical_id: ARXIV_ID,
      ids: { arxiv_id: ARXIV_ID },
      title: TOPIC,
      confidence: 1,
      local_paper_id: PAPER_ID,
      source: "local_database",
    }),
  },
  "POST /api/v1/agent/resolve/title": {
    body: agentBody({ title: TOPIC }),
    responseShape: agentEnvelope({
      candidates: [
        {
          paper_id: PAPER_ID,
          title: TOPIC,
          arxiv_id: ARXIV_ID,
          has_full_text: true,
          match_score: 1,
          source: "local_database",
        },
      ],
      match_score: 1,
      source: "local_database",
      recommended_candidate: PAPER_ID,
    }),
  },
  "POST /api/v1/agent/ingest/source": {
    body: agentBody({
      source: `https://arxiv.org/abs/${ARXIV_ID}`,
    }),
    responseShape: agentEnvelope({
      paper_id: PAPER_ID,
      job_id: "string | null",
      detected_ids: { arxiv_id: ARXIV_ID },
      source_type: "arxiv",
      dedupe_status: "duplicate | new_or_unresolved",
      next_actions: [],
    }),
  },
  "GET /api/v1/agent/papers/{paper_id}/processing-plan": {
    pathParams: { paper_id: PAPER_ID },
    responseShape: agentEnvelope({
      paper_id: PAPER_ID,
      missing_steps: [],
      available_outputs: ["metadata", "sections"],
      recommended_jobs: [],
    }),
  },
  "GET /api/v1/agent/papers/{paper_id}/section-map": {
    pathParams: { paper_id: PAPER_ID },
    responseShape: agentEnvelope({
      sections: [
        {
          title: TOPIC,
          normalized_type:
            "dual-view-training-for-instruction-following-information-retrieval",
          token_count: 39,
        },
        {
          title: "Abstract",
          normalized_type: "abstract",
          token_count: 387,
          paragraphs: [ABSTRACT_SNIPPET],
        },
        {
          title: "1 Introduction",
          normalized_type: "introduction",
          token_count: 802,
          paragraphs: [INTRO_SNIPPET],
        },
      ],
      token_count: 1228,
    }),
  },
  "GET /api/v1/agent/papers/{paper_id}/sections/{section_type}": {
    pathParams: { paper_id: PAPER_ID, section_type: "introduction" },
    responseShape: agentEnvelope({
      section_type: "introduction",
      title: "1 Introduction",
      markdown: `${INTRO_SNIPPET}\n\nWe make three contributions. First, we propose a polarity-reversal synthesis strategy that improves FollowIR p-MRR by 45% on a 305M-parameter encoder.`,
      paragraphs: [
        {
          paragraph_id: "s3p1",
          section_type: "introduction",
          text: INTRO_SNIPPET,
          token_count: 78,
        },
      ],
      page_spans: [],
      char_span: [1708, 2020],
    }),
  },
  "GET /api/v1/agent/papers/{paper_id}/paragraphs": {
    pathParams: { paper_id: PAPER_ID },
    responseShape: agentEnvelope({
      paragraphs: [
        {
          paragraph_id: "s2p1",
          section_type: "abstract",
          section_title: "Abstract",
          text: ABSTRACT_SNIPPET,
          char_span: [157, 1707],
          token_count: 387,
        },
      ],
    }),
  },
  "POST /api/v1/evidence/search": {
    body: {
      query: QUESTION,
      paper_ids: [PAPER_ID],
      top_k: 5,
      include_paper_fallback: true,
    },
    responseShape: liveEvidenceResponse,
  },
  "POST /api/v1/agent/evidence/search": {
    body: {
      query: QUESTION,
      paper_ids: [PAPER_ID],
      top_k: 5,
      include_paper_fallback: true,
    },
    responseShape: liveEvidenceResponse,
  },
  "POST /api/v1/evidence/packs": {
    body: {
      query: QUESTION,
      paper_ids: [PAPER_ID],
      top_k: 8,
      token_budget: 2048,
    },
    responseShape: {
      question: QUESTION,
      scope: { paper_ids: [PAPER_ID], collection_id: null },
      budget: { requested_tokens: 2048, estimated_tokens: 1917, truncated: true },
      citations: [
        {
          anchor: "E1",
          paper_id: PAPER_ID,
          paper_title: TOPIC,
          section_title: "Abstract",
        },
      ],
      evidence: [liveEvidenceItem],
      warnings: [],
    },
  },
  "POST /api/v1/agent/evidence/packs": {
    body: {
      query: QUESTION,
      paper_ids: [PAPER_ID],
      top_k: 8,
      token_budget: 2048,
    },
    responseShape: {
      question: QUESTION,
      scope: { paper_ids: [PAPER_ID], collection_id: null },
      budget: { requested_tokens: 2048, estimated_tokens: 1917, truncated: true },
      citations: [
        {
          anchor: "E1",
          paper_id: PAPER_ID,
          paper_title: TOPIC,
          section_title: "Abstract",
        },
      ],
      evidence: [liveEvidenceItem],
      warnings: [],
    },
  },
  "GET /api/v1/agent/papers/{paper_id}/abstract-plus": {
    pathParams: { paper_id: PAPER_ID },
    responseShape: agentEnvelope({
      abstract: ABSTRACT_SNIPPET,
      problem:
        "Instruction-following information retrieval systems must satisfy explicit user constraints, not only semantic relevance.",
      method:
        "Dual-view data synthesis uses polarity reversal to generate complementary instructions where document relevance labels swap.",
      result:
        "On a 305M-parameter encoder, the method improves FollowIR benchmark performance by 45%.",
      keywords: ["instruction-following retrieval", "dual-view training"],
      field: "information retrieval",
    }),
  },
  "GET /api/v1/agent/papers/{paper_id}/contributions": {
    pathParams: { paper_id: PAPER_ID },
    responseShape: agentEnvelope({
      contributions: [
        "A polarity-reversal synthesis strategy for instruction-following retrieval.",
        "A size-matched comparison showing instruction supervision improves instruction sensitivity.",
        "Evidence that dual-view synthesis can improve instruction sensitivity and preserve general retrieval quality.",
      ],
      type: "paper_claim",
      novelty_claim:
        "The same document pair is reused under complementary instructions so the retriever must condition on instruction semantics.",
      supporting_sections: ["Abstract", "1 Introduction", "4 Results and Analysis"],
    }),
  },
  "GET /api/v1/agent/papers/{paper_id}/method-card": {
    pathParams: { paper_id: PAPER_ID },
    responseShape: agentEnvelope({
      method_name: TOPIC,
      inputs: ["query", "positive document", "instruction negative document"],
      outputs: ["complementary instruction", "dual-view training pair"],
      architecture:
        "An LLM generates a new instruction that makes the previous hard negative relevant and the previous positive document an instruction negative.",
      training:
        "Contrastive training pairs the original and polarity-reversed views so retrieval depends on instruction semantics.",
      complexity: "No serving-time architecture change is required.",
    }),
  },
  "GET /api/v1/agent/papers/{paper_id}/experiment-card": {
    pathParams: { paper_id: PAPER_ID },
    responseShape: agentEnvelope({
      datasets: ["PromptRiever", "FollowIR", "InfoSearch", "MAIR IFEval"],
      baselines: ["Ins-orig", "All-orig", "EmbeddingGemma-300M"],
      metrics: ["p-MRR", "FollowIR Score", "MAIR IFEval"],
      settings: [
        {
          encoder: "gte-multilingual-mlm-base",
          parameters: "305M",
          hard_negatives_per_query: 30,
        },
      ],
      hardware: [],
      seeds: [],
    }),
  },
  "GET /api/v1/agent/papers/{paper_id}/results-card": {
    pathParams: { paper_id: PAPER_ID },
    responseShape: agentEnvelope({
      results: [RESULT_SNIPPET],
      metric: ["FollowIR p-MRR"],
      value: ["7.57"],
      baseline: ["Ins-orig p-MRR 5.21"],
      delta: ["+45%"],
      table_or_figure: ["4 Results and Analysis"],
    }),
  },
  "GET /api/v1/agent/papers/{paper_id}/limitations/structured": {
    pathParams: { paper_id: PAPER_ID },
    responseShape: agentEnvelope({
      limitations: [
        "External citation/provider coverage is not measured by the local corpus.",
      ],
      stated: true,
      risk_area: ["external_validity"],
      evidence_spans: [liveEvidenceItem],
    }),
  },
  "POST /api/v1/claims/verify": {
    body: {
      claim: TOPIC,
      paper_ids: [PAPER_ID],
      top_k: 5,
    },
    responseShape: {
      claim: TOPIC,
      label: "supported",
      confidence: 0.95,
      rationale: `The claim is labeled supported from the top local snippet E1 in ${TOPIC}.`,
      evidence_pack: {
        question: TOPIC,
        citations: [
          {
            anchor: "E1",
            paper_id: PAPER_ID,
            paper_title: TOPIC,
            section_title: "Abstract",
          },
        ],
        evidence: [liveEvidenceItem],
      },
    },
  },
  "POST /api/v1/agent/claims/verify": {
    body: {
      claim: TOPIC,
      paper_ids: [PAPER_ID],
      top_k: 5,
    },
    responseShape: {
      claim: TOPIC,
      label: "supported",
      confidence: 0.95,
      rationale: `The claim is labeled supported from the top local snippet E1 in ${TOPIC}.`,
      evidence_pack: {
        question: TOPIC,
        citations: [
          {
            anchor: "E1",
            paper_id: PAPER_ID,
            paper_title: TOPIC,
            section_title: "Abstract",
          },
        ],
        evidence: [liveEvidenceItem],
      },
    },
  },
  "POST /api/v1/agent/citations/intent-classify": {
    body: {
      contexts: ["We compare against this baseline in the evaluation section."],
    },
    responseShape: {
      total: 1,
      results: [
        {
          context: "We compare against this baseline in the evaluation section.",
          intent: "background | method | comparison | criticism",
          confidence: 0.7,
        },
      ],
    },
  },
  "POST /api/v1/agent/benchmarks/extract": {
    body: {
      text: RESULT_SNIPPET,
      paper_ids: [PAPER_ID],
    },
    responseShape: {
      benchmarks: ["FollowIR"],
      datasets: ["PromptRiever"],
      metrics: ["p-MRR"],
      hardware: [],
      warnings: [],
    },
  },
  "POST /api/v1/agent/literature/review-map": {
    body: { topic: TOPIC, paper_ids: [PAPER_ID], limit: 20 },
    responseShape: {
      mode: "review-map",
      nodes: [],
      edges: [],
      themes: [],
      reading_order: [],
    },
  },
  "POST /api/v1/agent/literature/related-work-pack": {
    body: { topic: TOPIC, paper_ids: [PAPER_ID], limit: 20 },
    responseShape: {
      mode: "related-work-pack",
      nodes: [],
      edges: [],
      claims: [],
      related_work: [],
    },
  },
  "POST /api/v1/agent/literature/contradiction-map": {
    body: { topic: TOPIC, paper_ids: [PAPER_ID], limit: 20 },
    responseShape: {
      mode: "contradiction-map",
      nodes: [],
      edges: [],
      claims: [],
      contradictions: [],
    },
  },
  "POST /api/v1/agent/context/task-pack": {
    body: agentBody({
      task: "write a grounded literature review",
      query: TOPIC,
    }),
    responseShape: agentEnvelope({
      task: TOPIC,
      inputs: { paper_ids: [PAPER_ID], topic: TOPIC },
      context_blocks: [liveEvidenceItem],
      tool_suggestions: [
        {
          method: "POST",
          path: "/api/v1/agent/context/task-pack",
        },
      ],
    }),
  },
  "POST /api/v1/agent/synthesis/evidence-matrix": {
    body: agentBody({ query: TOPIC }),
    responseShape: agentEnvelope({
      claims: [TOPIC],
      papers: [{ paper_id: PAPER_ID, title: TOPIC }],
      matrix: [{ claim: TOPIC, paper_id: PAPER_ID, support: "supported" }],
      support_levels: ["supported"],
      citations: [{ anchor: "E1", paper_id: PAPER_ID, section_title: "Abstract" }],
    }),
  },
  "POST /api/v1/agent/synthesis/method-comparison": {
    body: agentBody({ query: TOPIC }),
    responseShape: agentEnvelope({
      methods: ["Dual-view data synthesis", "instruction-negative training"],
      dimensions: ["instruction sensitivity", "general retrieval quality"],
      tradeoffs: [
        "Instruction supervision improves IF sensitivity while data diversity preserves general retrieval.",
      ],
      best_for: ["instruction-following retrieval"],
    }),
  },
  "POST /api/v1/agent/synthesis/gap-analysis": {
    body: agentBody({ query: TOPIC }),
    responseShape: agentEnvelope({
      gaps: ["External citation/provider coverage is not measured locally."],
      evidence: [liveEvidenceItem],
      feasibility: "medium",
      suggested_work: ["Compare dual-view synthesis across more retriever backbones."],
    }),
  },
  "POST /api/v1/agent/synthesis/reading-plan": {
    body: agentBody({ query: TOPIC }),
    responseShape: agentEnvelope({
      steps: ["Read Abstract", "Read 1 Introduction", "Read 2 Methodology"],
      paper_ids: [PAPER_ID],
      reason: "topic_relevance_then_recency",
      expected_takeaway: [
        "Understand how polarity reversal creates dual-view training samples.",
      ],
    }),
  },
  "POST /api/v1/agent/writing/outline": {
    body: agentBody({ query: TOPIC }),
    responseShape: agentEnvelope({
      outline: [
        "Problem: retrievers ignore instruction constraints",
        "Method: polarity-reversal dual-view synthesis",
        "Result: FollowIR p-MRR improves by 45%",
      ],
      required_evidence: [liveEvidenceItem],
      citation_slots: [{ anchor: "E1", section_title: "Abstract" }],
      missing_context: [],
    }),
  },
  "POST /api/v1/agent/writing/claim-grounding": {
    body: agentBody({
      claims: [TOPIC],
    }),
    responseShape: agentEnvelope({
      grounded_claims: [{ claim: TOPIC, evidence_anchor: "E1" }],
      unsupported_claims: [],
      evidence_spans: [liveEvidenceItem],
      risk_score: 0,
    }),
  },
  "POST /api/v1/agent/writing/citation-repair": {
    body: agentBody({ query: TOPIC }),
    responseShape: agentEnvelope({
      repairs: [{ claim: TOPIC, added_anchor: "E1" }],
      removed_citations: [],
      added_citations: [{ anchor: "E1", paper_id: PAPER_ID, section_title: "Abstract" }],
      confidence: 0.95,
    }),
  },
  "POST /api/v1/agent/writing/bibliography/export": {
    body: agentBody({ format: "bibtex" }),
    responseShape: agentEnvelope({
      format: "bibtex",
      entries: [
        `@misc{dualview2026, title={${TOPIC}}, archivePrefix={arXiv}, eprint={${ARXIV_ID}}}`,
      ],
      missing_metadata: [],
      dedupe_log: [],
    }),
  },
  "POST /api/v1/agent/planning/next-best-actions": {
    body: agentBody({ objective: "write a grounded literature review" }),
    responseShape: agentEnvelope({
      actions: ["Fetch evidence pack", "Ground outline claims", "Export bibliography"],
      expected_value: ["citation-safe literature review draft"],
      required_api_calls: [
        "POST /api/v1/agent/evidence/packs",
        "POST /api/v1/agent/writing/outline",
      ],
      blocking_unknowns: [],
      objective: "write a grounded literature review",
    }),
  },
  "POST /api/v1/agent/planning/tool-route": {
    body: agentBody({ task: "write a grounded literature review" }),
    responseShape: agentEnvelope({
      route: [
        "POST /api/v1/agent/context/task-pack",
        "POST /api/v1/agent/evidence/search",
        "POST /api/v1/agent/writing/outline",
      ],
      inputs_needed: ["paper_ids or topic"],
      expected_outputs: ["context_blocks", "evidence", "outline"],
      fallbacks: [],
    }),
  },
  "GET /api/v1/agent/health/data-coverage": {
    query: { query: TOPIC },
    responseShape: agentEnvelope({
      coverage: { papers: 200, with_full_text: 173, with_sections: 52, with_assets: 198 },
      missing_capabilities: ["external citation/provider coverage not measured"],
      recommended_ingestion: ["continue monitoring corpus coverage"],
      risk_level: "low",
    }),
  },
  "GET /api/v1/papers": {
    query: { page: 1, per_page: 5, sort_by: "created_at", order: "desc" },
    responseShape: {
      items: [
        {
          id: PAPER_ID,
          arxiv_id: ARXIV_ID,
          title: TOPIC,
          abstract: ABSTRACT_SNIPPET,
          has_full_text: true,
          ingestion_status: "index_failed",
        },
      ],
      total: 5794,
      page: 1,
      per_page: 5,
    },
  },
  "GET /api/v1/collections": {
    query: { kind: "workspace" },
    responseShape: [
      {
        id: "workspace-local",
        name: "Local research workspace",
        kind: "workspace",
      },
    ],
  },
  "GET /api/v1/search": {
    query: { q: TOPIC, mode: "hybrid", page: 1, per_page: 10 },
    responseShape: {
      hits: [],
      total: 0,
      query: TOPIC,
      mode: "hybrid",
    },
  },
  "POST /api/v1/auth/login": {
    body: { username: "demo", password: "demo" },
    responseShape: {
      access_token: "single-user-mode",
      user_id: "default",
      mode: "single_user",
    },
  },
  "POST /api/v1/paper-qa/{paper_id}/ask": {
    pathParams: { paper_id: PAPER_ID },
    body: {
      question: QUESTION,
      top_k: 5,
      stream: false,
    },
    responseShape: {
      answer:
        "The paper proposes dual-view training for instruction-following retrieval, using polarity reversal to create complementary instructions.",
      citations: [{ anchor: "E1", paper_id: PAPER_ID, section_title: "Abstract" }],
      confidence: 0.95,
      evidence: [liveEvidenceItem],
    },
  },
};

export function getApiExampleProfile(
  endpointId: string,
): ApiExampleProfile | null {
  return (
    getRuntimeApiExampleProfile(endpointId) ??
    API_EXAMPLE_REGISTRY[endpointId] ??
    null
  );
}
