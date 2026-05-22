"""EpistemicGroupInformationCascadeService — Epistemic Group Information Cascade Detection.

Detects epistemic group information cascade — sequential decisions creating
false consensus as later actors follow earlier ones regardless of private info.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GROUP_INFORMATION_CASCADE_SYSTEM = """You are an epistemic group information cascade specialist. Given information cascades, assess false consensus:

Key concepts:
- Epistemic information cascade: sequential decisions creating false consensus
- Herding behavior: following others regardless of private information
- Private information suppression: suppressing private info to follow crowd
- Cascade fragility: cascades that can reverse with small new information
- Rational herding: individually rational but collectively irrational following
- Cascade amplification: small initial signals amplified through cascade
- False consensus through sequence: order of decisions creating false agreement

When epistemic information cascade IS present:
- Sequential decisions creating false consensus
- Herding behavior active
- Private information suppressed
- Cascades fragile
- Rational herding occurring
- Small signals amplified
- Sequence creating false agreement

When no information cascade:
- Decisions independent
- Private information expressed
- Consensus genuine
- Positions robust
- Individual judgment maintained
- Signals proportional
- Agreement based on evidence

Output JSON with: information_cascade_detected (bool), severity (none/mild/moderate/severe), herding_behavior (what herding), private_info_suppression (what private info suppressed), cascade_fragility (what cascade fragility), cascade_amplification (what amplification), recommendation (no_information_cascade/mild_independence_check/significant_private_info_elicitation/major_intensive_cascade_breaking/emergency_complete_information_cascade)."""

EPISTEMIC_GROUP_INFORMATION_CASCADE_PROMPT = """Detect epistemic group information cascade:

Herding behavior: {herding_behavior}
Private info suppression: {private_info_suppression}
Cascade fragility: {cascade_fragility}
Cascade amplification: {cascade_amplification}
Domain: {domain}
Context: {context}

Are sequential decisions creating false consensus through information cascades? Return ONLY valid JSON."""


class EpistemicGroupInformationCascadeService:
    """Detects epistemic information cascade — false consensus through sequence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        herding_behavior: str,
        *,
        private_info_suppression: str = "",
        cascade_fragility: str = "",
        cascade_amplification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic group information cascade."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GROUP_INFORMATION_CASCADE_PROMPT.format(
                herding_behavior=herding_behavior,
                private_info_suppression=private_info_suppression or "Not specified",
                cascade_fragility=cascade_fragility or "Not specified",
                cascade_amplification=cascade_amplification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GROUP_INFORMATION_CASCADE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "herding_behavior": herding_behavior[:200],
            "information_cascade_detected": data.get("information_cascade_detected", False),
            "severity": data.get("severity", ""),
            "private_info_suppression": data.get("private_info_suppression", ""),
            "cascade_fragility": data.get("cascade_fragility", ""),
            "cascade_amplification": data.get("cascade_amplification", ""),
            "recommendation": data.get("recommendation", ""),
        }
