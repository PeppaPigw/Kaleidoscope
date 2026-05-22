"""EpistemicSocialConformityService — Epistemic Social Conformity Detection.

Detects epistemic social conformity — conforming to group beliefs
against better judgment due to social pressure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SOCIAL_CONFORMITY_SYSTEM = """You are an epistemic social conformity specialist. Given conforming to group beliefs against better judgment, assess social conformity:

Key concepts:
- Epistemic social conformity: conforming to group beliefs against better judgment
- Belief alignment pressure: pressure to align beliefs with group
- Dissent suppression: suppressing disagreement for social harmony
- Majority influence: majority opinion overriding personal judgment
- Normative pressure: norms pressuring belief adoption
- Compliance without conviction: agreeing without believing
- Asch effect: changing judgment to match group consensus

When epistemic social conformity IS present:
- Conforming against better judgment
- Pressure to align beliefs
- Dissent suppressed
- Majority overriding judgment
- Norms pressuring beliefs
- Complying without conviction
- Changing judgment to match group

When no social conformity:
- Beliefs held independently
- No pressure to align
- Dissent expressed freely
- Majority considered not followed blindly
- Norms not pressuring beliefs
- Conviction matches expression
- Judgment independent of group

Output JSON with: social_conformity_detected (bool), severity (none/mild/moderate/severe), belief_alignment_pressure (what beliefs pressured to align), dissent_suppression (what dissent suppressed), majority_influence (what majority overriding), compliance_without_conviction (what complying without believing), recommendation (no_social_conformity/mild_independence_practice/significant_dissent_recovery/major_intensive_autonomy_building/emergency_complete_social_conformity)."""

EPISTEMIC_SOCIAL_CONFORMITY_PROMPT = """Detect epistemic social conformity:

Belief alignment pressure: {belief_alignment_pressure}
Dissent suppression: {dissent_suppression}
Majority influence: {majority_influence}
Compliance without conviction: {compliance_without_conviction}
Domain: {domain}
Context: {context}

Is there conforming to group beliefs against better judgment? Return ONLY valid JSON."""


class EpistemicSocialConformityService:
    """Detects epistemic social conformity — conforming against better judgment."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief_alignment_pressure: str,
        *,
        dissent_suppression: str = "",
        majority_influence: str = "",
        compliance_without_conviction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic social conformity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SOCIAL_CONFORMITY_PROMPT.format(
                belief_alignment_pressure=belief_alignment_pressure,
                dissent_suppression=dissent_suppression or "Not specified",
                majority_influence=majority_influence or "Not specified",
                compliance_without_conviction=compliance_without_conviction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SOCIAL_CONFORMITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief_alignment_pressure": belief_alignment_pressure[:200],
            "social_conformity_detected": data.get("social_conformity_detected", False),
            "severity": data.get("severity", ""),
            "dissent_suppression": data.get("dissent_suppression", ""),
            "majority_influence": data.get("majority_influence", ""),
            "compliance_without_conviction": data.get("compliance_without_conviction", ""),
            "recommendation": data.get("recommendation", ""),
        }
