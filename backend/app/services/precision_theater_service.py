"""PrecisionTheaterService — Precision Theater Detection.

Detects precision theater — false precision that creates an illusion
of rigor without substance, using exact numbers, decimal places, or
quantitative language to mask fundamental uncertainty or ignorance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PRECISION_THEATER_SYSTEM = """You are a precision theater specialist. Given a quantitative claim, assess whether false precision creates an illusion of rigor:

Key concepts:
- Precision theater: false precision masking uncertainty
- Spurious precision: more decimal places than data supports
- Quantitative veneer: numbers hiding qualitative judgment
- Rigor illusion: appearance of rigor without substance
- Measurement theater: measuring what's easy, not what matters
- False exactitude: exact numbers for inherently uncertain things
- Precision-accuracy confusion: precise but not accurate

When precision theater IS present:
- Precision exceeds what data or methods support
- Numbers mask fundamental uncertainty
- Quantitative language hides qualitative judgment
- Exact figures given for inherently uncertain quantities
- Measurement precision confused with accuracy
- Decimal places create false confidence
- Rigor is performed rather than achieved

When precision is appropriate:
- Precision matched to measurement capability
- Uncertainty explicitly stated alongside precision
- Quantification appropriate to the phenomenon
- Precision serves communication, not theater
- Measurement validity established
- Accuracy and precision distinguished
- Limitations of quantification acknowledged

Output JSON with: theater_present (bool), severity (none/mild/moderate/severe), claim (what is claimed), precision_level (what precision is offered), supported_precision (what precision data supports), uncertainty_hidden (what uncertainty is masked), recommendation (appropriate_precision/mild_over_precision/significant_precision_theater/major_false_exactitude/match_precision_to_knowledge)."""

PRECISION_THEATER_PROMPT = """Detect precision theater:

Claim: {claim}
Precision offered: {precision}
Data basis: {data}
Uncertainty acknowledged: {uncertainty}
Domain: {domain}
Context: {context}

Does this claim use false precision to create an illusion of rigor? Return ONLY valid JSON."""


class PrecisionTheaterService:
    """Detects precision theater — false precision masking uncertainty."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        precision: str = "",
        data: str = "",
        uncertainty: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect precision theater."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PRECISION_THEATER_PROMPT.format(
                claim=claim,
                precision=precision or "Not specified",
                data=data or "Not specified",
                uncertainty=uncertainty or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PRECISION_THEATER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data_parsed = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "theater_present": data_parsed.get("theater_present", False),
            "severity": data_parsed.get("severity", ""),
            "precision_level": data_parsed.get("precision_level", ""),
            "supported_precision": data_parsed.get("supported_precision", ""),
            "uncertainty_hidden": data_parsed.get("uncertainty_hidden", ""),
            "recommendation": data_parsed.get("recommendation", ""),
        }
