"""EpistemicCertaintyGriefService — Epistemic Certainty Grief Detection.

Detects epistemic certainty grief — grieving the loss of intellectual
certainty and the comfort it provided.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CERTAINTY_GRIEF_SYSTEM = """You are an epistemic certainty grief specialist. Given grieving lost certainty, assess certainty grief:

Key concepts:
- Epistemic certainty grief: grieving loss of intellectual certainty
- Comfort loss: missing the comfort of knowing
- Ambiguity distress: pain of living without clear answers
- Foundation crumbling: ground giving way beneath understanding
- Anchor loss: losing intellectual anchoring points
- Vertigo of uncertainty: dizziness from groundlessness
- Security mourning: mourning the security certainty provided

When epistemic certainty grief IS present:
- Grieving loss of certainty
- Missing comfort of knowing
- Pain of ambiguity
- Foundation crumbling
- Losing anchoring points
- Dizziness from groundlessness
- Mourning security

When no certainty grief:
- Comfortable with uncertainty
- Finding comfort in exploration
- Embracing ambiguity
- Foundation flexible
- Multiple anchors
- Grounded in process
- Security from adaptability

Output JSON with: certainty_grief_detected (bool), severity (none/mild/moderate/severe), comfort_loss (what missing), ambiguity_distress (what painful about), foundation_crumbling (what giving way), anchor_loss (what losing), recommendation (no_certainty_grief/mild_uncertainty_tolerance/significant_groundedness_building/major_intensive_grief_processing/emergency_severe_groundlessness)."""

EPISTEMIC_CERTAINTY_GRIEF_PROMPT = """Detect epistemic certainty grief:

Comfort loss: {comfort_loss}
Ambiguity distress: {ambiguity_distress}
Foundation crumbling: {foundation_crumbling}
Anchor loss: {anchor_loss}
Domain: {domain}
Context: {context}

Is there grieving the loss of intellectual certainty? Return ONLY valid JSON."""


class EpistemicCertaintyGriefService:
    """Detects epistemic certainty grief — grieving loss of intellectual certainty."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        comfort_loss: str,
        *,
        ambiguity_distress: str = "",
        foundation_crumbling: str = "",
        anchor_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic certainty grief."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CERTAINTY_GRIEF_PROMPT.format(
                comfort_loss=comfort_loss,
                ambiguity_distress=ambiguity_distress or "Not specified",
                foundation_crumbling=foundation_crumbling or "Not specified",
                anchor_loss=anchor_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CERTAINTY_GRIEF_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "comfort_loss": comfort_loss[:200],
            "certainty_grief_detected": data.get("certainty_grief_detected", False),
            "severity": data.get("severity", ""),
            "ambiguity_distress": data.get("ambiguity_distress", ""),
            "foundation_crumbling": data.get("foundation_crumbling", ""),
            "anchor_loss": data.get("anchor_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }
