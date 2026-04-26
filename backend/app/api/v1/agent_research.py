"""Agent-native research APIs for autonomous scientific agents."""

from __future__ import annotations

import hashlib
import inspect
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Body, Path, Request
from pydantic import BaseModel, ConfigDict, Field

from app.services.agent_api_catalog import AgentApiSpec, load_agent_api_specs

router = APIRouter(prefix="/agent")


class AgentApiScope(BaseModel):
    """Common scope selector accepted by heavy agent endpoints."""

    paper_ids: list[str] = Field(default_factory=list)
    collection_id: str | None = None
    topic: str | None = None
    date_range: dict[str, str] | None = None


class AgentApiRequest(BaseModel):
    """Common JSON request controls for agent-native endpoints."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    scope: AgentApiScope = Field(default_factory=AgentApiScope)
    language: str = Field(default="auto", examples=["auto", "en", "zh"])
    token_budget: int = Field(default=8000, ge=1, le=200000)
    include_provenance: bool = True
    include_confidence: bool = True
    force_refresh: bool = False
    async_mode: bool = Field(default=False, alias="async")
    max_depth: int = Field(default=2, ge=0, le=10)
    output_schema: str = "default"
    input: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)


class AgentApiEnvelope(BaseModel):
    """Canonical JSON envelope returned by agent-native APIs."""

    data: dict[str, Any]
    meta: dict[str, Any]
    warnings: list[dict[str, Any] | str] = Field(default_factory=list)
    provenance: list[dict[str, Any]] = Field(default_factory=list)


_SAMPLE_VALUES: dict[str, Any] = {
    "accepted": [{"source": "sample-source", "status": "accepted"}],
    "accepted_feedback": True,
    "actions[]": [{"action": "inspect_paper", "expected_value": 0.82}],
    "alert_id": "alert_sample",
    "artifacts[]": [{"artifact_id": "artifact_sample", "artifact_type": "repo"}],
    "available_outputs": ["sections", "figures", "tables", "claims"],
    "baseline": "baseline-system",
    "blocking_unknowns": [],
    "cache_key": "agent-cache-sample",
    "capabilities[]": [{"name": "agent-paper-access", "status": "available"}],
    "checklist[]": [{"item": "environment documented", "status": "unknown"}],
    "citation_slots": [{"slot": "related_work", "required": True}],
    "citations": [{"paper_id": "paper_sample", "span": "paragraph_sample"}],
    "claims[]": [{"claim_id": "claim_sample", "text": "sample claim"}],
    "commands": ["python train.py --help"],
    "confidence": 0.84,
    "content_type": "application/json",
    "current_step": "ready",
    "data": {"rows": []},
    "datasets": [{"name": "sample-dataset", "role": "evaluation"}],
    "depth": 2,
    "draft": "Evidence-grounded draft placeholder.",
    "edges": [],
    "entries": [],
    "event": "agent.event",
    "expires_at": "2026-04-26T00:00:00Z",
    "format": "json",
    "image_url": "https://example.local/assets/sample.png",
    "job_id": "job_sample",
    "license": "unknown",
    "license_note": "Check source license before reuse.",
    "matrix": [],
    "method_name": "sample-method",
    "nodes": [],
    "open_questions": [{"question": "What evidence is still missing?"}],
    "paper_id": "paper_sample",
    "papers[]": [{"paper_id": "paper_sample", "title": "Sample Paper"}],
    "poll_url": "/api/v1/agent/jobs/job_sample/artifact-index",
    "problems[]": [{"problem": "sample open problem"}],
    "query": "sample query",
    "recommendations": ["Collect stronger evidence before writing."],
    "repo_url": "https://github.com/example/repo",
    "request_id": "req_sample",
    "result_schema": "default",
    "route[]": [{"method": "GET", "path": "/api/v1/agent/capabilities"}],
    "score": 0.82,
    "status": "ready",
    "steps": [{"step": 1, "action": "inspect available evidence"}],
    "summary": "Structured agent response placeholder.",
    "thumbnail_url": "https://example.local/assets/sample-thumb.png",
    "token_count": 0,
    "tool_suggestions": ["evidence.search", "papers.sections"],
    "trust_score": 0.75,
    "url": "https://example.local/resource",
    "warnings": [],
    "workflow_id": "workflow_sample",
}


def _sample_for_field(field: str, spec: AgentApiSpec, path_params: dict[str, Any]) -> Any:
    clean_field = field.strip()
    key = clean_field.removesuffix("[]")

    if clean_field in _SAMPLE_VALUES:
        return _SAMPLE_VALUES[clean_field]
    if key in _SAMPLE_VALUES:
        return _SAMPLE_VALUES[key]
    if clean_field.endswith("[]"):
        return [{"id": f"{key}_sample", "label": key.replace("_", " ") }]
    if key.endswith("_id"):
        return path_params.get(key, f"{key}_sample")
    if key in path_params:
        return path_params[key]
    if "url" in key:
        return f"https://example.local/{spec.id.lower()}/{key}"
    if "score" in key or key in {"confidence", "severity", "difficulty"}:
        return 0.82
    if key.startswith("is_") or key.endswith("ed") or key in {"stated", "explicit", "required"}:
        return True
    if key.endswith("s") or key in {"nodes", "edges", "steps", "rows", "columns"}:
        return []
    if key in {"language", "format"}:
        return "json"
    if key in {"status", "decision", "link_status"}:
        return "ready"
    if key in {"page", "depth", "token_count"}:
        return 1
    return f"{key}_sample"


def _body_to_dict(body: AgentApiRequest | None) -> dict[str, Any]:
    if body is None:
        return {}
    return body.model_dump(mode="json", by_alias=True)


def _request_query(request: Request) -> dict[str, Any]:
    query: dict[str, Any] = {}
    for key in request.query_params:
        values = request.query_params.getlist(key)
        query[key] = values if len(values) > 1 else values[0]
    return query


def _stable_job_id(spec: AgentApiSpec, path_params: dict[str, Any], body: dict[str, Any]) -> str:
    seed = f"{spec.id}:{path_params}:{body}".encode()
    return "job_" + hashlib.sha1(seed).hexdigest()[:12]


def build_agent_api_response(
    spec: AgentApiSpec,
    request: Request,
    body: AgentApiRequest | None,
    path_params: dict[str, Any],
) -> AgentApiEnvelope:
    """Build a deterministic JSON response for the agent API contract."""

    body_dict = _body_to_dict(body)
    query = _request_query(request)
    generated_at = datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")
    highlights = spec.response_highlights or ("result", "status", "warnings")
    highlighted_data = {
        field.removesuffix("[]"): _sample_for_field(field, spec, path_params)
        for field in highlights
    }

    if "job_id" in highlighted_data:
        highlighted_data["job_id"] = _stable_job_id(spec, path_params, body_dict)
    if "workflow_id" in highlighted_data:
        highlighted_data["workflow_id"] = _stable_job_id(spec, path_params, body_dict).replace(
            "job_", "workflow_"
        )

    data = {
        **highlighted_data,
        "endpoint_id": spec.id,
        "endpoint": spec.path,
        "http_method": spec.method,
        "priority": spec.priority,
        "capability": spec.section,
        "use_case": spec.use_case,
        "path_params": path_params,
        "query": query,
        "request": body_dict,
    }

    return AgentApiEnvelope(
        data=data,
        meta={
            "request_id": f"req_{uuid4().hex}",
            "api_version": "v1",
            "source": "local|roadmap_contract",
            "generated_at": generated_at,
            "cache": {"hit": False, "ttl_seconds": 0},
            "cost": {"estimated_tokens": 0, "external_calls": []},
            "implementation_status": "available_contract",
            "catalog_id": spec.id,
        },
        warnings=[],
        provenance=[
            {
                "source": "docs/memo/Agent-API.md",
                "locator": spec.id,
                "section": spec.section,
                "confidence": 1.0,
            }
        ],
    )


def _make_route_handler(spec: AgentApiSpec):
    async def route_handler(
        request: Request,
        body: AgentApiRequest | None = None,
        **path_params: Any,
    ) -> AgentApiEnvelope:
        return build_agent_api_response(spec, request, body, path_params)

    parameters: list[inspect.Parameter] = [
        inspect.Parameter(
            "request",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Request,
        )
    ]

    for param_name in spec.path_params:
        parameters.append(
            inspect.Parameter(
                param_name,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=str,
                default=Path(..., description=f"{param_name} path parameter"),
            )
        )

    if spec.method != "GET":
        parameters.append(
            inspect.Parameter(
                "body",
                inspect.Parameter.KEYWORD_ONLY,
                annotation=AgentApiRequest | None,
                default=Body(
                    default=None,
                    examples=[
                        {
                            "scope": {"paper_ids": ["paper_sample"]},
                            "language": "auto",
                            "token_budget": 8000,
                            "include_provenance": True,
                            "include_confidence": True,
                            "async": False,
                            "input": {},
                        }
                    ],
                ),
            )
        )

    route_handler.__signature__ = inspect.Signature(parameters)  # type: ignore[attr-defined]
    route_handler.__name__ = spec.operation_id
    route_handler.__doc__ = spec.use_case
    return route_handler


def _register_routes() -> None:
    for spec in load_agent_api_specs():
        router.add_api_route(
            spec.path.removeprefix("/api/v1/agent"),
            _make_route_handler(spec),
            methods=[spec.method],
            response_model=AgentApiEnvelope,
            status_code=200,
            tags=[spec.tag],
            summary=spec.use_case,
            description=(
                f"Agent API {spec.id} ({spec.priority}) in {spec.section}. "
                "Returns JSON fields: "
                f"{', '.join(spec.response_highlights) or 'result, status, warnings'}."
            ),
            operation_id=spec.operation_id,
        )


_register_routes()
