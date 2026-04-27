"""Machine-readable readiness profiles for agent-facing API operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from app.services.agent_api_catalog import AgentApiSpec

AgentEndpointStatus = Literal["production", "beta", "planned", "deprecated"]
AgentResponseMode = Literal["agent_envelope", "raw_json"]

DEFAULT_PAPER_ID = "31a1d910-a440-4a71-8614-93bc570f7a5d"
DEFAULT_TOPIC = "Dual-View Training for Instruction-Following Information Retrieval"
DEFAULT_ARXIV_ID = "2604.18845"
DEFAULT_QUESTION = DEFAULT_TOPIC

DEFAULT_FAILURE_MODES = (
    {
        "code": "INSUFFICIENT_LOCAL_CORPUS",
        "meaning": "The local corpus cannot satisfy the requested research task.",
        "agent_action": "Import or process more papers, or broaden the request scope.",
    },
    {
        "code": "ENDPOINT_NOT_PRODUCTIZED",
        "meaning": "The route is discoverable but not reliable enough for autonomous execution.",
        "agent_action": "Use a production fallback endpoint from the contract.",
    },
)

DEFAULT_COST = {
    "latency_class": "interactive",
    "token_cost_class": "medium",
    "external_calls": "none_by_default",
    "cacheable": True,
}


@dataclass(frozen=True)
class AgentEndpointProfile:
    """Readiness, examples, and semantic checks for one agent operation."""

    operation_id: str
    method: str
    path: str
    status: AgentEndpointStatus
    workflow_stage: str
    request_example: dict[str, Any] = field(default_factory=dict)
    response_example: dict[str, Any] = field(default_factory=dict)
    semantic_assertions: tuple[str, ...] = ()
    requires_fixture: bool = False
    minimum_data_keys: tuple[str, ...] = ()
    allow_generic_runtime: bool = False
    use_case: str = ""
    priority: str = ""
    purpose: str = ""
    when_to_use: tuple[str, ...] = ()
    do_not_use_when: tuple[str, ...] = ()
    inputs: dict[str, Any] = field(default_factory=dict)
    output_contract: dict[str, Any] = field(default_factory=dict)
    failure_modes: tuple[dict[str, Any], ...] = DEFAULT_FAILURE_MODES
    fallbacks: tuple[str, ...] = ()
    cost: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_COST))
    runtime_example_id: str = ""
    response_mode: AgentResponseMode = "agent_envelope"
    response_root: str = "data"

    @property
    def key(self) -> str:
        return endpoint_key(self.method, self.path)

    def manifest_entry(self) -> dict[str, Any]:
        """Return a compact profile shape suitable for agent discovery."""
        contract = self.agent_contract()
        return {
            "operation_id": self.operation_id,
            "method": self.method,
            "path": self.path,
            "status": self.status,
            "workflow_stage": self.workflow_stage,
            "priority": self.priority,
            "use_case": self.use_case,
            "purpose": contract["purpose"],
            "when_to_use": contract["when_to_use"],
            "do_not_use_when": contract["do_not_use_when"],
            "request_example": self.request_example,
            "response_example": self.response_example,
            "semantic_assertions": list(self.semantic_assertions),
            "minimum_data_keys": list(self.minimum_data_keys),
            "requires_fixture": self.requires_fixture,
            "contract": contract,
        }

    def agent_contract(self) -> dict[str, Any]:
        """Return the executable contract consumed by docs and verifiers."""
        path_prefix = "" if self.response_root == "$" else f"{self.response_root}."
        required_paths = [
            path if "." in path else f"{path_prefix}{path}"
            for path in self.minimum_data_keys
        ]
        output_contract = {
            "required_paths": required_paths,
            "minimum_non_empty_paths": required_paths if self.status == "production" else [],
            "stable_fields": list(self.minimum_data_keys),
            "next_step_inputs": {},
            **self.output_contract,
        }
        inputs = {
            "required": ["scope.paper_ids or scope.topic"],
            "recommended": [
                "token_budget",
                "include_provenance",
                "include_confidence",
            ],
            "accepted_identifiers": ["paper_id", "collection_id", "topic"],
            **self.inputs,
        }
        return {
            "purpose": self.purpose or self.use_case,
            "when_to_use": list(
                self.when_to_use
                or (f"Use when an agent needs to {self.use_case[:1].lower()}{self.use_case[1:]}",)
            ),
            "do_not_use_when": list(
                self.do_not_use_when
                or (
                    "Do not use as a production dependency when status is planned.",
                    "Do not use without a paper, collection, or topic scope when the endpoint requires local evidence.",
                )
            ),
            "inputs": inputs,
            "output_contract": output_contract,
            "failure_modes": list(self.failure_modes),
            "fallbacks": list(self.fallbacks),
            "cost": self.cost,
            "runtime_example_id": self.runtime_example_id or self.key,
            "response_mode": self.response_mode,
            "response_root": self.response_root,
        }


def endpoint_key(method: str, path: str) -> str:
    """Build the canonical profile lookup key."""
    return f"{method.upper()} {path}"


def _agent_body(
    input_values: dict[str, Any] | None = None,
    *,
    scope: dict[str, Any] | None = None,
    token_budget: int = 2048,
) -> dict[str, Any]:
    return {
        "scope": scope
        or {"paper_ids": [DEFAULT_PAPER_ID], "topic": DEFAULT_TOPIC},
        "language": "auto",
        "token_budget": token_budget,
        "include_provenance": True,
        "include_confidence": True,
        "async": False,
        "input": {"query": DEFAULT_TOPIC, **(input_values or {})},
    }


def _agent_envelope(data: dict[str, Any], status: str = "production") -> dict[str, Any]:
    return {
        "data": data,
        "meta": {
            "request_id": "req_...",
            "api_version": "v1",
            "source": "local_runtime",
            "implementation_status": status,
        },
        "warnings": [],
        "provenance": [
            {
                "source": "kaleidoscope.local_runtime",
                "confidence": 1.0,
            }
        ],
    }


PRODUCTION_DYNAMIC_IDS = {
    "A01",
    "A03",
    "A04",
    "A05",
    "A10",
    "B01",
    "B02",
    "B03",
    "B07",
    "D14",
    "D02",
    "D04",
    "D06",
    "D07",
    "D08",
    "E01",
    "E04",
    "H01",
    "H02",
    "H05",
    "H10",
    "I01",
    "I02",
    "I03",
    "J03",
    "J10",
    "K01",
    "K03",
    "K04",
    "K05",
    "L08",
    "L09",
    "L10",
}

WORKFLOW_STAGE_BY_ID = {
    "A01": "acquire_material",
    "A03": "resolve_material",
    "A04": "resolve_material",
    "A05": "prepare_processing",
    "A10": "audit_source_provenance",
    "B01": "read_exact_evidence",
    "B02": "read_exact_evidence",
    "B03": "read_exact_evidence",
    "B07": "extract_paper_understanding",
    "D02": "extract_scientific_objects",
    "D04": "extract_scientific_objects",
    "D06": "extract_scientific_objects",
    "D07": "extract_scientific_objects",
    "D08": "extract_scientific_objects",
    "D14": "extract_scientific_objects",
    "E01": "reproduction_planning",
    "E04": "reproduction_planning",
    "H01": "multi_paper_synthesis",
    "H02": "multi_paper_synthesis",
    "H05": "multi_paper_synthesis",
    "H10": "multi_paper_synthesis",
    "I01": "reproduction_planning",
    "I02": "reproduction_planning",
    "I03": "reproduction_planning",
    "J03": "agent_orchestration",
    "J10": "agent_discovery",
    "K01": "citation_safe_output",
    "K03": "citation_safe_output",
    "K04": "citation_safe_output",
    "K05": "citation_safe_output",
    "L08": "research_planning",
    "L09": "research_planning",
    "L10": "readiness_monitoring",
}

REQUEST_EXAMPLES_BY_ID: dict[str, dict[str, Any]] = {
    "A01": _agent_body({"source": f"https://arxiv.org/abs/{DEFAULT_ARXIV_ID}"}),
    "A03": _agent_body({"identifier": DEFAULT_ARXIV_ID}),
    "A04": _agent_body({"title": DEFAULT_TOPIC}),
    "H01": _agent_body({"query": DEFAULT_TOPIC}),
    "H02": _agent_body({"query": DEFAULT_TOPIC}),
    "H05": _agent_body({"query": DEFAULT_TOPIC}),
    "H10": _agent_body({"query": DEFAULT_TOPIC}),
    "J03": _agent_body({"task": "write a grounded literature review"}),
    "D14": _agent_body({"claims": ["The method improves retrieval quality."]}),
    "K01": _agent_body({"query": DEFAULT_TOPIC}),
    "K03": _agent_body({"query": DEFAULT_TOPIC}),
    "K04": _agent_body({"claims": ["The method improves retrieval quality."]}),
    "K05": _agent_body({"format": "bibtex"}),
    "L08": _agent_body({"objective": "write a grounded literature review"}),
    "L09": _agent_body({"task": "write a grounded literature review"}),
    "I02": _agent_body({"objective": "replicate the paper results"}),
}

RESPONSE_EXAMPLES_BY_ID: dict[str, dict[str, Any]] = {
    "A01": _agent_envelope(
        {
            "paper_id": "string | null",
            "job_id": "string | null",
            "detected_ids": {},
            "source_type": "arxiv | doi | pdf_url | url | title_or_identifier",
            "dedupe_status": "duplicate | new_or_unresolved",
            "next_actions": [],
        }
    ),
    "A03": _agent_envelope(
        {
            "canonical_id": DEFAULT_ARXIV_ID,
            "ids": {"arxiv_id": DEFAULT_ARXIV_ID},
            "title": DEFAULT_TOPIC,
            "confidence": 1.0,
            "local_paper_id": DEFAULT_PAPER_ID,
            "source": "local_database",
        }
    ),
    "B02": _agent_envelope(
        {
            "sections": [
                {
                    "title": "Introduction",
                    "normalized_type": "introduction",
                    "token_count": 320,
                }
            ]
        }
    ),
    "J03": _agent_envelope(
        {"task": "write a grounded literature review", "context_blocks": [], "tool_suggestions": []}
    ),
    "J10": _agent_envelope(
        {
            "capabilities": [],
            "input_schema": "AgentApiRequest",
            "output_schema": "AgentApiEnvelope",
            "rate_limits": {"default_api_key": "configured_by_server"},
        }
    ),
    "L10": _agent_envelope(
        {
            "coverage": {"papers": 0, "with_full_text": 0, "with_sections": 0},
            "missing_capabilities": [],
            "recommended_ingestion": [],
            "risk_level": "low | medium | high",
        }
    ),
}

MINIMUM_DATA_KEYS_BY_ID: dict[str, tuple[str, ...]] = {
    "A01": ("source_type", "dedupe_status", "next_actions"),
    "A03": ("canonical_id", "ids", "confidence"),
    "A04": ("candidates", "source", "match_score"),
    "A05": ("available_outputs", "recommended_jobs"),
    "A10": ("source_urls", "external_ids", "trust_score"),
    "B01": ("section_type", "markdown", "paragraphs"),
    "B02": ("sections",),
    "B03": ("paragraphs",),
    "B07": ("abstract", "keywords"),
    "D02": ("contributions",),
    "D04": ("limitations",),
    "D06": ("method_name", "inputs", "outputs"),
    "D07": ("datasets", "metrics"),
    "D08": ("results",),
    "D14": ("claim_evidence", "support", "missing_evidence"),
    "E01": ("artifacts", "artifact_type", "source"),
    "E04": ("repo_url", "languages", "entrypoints"),
    "H01": ("claims", "papers", "matrix"),
    "H02": ("methods", "dimensions"),
    "H05": ("gaps", "suggested_work"),
    "H10": ("steps", "paper_ids"),
    "I01": ("checklist", "missing_artifacts", "difficulty"),
    "I02": ("steps", "environment", "validation_metrics"),
    "I03": ("python", "packages", "hardware"),
    "J03": ("task", "context_blocks", "tool_suggestions"),
    "J10": ("capabilities", "input_schema", "output_schema"),
    "K01": ("outline", "required_evidence"),
    "K03": ("repairs", "confidence"),
    "K04": ("grounded_claims", "unsupported_claims", "risk_score"),
    "K05": ("format", "entries"),
    "L08": ("actions", "objective"),
    "L09": ("route", "inputs_needed"),
    "L10": ("coverage", "risk_level"),
}

CONTRACT_OVERRIDES_BY_ID: dict[str, dict[str, Any]] = {
    "A03": {
        "purpose": "Resolve an external identifier to a stable local or canonical paper identity.",
        "when_to_use": (
            "Before reading, verifying, or importing a paper from an arXiv ID, DOI, PMID, PMCID, or URL.",
            "When an agent has a citation-like string and needs a canonical paper candidate.",
        ),
        "inputs": {
            "required": ["input.identifier"],
            "accepted_identifiers": ["arxiv_id", "doi", "pmid", "pmcid", "url"],
        },
        "fallbacks": ("/api/v1/agent/resolve/title", "/api/v1/agent/ingest/source"),
    },
    "B02": {
        "purpose": "Expose the section map so an agent can choose exact paper regions before reading content.",
        "when_to_use": (
            "Before requesting section text from a paper.",
            "Before planning a paper-reading or citation-grounding workflow.",
        ),
        "inputs": {"required": ["path.paper_id"]},
        "output_contract": {
            "stable_fields": ["title", "normalized_type", "paragraphs", "token_count"],
            "next_step_inputs": {
                "data.sections[].normalized_type": [
                    "GET /api/v1/agent/papers/{paper_id}/sections/{section_type}"
                ]
            },
        },
        "fallbacks": ("/api/v1/agent/papers/{paper_id}/paragraphs",),
    },
    "B01": {
        "purpose": "Fetch one normalized paper section as structured text with paragraph evidence.",
        "inputs": {"required": ["path.paper_id", "path.section_type"]},
        "fallbacks": ("/api/v1/agent/papers/{paper_id}/paragraphs",),
    },
    "B03": {
        "purpose": "Fetch paragraph-level evidence units with stable local anchors.",
        "inputs": {"required": ["path.paper_id"]},
        "output_contract": {
            "stable_fields": ["paragraph_id", "section_type", "text", "char_span"],
        },
        "fallbacks": ("/api/v1/agent/evidence/search",),
    },
    "J03": {
        "purpose": "Build a citation-safe context pack for a concrete research task.",
        "when_to_use": (
            "Before drafting a literature review or answer that must cite evidence.",
            "When an agent needs bounded context blocks and suggested next API calls.",
        ),
        "do_not_use_when": (
            "The caller needs raw full text rather than selected context blocks.",
            "No paper, collection, or topic scope is available.",
        ),
        "inputs": {
            "required": ["scope.paper_ids or scope.topic", "input.task"],
            "recommended": ["token_budget", "include_provenance", "include_confidence"],
        },
        "output_contract": {
            "stable_fields": ["paper_id", "paper_title", "section_title", "content", "anchor"],
            "next_step_inputs": {
                "data.context_blocks[].paper_id": [
                    "POST /api/v1/agent/writing/outline",
                    "POST /api/v1/agent/writing/claim-grounding",
                ],
                "data.context_blocks[].anchor": [
                    "POST /api/v1/agent/writing/claim-grounding"
                ],
            },
        },
        "fallbacks": ("/api/v1/agent/evidence/search", "/api/v1/agent/evidence/packs"),
    },
    "J10": {
        "purpose": "Expose production endpoint contracts and workflow contracts for agent bootstrapping.",
        "when_to_use": (
            "At client startup before selecting tools or planning an autonomous research workflow.",
            "When a downstream agent needs machine-readable contracts, examples, readiness status, and rate-limit guidance.",
        ),
        "do_not_use_when": (
            "The caller only needs the stable manifest without runtime capability envelope metadata.",
        ),
        "inputs": {
            "required": [],
            "recommended": ["header.X-API-Key"],
            "accepted_identifiers": [],
        },
        "fallbacks": ("/api/v1/agent/manifest", "/api/openapi.json"),
    },
    "D14": {
        "purpose": "Map claims to exact supporting or missing evidence within a paper.",
        "when_to_use": (
            "After extracting claims from a paper or draft.",
            "Before accepting a claim as grounded in a research output.",
        ),
        "inputs": {"required": ["path.paper_id", "input.claims"]},
        "output_contract": {
            "required_paths": [
                "data.claim_evidence",
                "data.support",
                "data.missing_evidence",
            ],
            "minimum_non_empty_paths": ["data.claim_evidence", "data.support"],
        },
        "fallbacks": ("/api/v1/agent/claims/verify", "/api/v1/agent/evidence/search"),
    },
    "D08": {
        "purpose": "Extract reported result values or result-like deltas for one paper.",
        "output_contract": {
            "required_paths": ["data.results", "data.delta"],
            "minimum_non_empty_paths": ["data.results"],
            "stable_fields": ["results", "metric", "value", "delta", "table_or_figure"],
        },
    },
    "H01": {
        "purpose": "Build an evidence matrix that relates claims, papers, and support levels.",
        "fallbacks": ("/api/v1/agent/context/task-pack", "/api/v1/agent/evidence/packs"),
    },
    "H02": {
        "purpose": "Compare methods across papers using structured local evidence.",
        "fallbacks": ("/api/v1/agent/synthesis/evidence-matrix",),
    },
    "H05": {
        "purpose": "Find evidence-backed gaps and feasible follow-up work for a topic.",
        "fallbacks": ("/api/v1/agent/synthesis/reading-plan",),
    },
    "K01": {
        "purpose": "Create an outline with required evidence slots before drafting.",
        "fallbacks": ("/api/v1/agent/context/task-pack",),
    },
    "K04": {
        "purpose": "Separate grounded claims from unsupported claims before writing or publishing.",
        "inputs": {"required": ["scope.paper_ids or scope.topic", "input.claims"]},
        "output_contract": {
            "required_paths": [
                "data.grounded_claims",
                "data.unsupported_claims",
                "data.risk_score",
            ],
            "minimum_non_empty_paths": ["data.grounded_claims"],
        },
        "fallbacks": ("/api/v1/agent/claims/verify", "/api/v1/agent/evidence/search"),
    },
    "K05": {
        "purpose": "Export bibliography entries for cited papers in the requested format.",
        "inputs": {"required": ["scope.paper_ids", "input.format"]},
    },
    "E01": {
        "purpose": "List linked code, data, model, project, and supplemental artifacts for a paper.",
        "inputs": {"required": ["path.paper_id"]},
        "output_contract": {
            "required_paths": [
                "data.artifacts",
                "data.source",
                "data.confidence",
                "data.missing_artifacts",
            ],
            "minimum_non_empty_paths": ["data.source", "data.missing_artifacts"],
            "stable_fields": [
                "artifacts",
                "artifact_type",
                "url",
                "source",
                "confidence",
                "missing_artifacts",
            ],
        },
        "fallbacks": ("/api/v1/papers/{paper_id}/code-and-data",),
    },
    "E04": {
        "purpose": "Summarize repository structure and runnable-entry hints for reproduction planning.",
        "inputs": {"required": ["path.paper_id"]},
        "output_contract": {
            "required_paths": [
                "data.repo_url",
                "data.repo_status",
                "data.entrypoints",
                "data.recommended_actions",
            ],
            "minimum_non_empty_paths": [
                "data.repo_status",
                "data.entrypoints",
                "data.recommended_actions",
            ],
            "stable_fields": [
                "repo_url",
                "repo_status",
                "languages",
                "entrypoints",
                "install",
                "tests",
                "recommended_actions",
            ],
        },
        "fallbacks": ("/api/v1/agent/papers/{paper_id}/artifact-links",),
    },
    "I01": {
        "purpose": "Return a concrete reproduction checklist with missing artifacts and difficulty.",
        "inputs": {"required": ["path.paper_id"]},
        "fallbacks": ("/api/v1/agent/reproducibility/artifact-audit",),
    },
    "I02": {
        "purpose": "Generate a step-by-step replication plan with environment, data, commands, and metrics.",
        "inputs": {"required": ["path.paper_id", "input.objective"]},
        "fallbacks": ("/api/v1/agent/papers/{paper_id}/reproducibility-checklist",),
    },
    "I03": {
        "purpose": "Extract package, hardware, seed, and runtime assumptions for reproduction.",
        "inputs": {"required": ["path.paper_id"]},
        "fallbacks": ("/api/v1/agent/papers/{paper_id}/reproducibility-checklist",),
    },
}


def _contract_kwargs_for_spec(spec: AgentApiSpec) -> dict[str, Any]:
    """Return contract-oriented profile overrides for a roadmap endpoint."""
    override = dict(CONTRACT_OVERRIDES_BY_ID.get(spec.id, {}))
    override.setdefault("runtime_example_id", spec.key)
    return override


DISCOVERY_INPUTS = {
    "required": [],
    "recommended": ["header.X-API-Key"],
    "accepted_identifiers": [],
}

EVIDENCE_SEARCH_INPUTS = {
    "required": ["body.query"],
    "recommended": ["body.paper_ids", "body.top_k", "body.include_paper_fallback"],
    "accepted_identifiers": ["paper_id", "topic", "collection_id"],
}

EVIDENCE_PACK_INPUTS = {
    "required": ["body.query"],
    "recommended": ["body.paper_ids", "body.top_k", "body.token_budget"],
    "accepted_identifiers": ["paper_id", "topic", "collection_id"],
}

CLAIM_VERIFY_INPUTS = {
    "required": ["body.claim"],
    "recommended": ["body.paper_ids", "body.top_k"],
    "accepted_identifiers": ["paper_id", "claim", "topic"],
}

TEXT_EXTRACTION_INPUTS = {
    "required": ["body.text"],
    "recommended": ["body.paper_ids"],
    "accepted_identifiers": ["paper_id"],
}

LITERATURE_MAP_INPUTS = {
    "required": ["body.topic or body.paper_ids"],
    "recommended": ["body.limit"],
    "accepted_identifiers": ["paper_id", "topic", "collection_id"],
}


STATIC_PROFILES: dict[str, AgentEndpointProfile] = {
    endpoint_key("GET", "/api/v1/agent/manifest"): AgentEndpointProfile(
        operation_id="get_agent_manifest",
        method="GET",
        path="/api/v1/agent/manifest",
        status="production",
        workflow_stage="agent_discovery",
        response_example={
            "schema_version": "1.0.0",
            "auth": {"header_example": {"X-API-Key": "sk-kaleidoscope"}},
            "rest_capabilities": [],
            "recommended_workflows": [],
        },
        semantic_assertions=(
            "manifest includes auth.header_example.X-API-Key",
            "manifest includes rest_capabilities and recommended_workflows",
        ),
        minimum_data_keys=("schema_version", "tools", "rest_capabilities"),
        use_case="Discover agent tools, REST capabilities, auth, examples, and workflow guidance.",
        priority="P0",
        inputs=DISCOVERY_INPUTS,
        response_mode="raw_json",
        response_root="$",
        runtime_example_id="agent-manifest",
    ),
    endpoint_key("POST", "/api/v1/agent/evidence/search"): AgentEndpointProfile(
        operation_id="search_evidence_agent_alias",
        method="POST",
        path="/api/v1/agent/evidence/search",
        status="production",
        workflow_stage="read_exact_evidence",
        request_example={
            "query": DEFAULT_QUESTION,
            "paper_ids": [DEFAULT_PAPER_ID],
            "top_k": 5,
            "include_paper_fallback": True,
        },
        minimum_data_keys=("evidence", "query"),
        use_case="Search local evidence snippets through an agent namespace alias.",
        priority="P0",
        inputs=EVIDENCE_SEARCH_INPUTS,
        response_mode="raw_json",
        response_root="$",
        runtime_example_id="agent-evidence-search-alias",
    ),
    endpoint_key("POST", "/api/v1/agent/evidence/packs"): AgentEndpointProfile(
        operation_id="build_evidence_pack_agent_alias",
        method="POST",
        path="/api/v1/agent/evidence/packs",
        status="production",
        workflow_stage="read_exact_evidence",
        request_example={
            "query": DEFAULT_QUESTION,
            "paper_ids": [DEFAULT_PAPER_ID],
            "top_k": 8,
            "token_budget": 2048,
        },
        minimum_data_keys=("evidence", "budget", "citations"),
        use_case="Build a token-budgeted evidence pack through an agent namespace alias.",
        priority="P0",
        inputs=EVIDENCE_PACK_INPUTS,
        response_mode="raw_json",
        response_root="$",
    ),
    endpoint_key("POST", "/api/v1/agent/claims/verify"): AgentEndpointProfile(
        operation_id="verify_claim_agent_alias",
        method="POST",
        path="/api/v1/agent/claims/verify",
        status="production",
        workflow_stage="extract_scientific_objects",
        request_example={
            "claim": "The method improves retrieval quality.",
            "paper_ids": [DEFAULT_PAPER_ID],
            "top_k": 5,
        },
        minimum_data_keys=("label", "confidence", "evidence_pack"),
        use_case="Verify a claim against local evidence through an agent namespace alias.",
        priority="P0",
        inputs=CLAIM_VERIFY_INPUTS,
        response_mode="raw_json",
        response_root="$",
        runtime_example_id="agent-claim-verify-alias",
    ),
    endpoint_key("POST", "/api/v1/agent/citations/intent-classify"): AgentEndpointProfile(
        operation_id="classify_citation_intent_agent_alias",
        method="POST",
        path="/api/v1/agent/citations/intent-classify",
        status="production",
        workflow_stage="citation_intelligence",
        request_example={
            "contexts": ["We compare against this baseline in the evaluation section."]
        },
        minimum_data_keys=("results", "total"),
        use_case="Classify citation context intent through an agent namespace alias.",
        priority="P1",
        inputs={
            "required": ["body.contexts or body.context"],
            "recommended": [],
            "accepted_identifiers": [],
        },
        response_mode="raw_json",
        response_root="$",
    ),
    endpoint_key("POST", "/api/v1/agent/benchmarks/extract"): AgentEndpointProfile(
        operation_id="extract_benchmarks_agent_alias",
        method="POST",
        path="/api/v1/agent/benchmarks/extract",
        status="production",
        workflow_stage="extract_scientific_objects",
        request_example={
            "text": "On SciAgent, accuracy reaches 87.5% using an A100 GPU.",
            "paper_ids": [DEFAULT_PAPER_ID],
        },
        minimum_data_keys=("benchmarks", "datasets", "metrics"),
        use_case="Extract benchmark metrics through an agent namespace alias.",
        priority="P1",
        inputs=TEXT_EXTRACTION_INPUTS,
        response_mode="raw_json",
        response_root="$",
    ),
    endpoint_key("POST", "/api/v1/agent/literature/review-map"): AgentEndpointProfile(
        operation_id="literature_review_map_agent_alias",
        method="POST",
        path="/api/v1/agent/literature/review-map",
        status="production",
        workflow_stage="multi_paper_synthesis",
        request_example={"topic": DEFAULT_TOPIC, "paper_ids": [DEFAULT_PAPER_ID], "limit": 20},
        minimum_data_keys=("nodes", "edges", "themes"),
        use_case="Build a review map through an agent namespace alias.",
        priority="P1",
        inputs=LITERATURE_MAP_INPUTS,
        response_mode="raw_json",
        response_root="$",
    ),
    endpoint_key("POST", "/api/v1/agent/literature/related-work-pack"): AgentEndpointProfile(
        operation_id="related_work_pack_agent_alias",
        method="POST",
        path="/api/v1/agent/literature/related-work-pack",
        status="production",
        workflow_stage="multi_paper_synthesis",
        request_example={"topic": DEFAULT_TOPIC, "paper_ids": [DEFAULT_PAPER_ID], "limit": 20},
        minimum_data_keys=("nodes", "edges", "reading_order"),
        use_case="Build a related-work pack through an agent namespace alias.",
        priority="P1",
        inputs=LITERATURE_MAP_INPUTS,
        response_mode="raw_json",
        response_root="$",
    ),
    endpoint_key("POST", "/api/v1/agent/literature/contradiction-map"): AgentEndpointProfile(
        operation_id="contradiction_map_agent_alias",
        method="POST",
        path="/api/v1/agent/literature/contradiction-map",
        status="production",
        workflow_stage="multi_paper_synthesis",
        request_example={"topic": DEFAULT_TOPIC, "paper_ids": [DEFAULT_PAPER_ID], "limit": 20},
        minimum_data_keys=("nodes", "edges", "contradictions"),
        use_case="Build a contradiction map through an agent namespace alias.",
        priority="P1",
        inputs=LITERATURE_MAP_INPUTS,
        response_mode="raw_json",
        response_root="$",
    ),
}


def _status_for_spec(spec: AgentApiSpec) -> AgentEndpointStatus:
    if spec.id in PRODUCTION_DYNAMIC_IDS:
        return "production"
    if spec.priority == "P0":
        return "beta"
    return "planned"


def profile_for_spec(spec: AgentApiSpec) -> AgentEndpointProfile:
    """Create the readiness profile for a dynamic roadmap-backed endpoint."""
    status = _status_for_spec(spec)
    key = endpoint_key(spec.method, spec.path)
    if key in STATIC_PROFILES:
        return STATIC_PROFILES[key]
    contract_kwargs = _contract_kwargs_for_spec(spec)

    return AgentEndpointProfile(
        operation_id=spec.operation_id,
        method=spec.method,
        path=spec.path,
        status=status,
        workflow_stage=WORKFLOW_STAGE_BY_ID.get(spec.id, spec.section.lower().replace(" ", "_")),
        request_example=REQUEST_EXAMPLES_BY_ID.get(spec.id, {}),
        response_example=RESPONSE_EXAMPLES_BY_ID.get(spec.id, {}),
        semantic_assertions=tuple(
            f"data.{field.removesuffix('[]')} is present"
            for field in spec.response_highlights
        ),
        requires_fixture=spec.id[:1] in {"B", "C", "D", "E", "F", "I"},
        minimum_data_keys=MINIMUM_DATA_KEYS_BY_ID.get(
            spec.id,
            tuple(field.removesuffix("[]") for field in spec.response_highlights[:3]),
        ),
        allow_generic_runtime=status != "production",
        use_case=spec.use_case,
        priority=spec.priority,
        **contract_kwargs,
    )


def profile_for_operation(
    method: str,
    path: str,
    operation_id: str | None = None,
) -> AgentEndpointProfile | None:
    """Return a static or dynamic profile for an operation."""
    key = endpoint_key(method, path)
    static = STATIC_PROFILES.get(key)
    if static:
        return static

    from app.services.agent_api_catalog import load_agent_api_specs

    for spec in load_agent_api_specs():
        if endpoint_key(spec.method, spec.path) == key or (
            operation_id and spec.operation_id == operation_id
        ):
            return profile_for_spec(spec)
    return None


def iter_agent_endpoint_profiles() -> tuple[AgentEndpointProfile, ...]:
    """Return all known dynamic and static agent endpoint profiles."""
    from app.services.agent_api_catalog import load_agent_api_specs

    dynamic = [profile_for_spec(spec) for spec in load_agent_api_specs()]
    static_keys = {profile.key for profile in dynamic}
    static = [
        profile
        for key, profile in STATIC_PROFILES.items()
        if key not in static_keys
    ]
    return tuple([*static, *dynamic])


def implementation_status_for_response(
    profile: AgentEndpointProfile,
    warnings: list[dict[str, Any] | str],
) -> str:
    """Derive the public response status from profile readiness and warnings."""
    if profile.status == "production" and warnings:
        return "degraded_missing_local_data"
    return profile.status
