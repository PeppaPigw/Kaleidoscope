"""ScopeSensitivityService — Scope Sensitivity Assessment.

Evaluates whether responses are proportional to the scale of the
problem. Scope insensitivity occurs when people respond similarly
to problems of vastly different magnitudes — caring about one
affected person almost as much as thousands.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SCOPE_SENSITIVITY_SYSTEM = """You are a scope sensitivity specialist. Given a response to a problem, assess whether it is proportional to the scale:

Key concepts:
- Scope insensitivity: similar response regardless of magnitude
- Psychic numbing: inability to feel proportionally to large numbers
- Identified victim effect: one person evokes more response than statistics
- Proportion neglect: ignoring base rates and relative scale
- Unit bias: treating one unit the same regardless of what it represents
- Logarithmic perception: humans perceive scale logarithmically, not linearly
- Affect heuristic: emotional response doesn't scale with magnitude

When scope insensitivity IS present:
- Response is similar regardless of whether 10 or 10,000 are affected
- Resources allocated don't scale with problem magnitude
- Emotional response to one case equals response to systemic issue
- "Saving one life" valued nearly as much as "saving thousands"
- Small sample treated with same urgency as population-level problem
- Anecdote given same weight as large-scale data
- Response calibrated to narrative, not to numbers

When scope sensitivity IS present:
- Response scales appropriately with problem magnitude
- Resources allocated proportionally to scale
- Distinction made between individual cases and systemic patterns
- Large-scale problems receive proportionally more attention
- Numbers and statistics inform the response level
- Both emotional and analytical responses are calibrated to scale
- Triage and prioritization reflect actual magnitude

Output JSON with: scope_sensitive (bool), severity (none/mild/moderate/severe), scale (the actual magnitude of the problem), response_level (how much response is being given), proportionality (over_response/proportional/under_response), scaling_factor (how response should scale), recommendation (well_calibrated/mild_insensitivity/significant_disproportion/major_scope_neglect/recalibrate_to_scale)."""

SCOPE_SENSITIVITY_PROMPT = """Assess scope sensitivity:

Situation: {situation}
Scale: {scale}
Response: {response}
Comparison: {comparison}
Domain: {domain}
Context: {context}

Is the response proportional to the scale of the problem? Return ONLY valid JSON."""


class ScopeSensitivityService:
    """Assesses whether responses are proportional to problem scale."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        situation: str,
        *,
        scale: str = "",
        response: str = "",
        comparison: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess scope sensitivity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SCOPE_SENSITIVITY_PROMPT.format(
                situation=situation,
                scale=scale or "Not specified",
                response=response or "Not specified",
                comparison=comparison or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SCOPE_SENSITIVITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "scope_sensitive": data.get("scope_sensitive", False),
            "severity": data.get("severity", ""),
            "scale": data.get("scale", ""),
            "response_level": data.get("response_level", ""),
            "proportionality": data.get("proportionality", ""),
            "recommendation": data.get("recommendation", ""),
        }
