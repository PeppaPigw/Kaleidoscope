"""EpistemicHorizonService — Epistemic Horizon Limitation Detection.

Detects epistemic horizon violations — claiming knowledge beyond
what is knowable from a given vantage point, ignoring the inherent
limits of observation, measurement, or cognitive access.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HORIZON_SYSTEM = """You are an epistemic horizon specialist. Given a claim, assess whether it exceeds what is knowable from the claimant's vantage point:

Key concepts:
- Epistemic horizon: the boundary of what can be known from a position
- Observational limits: what cannot be seen from here
- Measurement boundaries: what instruments cannot reach
- Cognitive access limits: what minds cannot directly access
- Positional blindness: what position prevents seeing
- Horizon confusion: treating horizon as edge of reality
- Beyond-horizon claims: asserting knowledge past knowable limits

When epistemic horizon violation IS present:
- Claims exceed what is knowable from the vantage point
- Observational limits ignored or denied
- Measurement boundaries treated as non-existent
- Cognitive access assumed where none exists
- Position-dependent limits not acknowledged
- Horizon treated as edge of reality rather than edge of view
- Beyond-horizon assertions made without justification

When claims are within epistemic horizon:
- Claims bounded by acknowledged limits
- Observational constraints stated
- Measurement boundaries respected
- Cognitive access limits recognized
- Position-dependent knowledge acknowledged
- Horizon recognized as limit of view not reality
- Beyond-horizon speculation clearly marked as such

Output JSON with: violation_present (bool), severity (none/mild/moderate/severe), claim (what is claimed), horizon (what the epistemic horizon is), beyond (what lies beyond the horizon), vantage (what vantage point is assumed), recommendation (within_epistemic_horizon/mild_horizon_stretch/significant_horizon_violation/major_beyond_horizon_claim/respect_epistemic_boundaries)."""

EPISTEMIC_HORIZON_PROMPT = """Detect epistemic horizon violation:

Claim: {claim}
Vantage point: {vantage}
Known limits: {limits}
Justification: {justification}
Domain: {domain}
Context: {context}

Does this claim exceed what is knowable from the given vantage point? Return ONLY valid JSON."""


class EpistemicHorizonService:
    """Detects epistemic horizon violations — claims beyond knowable limits."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        vantage: str = "",
        limits: str = "",
        justification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic horizon violation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HORIZON_PROMPT.format(
                claim=claim,
                vantage=vantage or "Not specified",
                limits=limits or "Not specified",
                justification=justification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HORIZON_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "violation_present": data.get("violation_present", False),
            "severity": data.get("severity", ""),
            "horizon": data.get("horizon", ""),
            "beyond": data.get("beyond", ""),
            "vantage": data.get("vantage", ""),
            "recommendation": data.get("recommendation", ""),
        }
