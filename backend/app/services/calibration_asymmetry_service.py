"""CalibrationAsymmetryService — Calibration Asymmetry Detection.

Detects calibration asymmetry — when confidence is well-calibrated
in some domains or for some types of judgments but poorly
calibrated in others, without awareness of this inconsistency.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CALIBRATION_ASYMMETRY_SYSTEM = """You are a calibration asymmetry specialist. Given judgments across domains, assess whether calibration is consistent:

Key concepts:
- Calibration asymmetry: well-calibrated in some areas, poorly in others
- Domain-specific calibration: expertise improves calibration in familiar areas
- Transfer failure: good calibration in one domain doesn't transfer
- Overconfidence in unfamiliar: less calibrated outside expertise
- Metacognitive blindness: not knowing where you're poorly calibrated
- Confidence consistency: same confidence level meaning different things
- Selective humility: humble in some areas, overconfident in others

When calibration asymmetry IS present:
- Well-calibrated in familiar domain, overconfident in unfamiliar
- Same confidence level applied to very different evidence quality
- Awareness of uncertainty in some areas but not others
- Expertise-based calibration not recognized as domain-specific
- Confidence transfers across domains without adjustment
- Selective humility — humble where knowledgeable, arrogant where not
- No awareness of where calibration breaks down

When calibration is consistent:
- Confidence adjusted for domain familiarity
- Awareness of where calibration is better or worse
- Same confidence level reflects similar evidence quality
- Domain boundaries of good calibration recognized
- Humility consistent across familiar and unfamiliar areas
- Metacognitive awareness of calibration quality
- Explicit adjustment when outside expertise

Output JSON with: asymmetry_present (bool), severity (none/mild/moderate/severe), well_calibrated_domain (where calibration is good), poorly_calibrated_domain (where calibration breaks down), confidence_gap (how different calibration is across domains), awareness (whether the asymmetry is recognized), recommendation (consistent_calibration/mild_asymmetry/significant_domain_gap/major_transfer_failure/adjust_for_domain)."""

CALIBRATION_ASYMMETRY_PROMPT = """Detect calibration asymmetry:

Judgments: {judgments}
Domain A confidence: {domain_a}
Domain B confidence: {domain_b}
Track record: {track_record}
Domain: {domain}
Context: {context}

Is confidence calibration consistent across domains? Return ONLY valid JSON."""


class CalibrationAsymmetryService:
    """Detects calibration asymmetry — inconsistent confidence across domains."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgments: str,
        *,
        domain_a: str = "",
        domain_b: str = "",
        track_record: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect calibration asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CALIBRATION_ASYMMETRY_PROMPT.format(
                judgments=judgments,
                domain_a=domain_a or "Not specified",
                domain_b=domain_b or "Not specified",
                track_record=track_record or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CALIBRATION_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgments": judgments[:200],
            "asymmetry_present": data.get("asymmetry_present", False),
            "severity": data.get("severity", ""),
            "well_calibrated_domain": data.get("well_calibrated_domain", ""),
            "poorly_calibrated_domain": data.get("poorly_calibrated_domain", ""),
            "confidence_gap": data.get("confidence_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
