"""EpistemicFailureToThriveService — Epistemic Failure to Thrive Detection.

Detects epistemic failure to thrive — intellectual systems not growing or
developing despite adequate resources, declining without clear cause.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FAILURE_TO_THRIVE_SYSTEM = """You are an epistemic failure to thrive specialist. Given intellectual systems not growing despite resources, assess:

Key concepts:
- Epistemic failure to thrive: not growing despite adequate resources
- Weight loss: losing intellectual substance without explanation
- Anorexia: loss of intellectual appetite/motivation
- Social withdrawal: disengaging from intellectual community
- Functional decline: progressive loss of capability
- Depression: loss of intellectual vitality
- Neglect: inadequate intellectual care/stimulation

When epistemic failure to thrive IS present:
- Not growing despite adequate resources
- Losing substance without explanation
- Lost motivation for intellectual intake
- Disengaging from community
- Progressive capability loss
- Lost intellectual vitality
- Inadequate care or stimulation

When no failure to thrive:
- Growing appropriately
- Maintaining substance
- Motivated and engaged
- Active in community
- Stable or improving capability
- Vital and energetic
- Well-cared for

Output JSON with: failure_to_thrive (bool), severity (none/mild/moderate/severe), weight_trajectory (what substance trend), appetite_status (what motivation), social_engagement (what community participation), functional_trajectory (what capability trend), recommendation (no_failure_to_thrive/mild_monitoring/significant_intervention/major_comprehensive_assessment/emergency_rapid_decline)."""

EPISTEMIC_FAILURE_TO_THRIVE_PROMPT = """Detect epistemic failure to thrive:

Weight trajectory: {weight_trajectory}
Appetite status: {appetite_status}
Social engagement: {social_engagement}
Functional trajectory: {functional_trajectory}
Domain: {domain}
Context: {context}

Is the intellectual system failing to grow or develop despite adequate resources? Return ONLY valid JSON."""


class EpistemicFailureToThriveService:
    """Detects epistemic failure to thrive — not growing despite adequate resources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        weight_trajectory: str,
        *,
        appetite_status: str = "",
        social_engagement: str = "",
        functional_trajectory: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic failure to thrive."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FAILURE_TO_THRIVE_PROMPT.format(
                weight_trajectory=weight_trajectory,
                appetite_status=appetite_status or "Not specified",
                social_engagement=social_engagement or "Not specified",
                functional_trajectory=functional_trajectory or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FAILURE_TO_THRIVE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "weight_trajectory": weight_trajectory[:200],
            "failure_to_thrive": data.get("failure_to_thrive", False),
            "severity": data.get("severity", ""),
            "appetite_status": data.get("appetite_status", ""),
            "social_engagement": data.get("social_engagement", ""),
            "functional_trajectory": data.get("functional_trajectory", ""),
            "recommendation": data.get("recommendation", ""),
        }
