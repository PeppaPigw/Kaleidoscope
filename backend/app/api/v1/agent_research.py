"""Agent-native research APIs for autonomous scientific agents."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, Path, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.services.agent_api_catalog import AgentApiSpec, load_agent_api_specs
from app.services.agent_research_runtime import AgentResearchRuntime

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


def _body_to_dict(body: AgentApiRequest | None) -> dict[str, Any]:
    if body is None:
        return {}
    return body.model_dump(mode="json", by_alias=True)


def _make_route_handler(spec: AgentApiSpec):
    async def route_handler(
        request: Request,
        body: AgentApiRequest | None = None,
        db: AsyncSession | None = None,
        user_id: str | None = None,
        **path_params: Any,
    ) -> AgentApiEnvelope:
        runtime = AgentResearchRuntime(db, user_id or "default")  # type: ignore[arg-type]
        data, warnings, provenance = await runtime.run(
            spec=spec,
            request=request,
            body=_body_to_dict(body),
            path_params=path_params,
        )
        generated_at = datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")
        return AgentApiEnvelope(
            data=data,
            meta={
                "request_id": f"req_{uuid4().hex}",
                "api_version": "v1",
                "source": "local_runtime",
                "generated_at": generated_at,
                "cache": {"hit": False, "ttl_seconds": 0},
                "cost": {"estimated_tokens": 0, "external_calls": []},
                "implementation_status": "live_partial" if warnings else "live",
                "catalog_id": spec.id,
            },
            warnings=warnings,
            provenance=provenance,
        )

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
                            "scope": {"paper_ids": ["<paper_id>"]},
                            "language": "auto",
                            "token_budget": 8000,
                            "include_provenance": True,
                            "include_confidence": True,
                            "async": False,
                            "input": {"query": "paper-specific question"},
                        }
                    ],
                ),
            )
        )

    parameters.extend(
        [
            inspect.Parameter(
                "db",
                inspect.Parameter.KEYWORD_ONLY,
                annotation=AsyncSession,
                default=Depends(get_db),
            ),
            inspect.Parameter(
                "user_id",
                inspect.Parameter.KEYWORD_ONLY,
                annotation=str,
                default=Depends(get_current_user_id),
            ),
        ]
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
                "Returns a JSON envelope backed by the local Kaleidoscope corpus; "
                "missing artifacts are reported as warnings instead of fabricated samples. "
                "Response fields include: "
                f"{', '.join(spec.response_highlights) or 'result, status, warnings'}."
            ),
            operation_id=spec.operation_id,
        )


_register_routes()
