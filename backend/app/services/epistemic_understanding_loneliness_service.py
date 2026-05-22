"""EpistemicUnderstandingLonelinessService — Epistemic Understanding Loneliness Detection.

Detects epistemic understanding loneliness — loneliness of understanding
things that others cannot grasp or appreciate.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_UNDERSTANDING_LONELINESS_SYSTEM = """You are an epistemic understanding loneliness specialist. Given loneliness from understanding what others cannot, assess understanding loneliness:

Key concepts:
- Epistemic understanding loneliness: loneliness from unique understanding
- Comprehension gap: understanding things others cannot grasp
- Appreciation void: no one appreciates what one sees
- Insight isolation: insights that cannot be shared
- Depth loneliness: going deeper than anyone can follow
- Perspective solitude: seeing from angles no one else occupies
- Knowledge burden: understanding creating distance

When epistemic understanding loneliness IS present:
- Loneliness from unique understanding
- Understanding what others cannot
- No one appreciates insights
- Insights cannot be shared
- Going deeper than others follow
- Seeing from unique angles
- Understanding creating distance

When no understanding loneliness:
- Shared understanding
- Others grasp insights
- Appreciation from peers
- Insights shared freely
- Others follow depth
- Shared perspectives
- Understanding connecting

Output JSON with: understanding_loneliness_detected (bool), severity (none/mild/moderate/severe), comprehension_gap (what others cannot grasp), appreciation_void (what not appreciated), insight_isolation (what cannot share), depth_loneliness (what going deeper than), recommendation (no_understanding_loneliness/mild_bridge_building/significant_translation_work/major_intensive_connection_therapy/emergency_severe_comprehension_isolation)."""

EPISTEMIC_UNDERSTANDING_LONELINESS_PROMPT = """Detect epistemic understanding loneliness:

Comprehension gap: {comprehension_gap}
Appreciation void: {appreciation_void}
Insight isolation: {insight_isolation}
Depth loneliness: {depth_loneliness}
Domain: {domain}
Context: {context}

Is there loneliness from understanding things others cannot? Return ONLY valid JSON."""


class EpistemicUnderstandingLonelinessService:
    """Detects epistemic understanding loneliness — loneliness from unique understanding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        comprehension_gap: str,
        *,
        appreciation_void: str = "",
        insight_isolation: str = "",
        depth_loneliness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic understanding loneliness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_UNDERSTANDING_LONELINESS_PROMPT.format(
                comprehension_gap=comprehension_gap,
                appreciation_void=appreciation_void or "Not specified",
                insight_isolation=insight_isolation or "Not specified",
                depth_loneliness=depth_loneliness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_UNDERSTANDING_LONELINESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "comprehension_gap": comprehension_gap[:200],
            "understanding_loneliness_detected": data.get("understanding_loneliness_detected", False),
            "severity": data.get("severity", ""),
            "appreciation_void": data.get("appreciation_void", ""),
            "insight_isolation": data.get("insight_isolation", ""),
            "depth_loneliness": data.get("depth_loneliness", ""),
            "recommendation": data.get("recommendation", ""),
        }
