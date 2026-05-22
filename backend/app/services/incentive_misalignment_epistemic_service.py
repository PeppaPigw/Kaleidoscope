"""IncentiveMisalignmentEpistemicService — Epistemic Incentive Misalignment Detection.

Detects epistemic incentive misalignment — incentive structures that
reward epistemic bad behavior such as overconfidence, suppressing
uncertainty, or producing quantity over quality of knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INCENTIVE_MISALIGNMENT_EPISTEMIC_SYSTEM = """You are an epistemic incentive misalignment specialist. Given an incentive structure, assess whether it rewards epistemic bad behavior:

Key concepts:
- Incentive misalignment: rewards for epistemic bad behavior
- Overconfidence reward: certainty rewarded over accuracy
- Uncertainty suppression: incentives to hide uncertainty
- Quantity over quality: volume rewarded over rigor
- Speed over accuracy: fast answers rewarded over correct ones
- Novelty bias: new claims rewarded over verification
- Confirmation reward: confirming expectations rewarded over truth

When incentive misalignment IS present:
- Overconfidence rewarded over calibrated uncertainty
- Hiding uncertainty incentivized
- Quantity of claims rewarded over quality
- Speed prioritized over accuracy
- Novel claims rewarded more than verification
- Confirming expectations rewarded over challenging them
- Epistemic virtues punished by incentive structure

When incentives are aligned:
- Accuracy rewarded over confidence
- Appropriate uncertainty acknowledged and valued
- Quality prioritized over quantity
- Accuracy valued alongside timeliness
- Verification valued alongside discovery
- Truth-seeking rewarded regardless of outcome
- Epistemic virtues supported by incentive structure

Output JSON with: misalignment_present (bool), severity (none/mild/moderate/severe), structure (what incentive structure exists), bad_behavior_rewarded (what bad behavior is incentivized), good_behavior_punished (what good behavior is discouraged), consequence (what epistemic consequence results), recommendation (aligned_incentives/mild_misalignment/significant_incentive_misalignment/major_epistemic_perversion/realign_incentives_with_truth)."""

INCENTIVE_MISALIGNMENT_EPISTEMIC_PROMPT = """Detect epistemic incentive misalignment:

Incentive structure: {structure}
Behaviors rewarded: {rewarded}
Behaviors punished: {punished}
Epistemic consequence: {consequence}
Domain: {domain}
Context: {context}

Does this incentive structure reward epistemic bad behavior? Return ONLY valid JSON."""


class IncentiveMisalignmentEpistemicService:
    """Detects epistemic incentive misalignment — incentives rewarding bad epistemic behavior."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        structure: str,
        *,
        rewarded: str = "",
        punished: str = "",
        consequence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic incentive misalignment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INCENTIVE_MISALIGNMENT_EPISTEMIC_PROMPT.format(
                structure=structure,
                rewarded=rewarded or "Not specified",
                punished=punished or "Not specified",
                consequence=consequence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INCENTIVE_MISALIGNMENT_EPISTEMIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "structure": structure[:200],
            "misalignment_present": data.get("misalignment_present", False),
            "severity": data.get("severity", ""),
            "bad_behavior_rewarded": data.get("bad_behavior_rewarded", ""),
            "good_behavior_punished": data.get("good_behavior_punished", ""),
            "consequence": data.get("consequence", ""),
            "recommendation": data.get("recommendation", ""),
        }
