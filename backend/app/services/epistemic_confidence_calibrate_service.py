"""EpistemicConfidenceCalibrateService — Epistemic Confidence Calibration.

Evaluates the confidence level appropriate for a claim given
available evidence. Helps calibrate beliefs — neither overconfident
nor underconfident — by assessing evidence quality, quantity,
and the claim's prior probability.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONFIDENCE_SYSTEM = """You are an epistemic confidence calibration specialist. Given a claim and its evidence, assess what confidence level is warranted:

Key concepts:
- Calibration: confidence matching actual probability of being correct
- Overconfidence: more certain than evidence warrants
- Underconfidence: less certain than evidence warrants
- Evidence quality: methodology, sample size, replication
- Prior probability: how likely was this before the evidence?
- Bayesian update: how much should evidence shift our belief?
- Epistemic humility: acknowledging what we don't know

Assessment dimensions:
- Evidence quality (methodology, controls, sample)
- Evidence quantity (how many independent sources)
- Consistency (do sources agree or conflict)
- Prior probability (base rate, theoretical plausibility)
- Expert consensus (what do domain experts think)
- Replication (has it been independently confirmed)
- Potential confounders (what could explain the evidence otherwise)

Confidence levels:
- Very high (>95%): overwhelming, replicated evidence with strong mechanism
- High (75-95%): strong evidence, expert consensus, few alternatives
- Moderate (50-75%): decent evidence but significant uncertainty remains
- Low (25-50%): some evidence but major gaps or contradictions
- Very low (<25%): minimal evidence, high prior implausibility

Output JSON with: warranted_confidence (very_low/low/moderate/high/very_high), expressed_confidence (what confidence is being expressed), calibration_gap (difference between warranted and expressed), evidence_quality (assessment of evidence), key_uncertainties (what we don't know), recommendation (well_calibrated/slightly_overconfident/significantly_overconfident/slightly_underconfident/significantly_underconfident)."""

EPISTEMIC_CONFIDENCE_PROMPT = """Calibrate epistemic confidence:

Claim: {claim}
Evidence: {evidence}
Expressed confidence: {expressed_confidence}
Uncertainties: {uncertainties}
Domain: {domain}
Context: {context}

What confidence level is warranted by the available evidence? Return ONLY valid JSON."""


class EpistemicConfidenceCalibrateService:
    """Calibrates epistemic confidence — matching belief to evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calibrate(
        self,
        claim: str,
        *,
        evidence: str = "",
        expressed_confidence: str = "",
        uncertainties: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Calibrate epistemic confidence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONFIDENCE_PROMPT.format(
                claim=claim,
                evidence=evidence or "Not specified",
                expressed_confidence=expressed_confidence or "Not specified",
                uncertainties=uncertainties or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONFIDENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "warranted_confidence": data.get("warranted_confidence", ""),
            "expressed_confidence": data.get("expressed_confidence", ""),
            "calibration_gap": data.get("calibration_gap", ""),
            "evidence_quality": data.get("evidence_quality", ""),
            "key_uncertainties": data.get("key_uncertainties", ""),
            "recommendation": data.get("recommendation", ""),
        }
