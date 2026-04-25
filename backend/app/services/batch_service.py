"""Controlled batch execution for downstream agent workflows."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent.context_pack import AgentContextPackService
from app.services.agent.tool_dispatcher import ToolDispatcher
from app.services.answers.grounded_answer_service import GroundedAnswerService
from app.services.paper_resolver_service import PaperResolverService

SUPPORTED_BATCH_OPERATIONS = {
    "agent.tool",
    "resolve",
    "context_pack",
    "grounded_answer",
}


class BatchService:
    """Execute a bounded ordered batch of independent safe operations."""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    async def execute(self, calls: list[dict[str, Any]]) -> dict[str, Any]:
        """Execute calls in order and return per-call JSON results."""
        results = []
        for index, call in enumerate(calls[:20]):
            call_id = str(call.get("id") or index + 1)
            operation = str(call.get("operation") or "")
            arguments = call.get("arguments", {})
            if arguments is None:
                arguments = {}
            if not isinstance(arguments, dict):
                results.append(self._error(call_id, operation, "arguments must be an object"))
                continue
            try:
                result = await self._execute_one(operation, arguments)
                results.append(
                    {
                        "id": call_id,
                        "operation": operation,
                        "ok": True,
                        "result": result,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                results.append(self._error(call_id, operation, str(exc)))
        return {"results": results, "total": len(results)}

    async def _execute_one(self, operation: str, arguments: dict[str, Any]) -> Any:
        if operation not in SUPPORTED_BATCH_OPERATIONS:
            raise ValueError(f"Unsupported batch operation: {operation}")
        if operation == "agent.tool":
            tool_name = str(arguments.get("tool") or "")
            tool_args = arguments.get("arguments") or {}
            if not tool_name:
                raise ValueError("agent.tool requires a tool name")
            if not isinstance(tool_args, dict):
                raise ValueError("agent.tool arguments must be an object")
            return await ToolDispatcher(self.db).call_tool(tool_name, tool_args)
        if operation == "resolve":
            return await PaperResolverService(self.db).resolve(
                identifier=str(arguments.get("identifier") or ""),
                identifier_type=arguments.get("identifier_type", "auto"),
                include_external=bool(arguments.get("include_external", True)),
                candidate_limit=int(arguments.get("candidate_limit", 5)),
            )
        if operation == "context_pack":
            return await AgentContextPackService(
                self.db,
                user_id=self.user_id,
            ).build_context_pack(
                paper_ids=arguments.get("paper_ids") or [],
                collection_id=arguments.get("collection_id"),
                question=arguments.get("question"),
                token_budget=int(arguments.get("token_budget", 4000)),
                include_evidence=bool(arguments.get("include_evidence", True)),
                evidence_top_k=int(arguments.get("evidence_top_k", 8)),
            )
        return GroundedAnswerService().build_answer(
            question=str(arguments.get("question") or ""),
            evidence_pack=arguments.get("evidence_pack"),
            evidence=arguments.get("evidence") or [],
            style=arguments.get("style", "concise"),
            max_sources=int(arguments.get("max_sources", 8)),
            max_answer_chars=int(arguments.get("max_answer_chars", 4000)),
        )

    @staticmethod
    def _error(call_id: str, operation: str, message: str) -> dict[str, Any]:
        return {
            "id": call_id,
            "operation": operation,
            "ok": False,
            "error": message,
        }
