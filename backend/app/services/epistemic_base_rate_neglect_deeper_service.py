"""EpistemicBaseRateNeglectDeeperService — Epistemic Base Rate Neglect Detection (Deeper).

Detects epistemic base rate neglect — neglecting base rates in probability
estimation, overweighting specific evidence relative to prior probabilities.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BASE_RATE_NEGLECT_DEEPER_SYSTEM = """You are an epistemic base rate neglect specialist. Given neglected base rates in probability estimation, assess base rate neglect:

Key concepts:
- Epistemic base rate neglect: ignoring prior probabilities when updating beliefs
- Representativeness over base rate: judging by similarity not frequency
- Vivid evidence overweighting: overweighting vivid specific evidence over statistics
- Prior probability ignorance: ignoring how common something is
- Diagnostic evidence overvaluation: overvaluing diagnostic evidence relative to base rate
- Population frequency blindness: blind to population-level frequencies
- Reference class neglect: failing to identify appropriate reference class

When epistemic base rate neglect IS present:
- Base rates ignored
- Representativeness dominates
- Vivid evidence overweighted
- Prior probabilities ignored
- Diagnostic evidence overvalued
- Population frequencies missed
- Reference class neglected

When no base rate neglect:
- Base rates incorporated
- Representativeness balanced with frequency
- Vivid evidence weighted appropriately
- Prior probabilities considered
- Diagnostic evidence calibrated
- Population frequencies used
- Reference class identified

Output JSON with: base_rate_neglect_detected (bool), severity (none/mild/moderate/severe), representativeness_dominance (what representativeness dominating), vivid_overweighting (what vivid evidence overweighted), prior_ignorance (what priors ignored), reference_class_neglect (what reference class missed), recommendation (no_base_rate_neglect/mild_prior_awareness/significant_bayesian_updating/major_intensive_base_rate_integration/emergency_complete_base_rate_neglect)."""

EPISTEMIC_BASE_RATE_NEGLECT_DEEPER_PROMPT = """Detect epistemic base rate neglect:

Representativeness dominance: {representativeness_dominance}
Vivid overweighting: {vivid_overweighting}
Prior ignorance: {prior_ignorance}
Reference class neglect: {reference_class_neglect}
Domain: {domain}
Context: {context}

Are base rates being neglected in probability estimation? Return ONLY valid JSON."""


class EpistemicBaseRateNeglectDeeperService:
    """Detects epistemic base rate neglect — priors ignored."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        representativeness_dominance: str,
        *,
        vivid_overweighting: str = "",
        prior_ignorance: str = "",
        reference_class_neglect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic base rate neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BASE_RATE_NEGLECT_DEEPER_PROMPT.format(
                representativeness_dominance=representativeness_dominance,
                vivid_overweighting=vivid_overweighting or "Not specified",
                prior_ignorance=prior_ignorance or "Not specified",
                reference_class_neglect=reference_class_neglect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BASE_RATE_NEGLECT_DEEPER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "representativeness_dominance": representativeness_dominance[:200],
            "base_rate_neglect_detected": data.get("base_rate_neglect_detected", False),
            "severity": data.get("severity", ""),
            "vivid_overweighting": data.get("vivid_overweighting", ""),
            "prior_ignorance": data.get("prior_ignorance", ""),
            "reference_class_neglect": data.get("reference_class_neglect", ""),
            "recommendation": data.get("recommendation", ""),
        }
