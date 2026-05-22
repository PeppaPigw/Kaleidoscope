"""EpistemicGroupPolarizationAmplificationService — Epistemic Group Polarization Detection.

Detects epistemic group polarization amplification — group discussion
amplifying initial positions beyond what evidence supports.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GROUP_POLARIZATION_AMPLIFICATION_SYSTEM = """You are an epistemic group polarization amplification specialist. Given group polarization, assess position amplification:

Key concepts:
- Epistemic group polarization amplification: group discussion amplifying initial positions
- Risky shift: groups becoming more risk-seeking than individuals
- Cautious shift: groups becoming more cautious than individuals
- Argument pool bias: shared arguments reinforcing dominant position
- Social comparison: members competing to be more extreme
- Confidence amplification: group discussion inflating confidence
- Dissent suppression: polarization suppressing moderate voices

When epistemic group polarization amplification IS present:
- Initial positions amplified by discussion
- Risky or cautious shift occurring
- Argument pools biased
- Social comparison driving extremity
- Confidence inflated by group
- Dissent suppressed
- Positions beyond evidence

When no group polarization:
- Discussion moderating positions
- Risk assessment balanced
- Argument pools diverse
- Social comparison absent
- Confidence calibrated
- Dissent welcomed
- Positions evidence-based

Output JSON with: group_polarization_detected (bool), severity (none/mild/moderate/severe), position_amplification (what positions amplified), argument_pool_bias (what argument pools biased), confidence_amplification (what confidence amplified), dissent_suppression (what dissent suppressed), recommendation (no_group_polarization/mild_moderation_check/significant_dissent_inclusion/major_intensive_depolarization/emergency_complete_group_polarization)."""

EPISTEMIC_GROUP_POLARIZATION_AMPLIFICATION_PROMPT = """Detect epistemic group polarization amplification:

Position amplification: {position_amplification}
Argument pool bias: {argument_pool_bias}
Confidence amplification: {confidence_amplification}
Dissent suppression: {dissent_suppression}
Domain: {domain}
Context: {context}

Is group discussion amplifying initial positions beyond evidence? Return ONLY valid JSON."""


class EpistemicGroupPolarizationAmplificationService:
    """Detects epistemic group polarization — position amplification."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        position_amplification: str,
        *,
        argument_pool_bias: str = "",
        confidence_amplification: str = "",
        dissent_suppression: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic group polarization amplification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GROUP_POLARIZATION_AMPLIFICATION_PROMPT.format(
                position_amplification=position_amplification,
                argument_pool_bias=argument_pool_bias or "Not specified",
                confidence_amplification=confidence_amplification or "Not specified",
                dissent_suppression=dissent_suppression or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GROUP_POLARIZATION_AMPLIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "position_amplification": position_amplification[:200],
            "group_polarization_detected": data.get("group_polarization_detected", False),
            "severity": data.get("severity", ""),
            "argument_pool_bias": data.get("argument_pool_bias", ""),
            "confidence_amplification": data.get("confidence_amplification", ""),
            "dissent_suppression": data.get("dissent_suppression", ""),
            "recommendation": data.get("recommendation", ""),
        }
