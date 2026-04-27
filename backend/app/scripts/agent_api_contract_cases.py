"""Endpoint-specific runtime contract cases for agent-facing APIs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentContractCase:
    """One replayable request plus semantic response assertions."""

    case_id: str
    method: str
    path: str
    description: str
    query: dict[str, Any] = field(default_factory=dict)
    body: Any = None
    required_json_paths: tuple[str, ...] = ()
    required_meaningful_json_paths: tuple[str, ...] = ()
    expected_statuses: tuple[int, ...] = (200,)
    requires_runtime_paper: bool = False
    expects_agent_envelope: bool = True


PAPER_ID = "<runtime_paper_id>"
TOPIC = "<runtime_topic>"
IDENTIFIER = "<runtime_identifier>"


def agent_body(input_values: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "scope": {"paper_ids": [PAPER_ID], "topic": TOPIC},
        "language": "auto",
        "token_budget": 2048,
        "include_provenance": True,
        "include_confidence": True,
        "async": False,
        "input": {"query": TOPIC, **(input_values or {})},
    }


AGENT_CONTRACT_CASES: tuple[AgentContractCase, ...] = (
    AgentContractCase(
        case_id="agent-manifest",
        method="GET",
        path="/api/v1/agent/manifest",
        description="Manifest exposes auth, profile-backed REST capabilities, and workflows.",
        required_json_paths=(
            "schema_version",
            "auth.header_example.X-API-Key",
            "rest_capabilities",
            "recommended_workflows",
            "workflows",
        ),
        expects_agent_envelope=False,
    ),
    AgentContractCase(
        case_id="agent-capabilities",
        method="GET",
        path="/api/v1/agent/capabilities",
        description="Capabilities enumerate readiness status and runnable examples.",
        required_json_paths=(
            "data.capabilities",
            "data.workflows",
            "data.input_schema",
            "data.output_schema",
            "data.rate_limits.header",
            "meta.implementation_status",
        ),
    ),
    AgentContractCase(
        case_id="agent-resolve-identifier",
        method="POST",
        path="/api/v1/agent/resolve/identifier",
        description="Identifier resolution returns parsed IDs and confidence.",
        body=agent_body({"identifier": IDENTIFIER}),
        required_json_paths=(
            "data.canonical_id",
            "data.ids",
            "data.confidence",
            "meta.implementation_status",
        ),
    ),
    AgentContractCase(
        case_id="agent-section-map",
        method="GET",
        path="/api/v1/agent/papers/<runtime_paper_id>/section-map",
        description="A runtime paper exposes a section map or a coded missing-paper response.",
        required_json_paths=(
            "data.sections",
            "data.endpoint_id",
            "meta.implementation_status",
        ),
        required_meaningful_json_paths=("data.sections",),
        requires_runtime_paper=True,
    ),
    AgentContractCase(
        case_id="agent-context-task-pack",
        method="POST",
        path="/api/v1/agent/context/task-pack",
        description="Task packs accept scope/input/token controls and return tool suggestions.",
        body=agent_body({"task": "write a grounded literature review"}),
        required_json_paths=(
            "data.task",
            "data.inputs",
            "data.context_blocks",
            "data.tool_suggestions",
            "meta.implementation_status",
        ),
        required_meaningful_json_paths=("data.context_blocks",),
        requires_runtime_paper=True,
    ),
    AgentContractCase(
        case_id="agent-evidence-search-alias",
        method="POST",
        path="/api/v1/agent/evidence/search",
        description="Agent evidence alias reuses the practical evidence service.",
        body={
            "query": TOPIC,
            "paper_ids": [PAPER_ID],
            "top_k": 5,
            "include_paper_fallback": True,
        },
        required_json_paths=("query", "evidence"),
        required_meaningful_json_paths=("evidence",),
        requires_runtime_paper=True,
        expects_agent_envelope=False,
    ),
    AgentContractCase(
        case_id="agent-claim-verify-alias",
        method="POST",
        path="/api/v1/agent/claims/verify",
        description="Agent claim verification alias returns a label and evidence pack.",
        body={
            "claim": TOPIC,
            "paper_ids": [PAPER_ID],
            "top_k": 5,
        },
        required_json_paths=("label", "confidence", "evidence_pack"),
        required_meaningful_json_paths=("evidence_pack.evidence",),
        requires_runtime_paper=True,
        expects_agent_envelope=False,
    ),
    AgentContractCase(
        case_id="agent-data-coverage",
        method="GET",
        path="/api/v1/agent/health/data-coverage",
        description="Data coverage reports local corpus readiness and ingestion recommendations.",
        query={"query": TOPIC},
        required_json_paths=(
            "data.coverage",
            "data.missing_capabilities",
            "data.recommended_ingestion",
            "data.risk_level",
            "meta.implementation_status",
        ),
    ),
)
