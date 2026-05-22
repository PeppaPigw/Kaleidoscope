"""PathDependencyBlindnessService — Path Dependency Blindness Detection.

Detects path dependency blindness — failing to recognize how
historical sequence constrains current options, treating the
present as if all paths remain equally available.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PATH_DEPENDENCY_BLINDNESS_SYSTEM = """You are a path dependency blindness specialist. Given a decision or analysis, assess whether path dependencies are being ignored:

Key concepts:
- Path dependency: history constrains future options
- Lock-in: past choices making alternatives increasingly costly
- Switching costs: expense of changing established paths
- Increasing returns: early advantages compounding over time
- Critical junctures: moments where paths diverge irreversibly
- Sunk costs as constraints: past investments limiting future flexibility
- Institutional inertia: organizational momentum from past decisions

When path dependency blindness IS present:
- Options presented as if history doesn't constrain them
- Switching costs not acknowledged
- Lock-in effects ignored
- Past decisions treated as freely reversible
- Institutional inertia not factored in
- Critical junctures not identified
- Analysis assumes clean-slate when path-dependent

When path dependency is recognized:
- Historical constraints explicitly identified
- Switching costs estimated
- Lock-in effects acknowledged
- Feasible vs theoretical options distinguished
- Institutional inertia factored into plans
- Critical junctures identified for future decisions
- Path-dependent recommendations given

Output JSON with: blindness_present (bool), severity (none/mild/moderate/severe), decision (what is being decided), path_constraints (what historical constraints exist), ignored_lock_in (what lock-in effects are missed), switching_costs (what costs of changing path), recommendation (path_dependency_recognized/mild_history_neglect/significant_constraint_blindness/major_path_ignorance/map_historical_constraints)."""

PATH_DEPENDENCY_BLINDNESS_PROMPT = """Detect path dependency blindness:

Decision: {decision}
History: {history}
Current constraints: {constraints}
Options considered: {options}
Domain: {domain}
Context: {context}

Are path dependencies being ignored in this decision? Return ONLY valid JSON."""


class PathDependencyBlindnessService:
    """Detects path dependency blindness — ignoring how history constrains options."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        history: str = "",
        constraints: str = "",
        options: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect path dependency blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PATH_DEPENDENCY_BLINDNESS_PROMPT.format(
                decision=decision,
                history=history or "Not specified",
                constraints=constraints or "Not specified",
                options=options or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PATH_DEPENDENCY_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "blindness_present": data.get("blindness_present", False),
            "severity": data.get("severity", ""),
            "path_constraints": data.get("path_constraints", ""),
            "ignored_lock_in": data.get("ignored_lock_in", ""),
            "switching_costs": data.get("switching_costs", ""),
            "recommendation": data.get("recommendation", ""),
        }
