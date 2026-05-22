"""EpistemicMirrorHallService — Epistemic Mirror Hall Detection.

Detects epistemic mirror halls — environments where ideas reflect
endlessly creating illusion of depth and multiplicity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MIRROR_HALL_SYSTEM = """You are an epistemic mirror hall specialist. Given a discourse environment, assess whether ideas are reflecting endlessly creating false depth:

Key concepts:
- Epistemic mirror hall: ideas reflecting endlessly
- False multiplicity: one idea appearing as many through reflection
- Depth illusion: reflections creating illusion of depth
- Echo amplification: ideas amplified through reflection
- Self-reference loop: ideas referencing their own reflections
- Infinite regress appearance: appearance of infinite depth
- Disorientation through reflection: reflection causing disorientation

When epistemic mirror hall IS present:
- Ideas reflecting endlessly creating false depth
- One idea appearing as many through reflection
- Reflections creating illusion of depth
- Ideas amplified through endless reflection
- Ideas referencing their own reflections
- Appearance of infinite depth from finite content
- Reflection causing disorientation

When genuine depth is present:
- Multiple genuinely distinct ideas
- Depth from substance not reflection
- Multiplicity from genuine diversity
- Ideas distinct not reflected copies
- Self-reference productive not circular
- Actual depth not illusory
- Orientation maintained through genuine structure

Output JSON with: mirror_hall_present (bool), severity (none/mild/moderate/severe), environment (what environment exists), reflection (what reflects), false_depth (what false depth is created), disorientation (how disorientation occurs), recommendation (genuine_depth/mild_reflection/significant_mirror_hall/major_false_multiplicity/find_original_idea)."""

EPISTEMIC_MIRROR_HALL_PROMPT = """Detect epistemic mirror hall:

Environment: {environment}
Reflection: {reflection}
False depth: {false_depth}
Disorientation: {disorientation}
Domain: {domain}
Context: {context}

Are ideas reflecting endlessly creating illusion of depth and multiplicity? Return ONLY valid JSON."""


class EpistemicMirrorHallService:
    """Detects epistemic mirror halls — ideas reflecting endlessly."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        environment: str,
        *,
        reflection: str = "",
        false_depth: str = "",
        disorientation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic mirror hall."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MIRROR_HALL_PROMPT.format(
                environment=environment,
                reflection=reflection or "Not specified",
                false_depth=false_depth or "Not specified",
                disorientation=disorientation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MIRROR_HALL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "environment": environment[:200],
            "mirror_hall_present": data.get("mirror_hall_present", False),
            "severity": data.get("severity", ""),
            "reflection": data.get("reflection", ""),
            "false_depth": data.get("false_depth", ""),
            "disorientation": data.get("disorientation", ""),
            "recommendation": data.get("recommendation", ""),
        }
