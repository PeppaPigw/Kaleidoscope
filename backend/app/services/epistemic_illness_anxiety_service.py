"""EpistemicIllnessAnxietyService — Epistemic Illness Anxiety Detection.

Detects epistemic illness anxiety — excessive worry about intellectual
health with misinterpretation of normal cognitive variations as disease.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ILLNESS_ANXIETY_SYSTEM = """You are an epistemic illness anxiety specialist. Given excessive intellectual health worry, assess illness anxiety:

Key concepts:
- Epistemic illness anxiety: excessive worry about intellectual health
- Misinterpretation: normal variations seen as disease
- Reassurance seeking: constantly checking intellectual function
- Body scanning: monitoring every cognitive fluctuation
- Catastrophizing: minor lapses interpreted as serious decline
- Doctor shopping: seeking multiple opinions on intellectual health
- Preoccupation: consumed by worry about cognitive decline

When epistemic illness anxiety IS present:
- Excessive worry about health
- Normal variations seen as disease
- Constantly checking function
- Monitoring every fluctuation
- Minor lapses as serious decline
- Seeking multiple opinions
- Consumed by worry

When no illness anxiety:
- Proportionate health concern
- Normal variations accepted
- No excessive checking
- Not monitoring fluctuations
- Proportionate interpretation
- Appropriate help-seeking
- Not consumed by worry

Output JSON with: illness_anxiety_detected (bool), severity (none/mild/moderate/severe), worry_level (what preoccupation), misinterpretation (what catastrophizing), reassurance_seeking (what checking), body_scanning (what monitoring), recommendation (no_illness_anxiety/mild_psychoeducation/significant_cbt/major_intensive_therapy/emergency_complete_preoccupation)."""

EPISTEMIC_ILLNESS_ANXIETY_PROMPT = """Detect epistemic illness anxiety:

Worry level: {worry_level}
Misinterpretation: {misinterpretation}
Reassurance seeking: {reassurance_seeking}
Body scanning: {body_scanning}
Domain: {domain}
Context: {context}

Is there excessive worry about intellectual health with misinterpretation of normal variations? Return ONLY valid JSON."""


class EpistemicIllnessAnxietyService:
    """Detects epistemic illness anxiety — excessive intellectual health worry."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        worry_level: str,
        *,
        misinterpretation: str = "",
        reassurance_seeking: str = "",
        body_scanning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic illness anxiety."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ILLNESS_ANXIETY_PROMPT.format(
                worry_level=worry_level,
                misinterpretation=misinterpretation or "Not specified",
                reassurance_seeking=reassurance_seeking or "Not specified",
                body_scanning=body_scanning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ILLNESS_ANXIETY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "worry_level": worry_level[:200],
            "illness_anxiety_detected": data.get("illness_anxiety_detected", False),
            "severity": data.get("severity", ""),
            "misinterpretation": data.get("misinterpretation", ""),
            "reassurance_seeking": data.get("reassurance_seeking", ""),
            "body_scanning": data.get("body_scanning", ""),
            "recommendation": data.get("recommendation", ""),
        }
