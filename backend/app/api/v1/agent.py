"""Agent Tool API — REST endpoints for AI agent integration.

Exposes Kaleidoscope capabilities as tool calls over HTTP.
This is a custom REST interface, NOT the MCP (Model Context Protocol)
wire format. Agents using MCP transport should use the dedicated
MCP stdio/SSE server (planned for P2).

The tool registry and dispatcher are shared — when a real MCP server
is added, it will reuse the same TOOLS list and MCPToolDispatcher.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.services.agent.context_pack import AgentContextPackService
from app.services.agent.manifest import build_agent_manifest
from app.services.agent.tool_dispatcher import TOOLS, ToolDispatcher

router = APIRouter(prefix="/agent", tags=["agent"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
UserId = Annotated[str, Depends(get_current_user_id)]


# ─── Request / Response Schemas ──────────────────────────────────


class ToolCallRequest(BaseModel):
    """Tool call request."""

    tool: str = Field(..., description="Tool name to invoke")
    arguments: dict = Field(default_factory=dict, description="Tool arguments")


class ToolCallResponse(BaseModel):
    """Tool call response."""

    tool: str
    result: dict | list | str
    is_error: bool = False


class ContextPackRequest(BaseModel):
    """Request body for building an agent context pack."""

    paper_ids: list[str] = Field(default_factory=list, max_length=100)
    collection_id: str | None = Field(default=None, max_length=100)
    question: str | None = Field(default=None, max_length=2000)
    token_budget: int = Field(default=4000, ge=500, le=32000)
    include_evidence: bool = True
    evidence_top_k: int = Field(default=8, ge=0, le=30)


# ─── Endpoints ───────────────────────────────────────────────────


@router.get("/manifest")
async def get_agent_manifest() -> dict[str, Any]:
    """Return agent-friendly tool schemas, scopes, costs, and examples."""
    return build_agent_manifest()


@router.get("/tools")
async def list_tools():
    """
    List all available tools.

    Returns the tool registry with names, descriptions,
    and parameter schemas. AI agents use this to discover
    available capabilities.
    """
    return {"tools": TOOLS}




@router.post("/context-pack")
async def build_context_pack(
    body: ContextPackRequest,
    db: DbSession,
    user_id: UserId,
) -> dict[str, Any]:
    """Return compressed, cited JSON context optimized for agent token budgets."""
    return await AgentContextPackService(db, user_id=user_id).build_context_pack(
        paper_ids=body.paper_ids,
        collection_id=body.collection_id,
        question=body.question,
        token_budget=body.token_budget,
        include_evidence=body.include_evidence,
        evidence_top_k=body.evidence_top_k,
    )


@router.post("/call", response_model=ToolCallResponse)
async def call_tool(
    body: ToolCallRequest,
    db: DbSession,
):
    """
    Execute a single tool call.

    The agent specifies a tool name and arguments,
    and receives structured results.
    """
    dispatcher = ToolDispatcher(db)
    result = await dispatcher.call_tool(body.tool, body.arguments)

    is_error = isinstance(result, dict) and "error" in result
    return ToolCallResponse(
        tool=body.tool,
        result=result,
        is_error=is_error,
    )


@router.post("/batch")
async def batch_tool_calls(
    calls: list[ToolCallRequest],
    db: DbSession,
):
    """
    Execute multiple tool calls in sequence.

    Useful for agents that need to gather information
    from multiple sources in a single request.
    """
    dispatcher = ToolDispatcher(db)
    results = []
    for call in calls[:20]:  # Cap at 20 calls per batch
        result = await dispatcher.call_tool(call.tool, call.arguments)
        results.append(
            ToolCallResponse(
                tool=call.tool,
                result=result,
                is_error=isinstance(result, dict) and "error" in result,
            )
        )
    return {"results": results}
