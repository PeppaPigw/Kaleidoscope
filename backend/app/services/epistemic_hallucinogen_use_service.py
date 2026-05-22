"""EpistemicHallucinogenUseService — Epistemic Hallucinogen Use Detection.

Detects epistemic hallucinogen use — seeking reality distortion to escape
conventional intellectual frameworks and perceive alternative realities.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HALLUCINOGEN_SYSTEM = """You are an epistemic hallucinogen use specialist. Given reality distortion seeking, assess hallucinogen use:

Key concepts:
- Epistemic hallucinogen use: seeking reality distortion
- Altered states: pursuing non-ordinary intellectual perception
- Ego dissolution: losing intellectual identity boundaries
- Synesthesia: cross-modal intellectual experience
- Flashbacks: involuntary return to altered states
- Integration failure: unable to reconcile altered with normal
- Set and setting: context determining experience quality

When epistemic hallucinogen use IS present:
- Seeking reality distortion
- Pursuing non-ordinary perception
- Losing identity boundaries
- Cross-modal experience
- Involuntary altered returns
- Cannot reconcile states
- Context-dependent experiences

When no hallucinogen use:
- Accepting consensus reality
- Ordinary perception
- Clear identity boundaries
- Normal modal experience
- Stable perception
- Integrated worldview
- Context-independent stability

Output JSON with: hallucinogen_use_detected (bool), severity (none/mild/moderate/severe), distortion_seeking (what altered states), ego_dissolution (what boundary loss), integration_status (what reconciliation), flashback_risk (what involuntary returns), recommendation (no_hallucinogen_use/mild_grounding_practices/significant_integration_therapy/major_intensive_reality_testing/emergency_persistent_psychosis)."""

EPISTEMIC_HALLUCINOGEN_PROMPT = """Detect epistemic hallucinogen use:

Distortion seeking: {distortion_seeking}
Ego dissolution: {ego_dissolution}
Integration status: {integration_status}
Flashback risk: {flashback_risk}
Domain: {domain}
Context: {context}

Is there seeking of reality distortion to escape conventional intellectual frameworks? Return ONLY valid JSON."""


class EpistemicHallucinogenUseService:
    """Detects epistemic hallucinogen use — reality distortion seeking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        distortion_seeking: str,
        *,
        ego_dissolution: str = "",
        integration_status: str = "",
        flashback_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hallucinogen use."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HALLUCINOGEN_PROMPT.format(
                distortion_seeking=distortion_seeking,
                ego_dissolution=ego_dissolution or "Not specified",
                integration_status=integration_status or "Not specified",
                flashback_risk=flashback_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HALLUCINOGEN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "distortion_seeking": distortion_seeking[:200],
            "hallucinogen_use_detected": data.get("hallucinogen_use_detected", False),
            "severity": data.get("severity", ""),
            "ego_dissolution": data.get("ego_dissolution", ""),
            "integration_status": data.get("integration_status", ""),
            "flashback_risk": data.get("flashback_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
