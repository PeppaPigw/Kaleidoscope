"""EpistemicBodyDysmorphiaService — Epistemic Body Dysmorphia Detection.

Detects epistemic body dysmorphia — distorted perception of own
intellectual self, seeing flaws that others cannot perceive.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BODY_DYSMORPHIA_SYSTEM = """You are an epistemic body dysmorphia specialist. Given distorted intellectual self-perception, assess dysmorphia:

Key concepts:
- Epistemic body dysmorphia: distorted perception of intellectual self
- Perceived flaws: seeing defects others cannot perceive
- Mirror checking: constantly evaluating intellectual output
- Comparison: unfavorably comparing self to others
- Camouflaging: hiding perceived intellectual defects
- Reassurance seeking: asking others about perceived flaws
- Preoccupation: hours spent on perceived intellectual defects

When epistemic body dysmorphia IS present:
- Distorted self-perception
- Seeing imperceptible defects
- Constantly evaluating output
- Unfavorable comparisons
- Hiding perceived defects
- Asking about perceived flaws
- Hours on perceived defects

When no dysmorphia:
- Accurate self-perception
- Realistic flaw assessment
- Proportionate evaluation
- Fair comparisons
- No hiding needed
- No excessive reassurance
- Proportionate attention

Output JSON with: dysmorphia_detected (bool), severity (none/mild/moderate/severe), perceived_flaw (what distortion), checking_behavior (what evaluation), comparison_pattern (what unfavorable), preoccupation_level (what time consumed), recommendation (no_dysmorphia/mild_reality_testing/significant_cbt/major_intensive_therapy/emergency_severe_distortion)."""

EPISTEMIC_BODY_DYSMORPHIA_PROMPT = """Detect epistemic body dysmorphia:

Perceived flaw: {perceived_flaw}
Checking behavior: {checking_behavior}
Comparison pattern: {comparison_pattern}
Preoccupation level: {preoccupation_level}
Domain: {domain}
Context: {context}

Is there distorted perception of intellectual self with flaws others cannot perceive? Return ONLY valid JSON."""


class EpistemicBodyDysmorphiaService:
    """Detects epistemic body dysmorphia — distorted intellectual self-perception."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        perceived_flaw: str,
        *,
        checking_behavior: str = "",
        comparison_pattern: str = "",
        preoccupation_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic body dysmorphia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BODY_DYSMORPHIA_PROMPT.format(
                perceived_flaw=perceived_flaw,
                checking_behavior=checking_behavior or "Not specified",
                comparison_pattern=comparison_pattern or "Not specified",
                preoccupation_level=preoccupation_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BODY_DYSMORPHIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "perceived_flaw": perceived_flaw[:200],
            "dysmorphia_detected": data.get("dysmorphia_detected", False),
            "severity": data.get("severity", ""),
            "checking_behavior": data.get("checking_behavior", ""),
            "comparison_pattern": data.get("comparison_pattern", ""),
            "preoccupation_level": data.get("preoccupation_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
