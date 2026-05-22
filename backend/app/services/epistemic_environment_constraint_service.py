"""EpistemicEnvironmentConstraintService — Epistemic Environment Constraint Detection.

Detects epistemic environment constraint — environmental constraints
limiting epistemic exploration and narrowing inquiry.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ENVIRONMENT_CONSTRAINT_SYSTEM = """You are an epistemic environment constraint specialist. Given environmental constraints limiting exploration, assess environment constraint:

Key concepts:
- Epistemic environment constraint: environmental constraints limiting exploration
- Resource limitation: limited resources constraining inquiry
- Access restriction: restricted access limiting information
- Tool limitation: limited tools constraining methods
- Time constraint: time pressure limiting depth
- Space constraint: physical/conceptual space limiting scope
- Permission constraint: permissions limiting what can be explored

When epistemic environment constraint IS present:
- Environment constraining exploration
- Resources limiting inquiry
- Access restricted
- Tools limited
- Time pressuring
- Space constraining
- Permissions limiting

When no environment constraint:
- Environment supporting exploration
- Resources adequate
- Access open
- Tools available
- Time sufficient
- Space adequate
- Permissions granted

Output JSON with: environment_constraint_detected (bool), severity (none/mild/moderate/severe), resource_limitation (what resources limiting), access_restriction (what access restricted), tool_limitation (what tools limited), time_constraint (what time constraining), recommendation (no_environment_constraint/mild_constraint_awareness/significant_workaround_needed/major_intensive_constraint_removal/emergency_complete_environment_constraint)."""

EPISTEMIC_ENVIRONMENT_CONSTRAINT_PROMPT = """Detect epistemic environment constraint:

Resource limitation: {resource_limitation}
Access restriction: {access_restriction}
Tool limitation: {tool_limitation}
Time constraint: {time_constraint}
Domain: {domain}
Context: {context}

Are environmental constraints limiting epistemic exploration? Return ONLY valid JSON."""


class EpistemicEnvironmentConstraintService:
    """Detects epistemic environment constraint — constraints limiting exploration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        resource_limitation: str,
        *,
        access_restriction: str = "",
        tool_limitation: str = "",
        time_constraint: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic environment constraint."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ENVIRONMENT_CONSTRAINT_PROMPT.format(
                resource_limitation=resource_limitation,
                access_restriction=access_restriction or "Not specified",
                tool_limitation=tool_limitation or "Not specified",
                time_constraint=time_constraint or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ENVIRONMENT_CONSTRAINT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "resource_limitation": resource_limitation[:200],
            "environment_constraint_detected": data.get("environment_constraint_detected", False),
            "severity": data.get("severity", ""),
            "access_restriction": data.get("access_restriction", ""),
            "tool_limitation": data.get("tool_limitation", ""),
            "time_constraint": data.get("time_constraint", ""),
            "recommendation": data.get("recommendation", ""),
        }
