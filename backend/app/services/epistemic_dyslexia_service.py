"""EpistemicDyslexiaService — Epistemic Dyslexia Detection.

Detects epistemic dyslexia — difficulty processing intellectual symbols
and patterns despite adequate intelligence and exposure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DYSLEXIA_SYSTEM = """You are an epistemic dyslexia specialist. Given intellectual processing difficulty, assess dyslexia patterns:

Key concepts:
- Epistemic dyslexia: difficulty processing intellectual symbols
- Decoding: struggling to interpret intellectual patterns
- Fluency: slow and effortful intellectual processing
- Comprehension gap: understanding lags behind effort
- Phonological: difficulty with intellectual sound-symbol mapping
- Compensation: developing workarounds for processing gaps
- Strength-based: leveraging other cognitive strengths

When epistemic dyslexia IS present:
- Difficulty processing symbols
- Struggling to interpret patterns
- Slow effortful processing
- Understanding lags behind effort
- Sound-symbol mapping difficulty
- Developing workarounds
- Other strengths compensating

When no dyslexia:
- Fluent symbol processing
- Easy pattern interpretation
- Efficient processing
- Understanding matches effort
- Natural mapping
- No workarounds needed
- Balanced cognitive profile

Output JSON with: dyslexia_detected (bool), severity (none/mild/moderate/severe), decoding_difficulty (what interpretation struggle), fluency_level (what processing speed), comprehension_gap (what understanding lag), compensation_strategies (what workarounds), recommendation (no_dyslexia/mild_accommodation/significant_structured_support/major_intensive_remediation/emergency_complete_processing_failure)."""

EPISTEMIC_DYSLEXIA_PROMPT = """Detect epistemic dyslexia:

Decoding difficulty: {decoding_difficulty}
Fluency level: {fluency_level}
Comprehension gap: {comprehension_gap}
Compensation strategies: {compensation_strategies}
Domain: {domain}
Context: {context}

Is there difficulty processing intellectual symbols despite adequate intelligence? Return ONLY valid JSON."""


class EpistemicDyslexiaService:
    """Detects epistemic dyslexia — difficulty processing intellectual symbols."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decoding_difficulty: str,
        *,
        fluency_level: str = "",
        comprehension_gap: str = "",
        compensation_strategies: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dyslexia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DYSLEXIA_PROMPT.format(
                decoding_difficulty=decoding_difficulty,
                fluency_level=fluency_level or "Not specified",
                comprehension_gap=comprehension_gap or "Not specified",
                compensation_strategies=compensation_strategies or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DYSLEXIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decoding_difficulty": decoding_difficulty[:200],
            "dyslexia_detected": data.get("dyslexia_detected", False),
            "severity": data.get("severity", ""),
            "fluency_level": data.get("fluency_level", ""),
            "comprehension_gap": data.get("comprehension_gap", ""),
            "compensation_strategies": data.get("compensation_strategies", ""),
            "recommendation": data.get("recommendation", ""),
        }
