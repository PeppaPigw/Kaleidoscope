"""ConfidenceCompetenceGapService — Confidence-Competence Gap Detection.

Detects confidence-competence gap — systematic mismatch between
confidence in one's abilities and actual competence, either
overconfidence or underconfidence relative to demonstrated ability.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONFIDENCE_COMPETENCE_GAP_SYSTEM = """You are a confidence-competence gap specialist. Given a performance claim, assess whether confidence matches actual competence:

Key concepts:
- Confidence-competence gap: mismatch between confidence and ability
- Dunning-Kruger pattern: low competence with high confidence
- Impostor pattern: high competence with low confidence
- Calibration: alignment of confidence with accuracy
- Overconfidence: confidence exceeding competence
- Underconfidence: competence exceeding confidence
- Domain-specific calibration: calibration varies by domain

When confidence-competence gap IS present:
- Confidence level mismatched with demonstrated ability
- High confidence without supporting track record
- Low confidence despite strong performance
- Confidence not updated based on feedback
- Domain expertise not reflected in confidence level
- Systematic over- or under-estimation of ability
- Confidence driven by personality, not performance

When confidence is well-calibrated:
- Confidence matches demonstrated track record
- Confidence updated based on outcomes
- Uncertainty acknowledged where appropriate
- Domain-specific confidence reflects domain-specific ability
- Confidence varies appropriately across domains
- Feedback incorporated into self-assessment
- Calibration actively maintained

Output JSON with: gap_present (bool), severity (none/mild/moderate/severe), claim (what is claimed), confidence_level (expressed confidence), competence_evidence (evidence of actual competence), direction (overconfident/underconfident), recommendation (appropriate_calibration/mild_miscalibration/significant_confidence_gap/major_competence_mismatch/calibrate_to_evidence)."""

CONFIDENCE_COMPETENCE_GAP_PROMPT = """Detect confidence-competence gap:

Claim: {claim}
Confidence expressed: {confidence}
Evidence of competence: {competence}
Track record: {track_record}
Domain: {domain}
Context: {context}

Is there a systematic mismatch between confidence and actual competence? Return ONLY valid JSON."""


class ConfidenceCompetenceGapService:
    """Detects confidence-competence gap — mismatch between confidence and ability."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        confidence: str = "",
        competence: str = "",
        track_record: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect confidence-competence gap."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONFIDENCE_COMPETENCE_GAP_PROMPT.format(
                claim=claim,
                confidence=confidence or "Not specified",
                competence=competence or "Not specified",
                track_record=track_record or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONFIDENCE_COMPETENCE_GAP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "gap_present": data.get("gap_present", False),
            "severity": data.get("severity", ""),
            "confidence_level": data.get("confidence_level", ""),
            "competence_evidence": data.get("competence_evidence", ""),
            "direction": data.get("direction", ""),
            "recommendation": data.get("recommendation", ""),
        }
