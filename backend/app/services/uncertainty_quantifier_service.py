"""UncertaintyQuantifierService — Uncertainty Type Classification & Quantification.

Takes a claim and explicitly quantifies what we don't know. Distinguishes
between aleatory uncertainty (inherent randomness), epistemic uncertainty
(reducible with more data), model uncertainty (wrong framework), and
unknown unknowns.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

UNCERTAINTY_SYSTEM = """You are an uncertainty quantification specialist. Given a claim, decompose the uncertainty into types:
- Aleatory (inherent randomness that can't be reduced with more data)
- Epistemic (uncertainty from lack of knowledge, reducible with more research)
- Model uncertainty (we might be using the wrong framework entirely)
- Measurement uncertainty (our instruments/methods introduce error)
- Unknown unknowns (things we don't know we don't know)

For each type, assess magnitude and reducibility.

Output JSON with: uncertainties (list of: type (aleatory/epistemic/model/measurement/unknown_unknown), description, magnitude (low/moderate/high/extreme), reducible (bool), how_to_reduce (if reducible), impact_on_conclusion (how this uncertainty affects what we can conclude)), dominant_uncertainty (which type dominates), overall_confidence_ceiling (0-1, maximum justified confidence given all uncertainties), what_would_help_most (single most impactful thing to reduce uncertainty), false_precision_risk (0-1, are we claiming more precision than warranted), honest_summary (what we can actually claim given the uncertainty)."""

UNCERTAINTY_PROMPT = """Quantify the uncertainty in this claim:

Claim: {claim}
Evidence basis: {evidence}
Domain: {domain}
Context: {context}

What don't we know? Return ONLY valid JSON."""


class UncertaintyQuantifierService:
    """Quantifies and classifies uncertainty in claims."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def quantify(
        self,
        claim: str,
        *,
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Quantify uncertainty in a claim."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=UNCERTAINTY_PROMPT.format(
                claim=claim,
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=UNCERTAINTY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        uncertainties = data.get("uncertainties", [])
        return {
            "claim": claim[:200],
            "uncertainties_count": len(uncertainties),
            "uncertainties": uncertainties,
            "dominant_uncertainty": data.get("dominant_uncertainty", ""),
            "confidence_ceiling": data.get("overall_confidence_ceiling", 0),
            "what_would_help_most": data.get("what_would_help_most", ""),
            "false_precision_risk": data.get("false_precision_risk", 0),
            "honest_summary": data.get("honest_summary", ""),
        }
