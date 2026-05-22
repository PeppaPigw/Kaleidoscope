"""PrecisionAccuracyConfusionService — Precision-Accuracy Confusion Detection.

Detects precision-accuracy confusion — confusing precise measurements
with accurate ones, where precision refers to consistency/resolution
and accuracy refers to closeness to the true value.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PRECISION_ACCURACY_CONFUSION_SYSTEM = """You are a precision-accuracy confusion specialist. Given a measurement claim, assess whether precision is being confused with accuracy:

Key concepts:
- Precision: consistency, resolution, number of decimal places
- Accuracy: closeness to true value
- Systematic error: precise but consistently wrong (accurate aim, wrong target)
- Random error: accurate on average but imprecise (right target, scattered shots)
- False precision: reporting more decimal places than justified
- Calibration: ensuring precision and accuracy align
- Significant figures: precision appropriate to measurement method

When precision-accuracy confusion IS present:
- Precise numbers assumed to be accurate
- Many decimal places treated as evidence of correctness
- Systematic errors ignored because measurements are consistent
- Precision of reporting exceeds precision of measurement
- Calibration not verified
- Consistent results assumed to be correct results
- Resolution confused with validity

When distinction is maintained:
- Precision and accuracy distinguished explicitly
- Systematic errors checked for
- Calibration verified against known standards
- Reporting precision matches measurement precision
- Consistency not confused with correctness
- Both random and systematic error considered
- Appropriate significant figures used

Output JSON with: confusion_present (bool), severity (none/mild/moderate/severe), measurement (what is measured), precision_claimed (what precision is reported), accuracy_evidence (what evidence of accuracy exists), systematic_risk (what systematic errors might exist), recommendation (distinction_maintained/mild_conflation/significant_confusion/major_false_precision/verify_accuracy_independently)."""

PRECISION_ACCURACY_CONFUSION_PROMPT = """Detect precision-accuracy confusion:

Claim: {claim}
Measurement: {measurement}
Precision: {precision}
Calibration: {calibration}
Domain: {domain}
Context: {context}

Is precision being confused with accuracy in this measurement? Return ONLY valid JSON."""


class PrecisionAccuracyConfusionService:
    """Detects precision-accuracy confusion — precise doesn't mean accurate."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        measurement: str = "",
        precision: str = "",
        calibration: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect precision-accuracy confusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PRECISION_ACCURACY_CONFUSION_PROMPT.format(
                claim=claim,
                measurement=measurement or "Not specified",
                precision=precision or "Not specified",
                calibration=calibration or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PRECISION_ACCURACY_CONFUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "confusion_present": data.get("confusion_present", False),
            "severity": data.get("severity", ""),
            "precision_claimed": data.get("precision_claimed", ""),
            "accuracy_evidence": data.get("accuracy_evidence", ""),
            "systematic_risk": data.get("systematic_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
