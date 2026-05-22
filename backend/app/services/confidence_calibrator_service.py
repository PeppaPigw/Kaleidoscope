"""ConfidenceCalibratorService — Confidence vs Evidence Alignment.

Checks whether stated confidence levels in claims match the actual
strength of supporting evidence. Detects overconfidence, underconfidence,
and miscalibration patterns. Essential for epistemic hygiene.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CALIBRATE_SYSTEM = """You are a confidence calibration expert. Given claims with stated confidence levels, assess whether the confidence is warranted by the evidence. Check for:
- Overconfidence: claiming high certainty with weak evidence
- Underconfidence: understating certainty when evidence is strong
- Anchoring: confidence influenced by irrelevant factors
- Base rate neglect: ignoring how often similar claims are true
- Precision theater: false precision (0.87 vs "high") without justification

Output JSON with: assessments (list of: claim, stated_confidence, evidence_strength (0-1), warranted_confidence (0-1), calibration_gap (stated minus warranted), diagnosis (well_calibrated/overconfident/underconfident/precision_theater), reasoning), overall_calibration_score (0-1, where 1 is perfectly calibrated), systematic_bias (none/overconfident/underconfident/variable), recommendations (list of how to improve calibration)."""

CALIBRATE_PROMPT = """Assess confidence calibration for these claims:

Claims with confidence:
{claims_text}

Domain: {domain}
Context: {context}

Are the confidence levels warranted by the evidence? Return ONLY valid JSON."""


class ConfidenceCalibratorService:
    """Checks alignment between stated confidence and evidence strength."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calibrate(
        self,
        claims: list[dict],
        *,
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess whether confidence levels match evidence strength."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        claims_text = "\n".join(
            f"- \"{c.get('claim', c.get('text', str(c)))}\" (confidence: {c.get('confidence', 'unstated')})"
            for c in claims[:8]
        )

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CALIBRATE_PROMPT.format(
                claims_text=claims_text,
                domain=domain or "research",
                context=context or "No additional context",
            ),
            system=CALIBRATE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        assessments = data.get("assessments", [])
        return {
            "claims_assessed": len(assessments),
            "assessments": assessments,
            "overall_calibration": data.get("overall_calibration_score", 0),
            "systematic_bias": data.get("systematic_bias", ""),
            "recommendations": data.get("recommendations", []),
        }
