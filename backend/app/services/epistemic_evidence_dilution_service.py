"""EpistemicEvidenceDilutionService — Epistemic Evidence Dilution Detection.

Detects epistemic evidence dilution — diluting strong evidence by mixing
with weak irrelevant evidence, reducing overall persuasive force.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EVIDENCE_DILUTION_SYSTEM = """You are an epistemic evidence dilution specialist. Given strong evidence diluted by weak additions, assess evidence dilution:

Key concepts:
- Epistemic evidence dilution: mixing strong evidence with weak to reduce force
- Quantity over quality: substituting many weak points for few strong ones
- Noise injection: injecting irrelevant information to obscure signal
- Argument padding: padding arguments with filler to seem comprehensive
- Strength averaging: averaging strong and weak evidence reducing overall strength
- Relevance flooding: flooding with marginally relevant evidence
- Signal drowning: drowning key evidence in sea of trivia

When epistemic evidence dilution IS present:
- Strong evidence diluted
- Quantity substituted for quality
- Noise injected
- Arguments padded
- Strength averaged down
- Relevance flooded
- Signal drowned

When no evidence dilution:
- Evidence curated for strength
- Quality prioritized
- Signal clear
- Arguments focused
- Strength preserved
- Relevance maintained
- Key evidence highlighted

Output JSON with: evidence_dilution_detected (bool), severity (none/mild/moderate/severe), quantity_over_quality (what quantity substituted), noise_injection (what noise injected), strength_averaging (what strength averaged), signal_drowning (what signal drowned), recommendation (no_evidence_dilution/mild_curation_practice/significant_evidence_focusing/major_intensive_signal_extraction/emergency_complete_evidence_dilution)."""

EPISTEMIC_EVIDENCE_DILUTION_PROMPT = """Detect epistemic evidence dilution:

Quantity over quality: {quantity_over_quality}
Noise injection: {noise_injection}
Strength averaging: {strength_averaging}
Signal drowning: {signal_drowning}
Domain: {domain}
Context: {context}

Is strong evidence being diluted by mixing with weak irrelevant evidence? Return ONLY valid JSON."""


class EpistemicEvidenceDilutionService:
    """Detects epistemic evidence dilution — strength diluted by weakness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        quantity_over_quality: str,
        *,
        noise_injection: str = "",
        strength_averaging: str = "",
        signal_drowning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic evidence dilution."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EVIDENCE_DILUTION_PROMPT.format(
                quantity_over_quality=quantity_over_quality,
                noise_injection=noise_injection or "Not specified",
                strength_averaging=strength_averaging or "Not specified",
                signal_drowning=signal_drowning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EVIDENCE_DILUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "quantity_over_quality": quantity_over_quality[:200],
            "evidence_dilution_detected": data.get("evidence_dilution_detected", False),
            "severity": data.get("severity", ""),
            "noise_injection": data.get("noise_injection", ""),
            "strength_averaging": data.get("strength_averaging", ""),
            "signal_drowning": data.get("signal_drowning", ""),
            "recommendation": data.get("recommendation", ""),
        }
