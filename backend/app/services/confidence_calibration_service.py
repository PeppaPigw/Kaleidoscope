"""ConfidenceCalibrationService — Expertise-Confidence Mismatch Detection.

Assesses whether confidence in a claim is calibrated to actual
expertise and evidence quality. Detects overconfidence (Dunning-Kruger),
underconfidence, and false certainty from insufficient evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CALIBRATION_SYSTEM = """You are a confidence calibration specialist. Given a claim and its stated confidence, assess whether the confidence is warranted:
- Is the confidence level appropriate for the evidence quality?
- Is there an expertise-confidence mismatch (high confidence + low expertise)?
- Are there signs of overconfidence (certainty without acknowledging unknowns)?
- Are there signs of underconfidence (excessive hedging despite strong evidence)?
- What confidence level would be well-calibrated?

Output JSON with: confidence_stated (0-1, the expressed confidence), confidence_warranted (0-1, what the evidence supports), calibration_gap (difference between stated and warranted), miscalibration_type (overconfident/underconfident/well_calibrated), expertise_signals (list of indicators of expertise level), evidence_quality_signals (list of indicators of evidence quality), overconfidence_markers (list of: marker, why_concerning), underconfidence_markers (list of: marker, why_concerning), dunning_kruger_risk (0-1, risk of unknown unknowns), unknown_unknowns (things the claimant likely doesn't know they don't know), appropriate_hedging (what caveats should be present), recommendation (confidence_appropriate/reduce_confidence/increase_confidence/seek_more_evidence), calibrated_statement (how to express this with appropriate confidence)."""

CALIBRATION_PROMPT = """Assess confidence calibration:

Claim: {claim}
Stated confidence: {confidence_level}
Expertise basis: {expertise}
Evidence cited: {evidence}
Domain: {domain}

Is the confidence calibrated? Return ONLY valid JSON."""


class ConfidenceCalibrationService:
    """Assesses confidence calibration and expertise-confidence mismatch."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        claim: str,
        *,
        confidence_level: str = "",
        expertise: str = "",
        evidence: str = "",
        domain: str = "",
    ) -> dict:
        """Assess confidence calibration."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CALIBRATION_PROMPT.format(
                claim=claim,
                confidence_level=confidence_level or "High (implied by tone)",
                expertise=expertise or "Not specified",
                evidence=evidence or "Not cited",
                domain=domain or "general",
            ),
            system=CALIBRATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "confidence_stated": data.get("confidence_stated", 0),
            "confidence_warranted": data.get("confidence_warranted", 0),
            "calibration_gap": data.get("calibration_gap", 0),
            "miscalibration_type": data.get("miscalibration_type", ""),
            "expertise_signals": data.get("expertise_signals", []),
            "evidence_quality_signals": data.get("evidence_quality_signals", []),
            "overconfidence_markers": data.get("overconfidence_markers", []),
            "underconfidence_markers": data.get("underconfidence_markers", []),
            "dunning_kruger_risk": data.get("dunning_kruger_risk", 0),
            "unknown_unknowns": data.get("unknown_unknowns", []),
            "appropriate_hedging": data.get("appropriate_hedging", ""),
            "recommendation": data.get("recommendation", ""),
            "calibrated_statement": data.get("calibrated_statement", ""),
        }
