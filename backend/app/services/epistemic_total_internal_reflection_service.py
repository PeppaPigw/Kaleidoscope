"""EpistemicTotalInternalReflectionService — Epistemic Total Internal Reflection Detection.

Detects epistemic total internal reflection — ideas trapped inside a
dense medium because they hit the boundary at too shallow an angle to escape.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TOTAL_INTERNAL_REFLECTION_SYSTEM = """You are an epistemic total internal reflection specialist. Given an idea trapping pattern, assess whether ideas are trapped inside a dense medium:

Key concepts:
- Epistemic total internal reflection: ideas trapped at boundary
- Critical angle: angle below which ideas cannot escape
- Dense medium: intellectual environment that traps ideas
- Evanescent wave: ideas that partially penetrate but don't escape
- Fiber optic: channel that uses total reflection to guide ideas
- Frustrated reflection: thin barrier allowing some escape
- Snell's law: relationship between angles and media density

When epistemic total internal reflection IS present:
- Ideas trapped inside dense medium at shallow angles
- Angle below which ideas cannot escape the medium
- Dense intellectual environment preventing idea escape
- Ideas partially penetrating boundary but not escaping
- Channels using reflection to guide ideas internally
- Thin barriers occasionally allowing some escape
- Relationship between approach angle and escape probability

When free transmission is present:
- Ideas passing freely through boundaries
- No critical angle preventing escape
- No dense medium trapping ideas
- Ideas fully penetrating boundaries
- No internal guiding through reflection
- All barriers allowing passage
- No angle-dependent trapping

Output JSON with: total_internal_reflection_present (bool), severity (none/mild/moderate/severe), critical_angle (what angle prevents escape), dense_medium (what traps ideas), evanescent (what partially penetrates), fiber (what guides internally), recommendation (free_transmission/mild_trapping/significant_reflection/major_internal_trapping/reduce_medium_density)."""

EPISTEMIC_TOTAL_INTERNAL_REFLECTION_PROMPT = """Detect epistemic total internal reflection:

Critical angle: {critical_angle}
Dense medium: {dense_medium}
Evanescent: {evanescent}
Fiber: {fiber}
Domain: {domain}
Context: {context}

Are ideas trapped inside a dense medium because they hit the boundary at too shallow an angle to escape? Return ONLY valid JSON."""


class EpistemicTotalInternalReflectionService:
    """Detects epistemic total internal reflection — ideas trapped at boundary."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        critical_angle: str,
        *,
        dense_medium: str = "",
        evanescent: str = "",
        fiber: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic total internal reflection."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TOTAL_INTERNAL_REFLECTION_PROMPT.format(
                critical_angle=critical_angle,
                dense_medium=dense_medium or "Not specified",
                evanescent=evanescent or "Not specified",
                fiber=fiber or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TOTAL_INTERNAL_REFLECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "critical_angle": critical_angle[:200],
            "total_internal_reflection_present": data.get("total_internal_reflection_present", False),
            "severity": data.get("severity", ""),
            "dense_medium": data.get("dense_medium", ""),
            "evanescent": data.get("evanescent", ""),
            "fiber": data.get("fiber", ""),
            "recommendation": data.get("recommendation", ""),
        }
