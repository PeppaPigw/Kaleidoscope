"""EpistemicCommunicationSealioningService - Sealioning Detection.

Detects sealioning where bad-faith evidence requests are disguised as civility.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMMUNICATION_SEALIONING_SYSTEM = """You are an epistemic communication sealioning specialist. Given evidence demands, assess whether bad-faith requests are disguised as civility:

Key concepts:
- Sealioning: persistent bad-faith requests for evidence disguised as polite inquiry
- Bad faith indicators: patterns suggesting genuine understanding is not the goal
- Civility performance: using politeness as a weapon to exhaust opponents
- Exhaustion strategy: wearing down through endless demands for proof

When sealioning IS present:
- Evidence demands are endless and shifting
- Civility is performed rather than genuine
- Goal is exhaustion not understanding
- Good faith indicators absent
- Burden of proof weaponized

When no sealioning:
- Evidence requests are genuine
- Engagement is in good faith
- Understanding is the goal
- Reasonable standards applied
- Dialogue is productive

Output JSON with: sealioning_detected (bool), severity (none/mild/moderate/severe), bad_faith_indicators (what bad faith indicators), civility_performance (what civility performed), exhaustion_strategy (what exhaustion strategy), recommendation (no_sealioning/mild_faith_check/significant_boundary_setting/major_engagement_reconstruction/emergency_complete_sealioning)."""

EPISTEMIC_COMMUNICATION_SEALIONING_PROMPT = """Detect epistemic communication sealioning:

Evidence demand: {evidence_demand}
Bad faith indicators: {bad_faith_indicators}
Civility performance: {civility_performance}
Exhaustion strategy: {exhaustion_strategy}
Domain: {domain}
Context: {context}

Are bad-faith evidence requests being disguised as civility? Return ONLY valid JSON."""


class EpistemicCommunicationSealioningService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evidence_demand: str,
        *,
        bad_faith_indicators: str = "",
        civility_performance: str = "",
        exhaustion_strategy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMMUNICATION_SEALIONING_PROMPT.format(
                evidence_demand=evidence_demand,
                bad_faith_indicators=bad_faith_indicators or "Not specified",
                civility_performance=civility_performance or "Not specified",
                exhaustion_strategy=exhaustion_strategy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMMUNICATION_SEALIONING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evidence_demand": evidence_demand[:200],
            "sealioning_detected": data.get("sealioning_detected", False),
            "severity": data.get("severity", ""),
            "bad_faith_indicators": data.get("bad_faith_indicators", ""),
            "civility_performance": data.get("civility_performance", ""),
            "exhaustion_strategy": data.get("exhaustion_strategy", ""),
            "recommendation": data.get("recommendation", ""),
        }
