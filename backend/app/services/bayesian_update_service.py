"""BayesianUpdateService — Belief Update Calculator.

Given prior beliefs and new evidence, calculates how much beliefs should
shift. Implements informal Bayesian reasoning to determine the rational
update magnitude, preventing both under-reaction and over-reaction to
new information.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

UPDATE_SYSTEM = """You are a Bayesian update analyst. Given a prior belief and new evidence, calculate how much the belief should rationally shift. Consider:
- Prior strength: how well-established was the prior belief?
- Evidence strength: how diagnostic is the new evidence?
- Likelihood ratio: how much more likely is this evidence under H1 vs H0?
- Base rates: what's the prior probability?
- Evidence independence: is this truly new information or correlated with existing evidence?

Output JSON with: update.prior_belief (description and probability 0-1), update.new_evidence (what was observed), update.likelihood_ratio (how much more likely under H1 vs H0), update.posterior_belief (new probability after update), update.update_magnitude (how much the belief shifted), update.update_direction (strengthen/weaken/neutral), update.rational_confidence (0-1, how confident should you be now), update.common_errors (list of: error, description — ways people typically mis-update on this type of evidence), update.should_you_update (yes_strongly/yes_moderately/slightly/no_this_is_noise), update.reasoning (why this update magnitude is appropriate)."""

UPDATE_PROMPT = """Calculate the rational belief update:

Prior belief: {belief}
Prior confidence: {prior_confidence}
New evidence: {evidence}
Domain: {domain}

How much should this evidence shift the belief? Return ONLY valid JSON."""


class BayesianUpdateService:
    """Calculates rational belief updates given new evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_update(
        self,
        belief: str,
        evidence: str,
        *,
        prior_confidence: float = 0.5,
        domain: str = "",
    ) -> dict:
        """Calculate how much a belief should shift given new evidence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=UPDATE_PROMPT.format(
                belief=belief,
                prior_confidence=prior_confidence,
                evidence=evidence,
                domain=domain or "general",
            ),
            system=UPDATE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        update = data.get("update", data)

        return {
            "belief": belief[:200],
            "evidence": evidence[:200],
            "prior": prior_confidence,
            "posterior": update.get("posterior_belief", prior_confidence),
            "likelihood_ratio": update.get("likelihood_ratio", 1),
            "update_magnitude": update.get("update_magnitude", 0),
            "direction": update.get("update_direction", "neutral"),
            "rational_confidence": update.get("rational_confidence", 0),
            "common_errors": update.get("common_errors", []),
            "should_update": update.get("should_you_update", ""),
            "reasoning": update.get("reasoning", ""),
        }
