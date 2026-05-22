"""EpistemicDyscalculiaService — Epistemic Dyscalculia Detection.

Detects epistemic dyscalculia — specific deficit in quantitative
reasoning and numerical intellectual processing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DYSCALCULIA_SYSTEM = """You are an epistemic dyscalculia specialist. Given quantitative reasoning deficit, assess dyscalculia patterns:

Key concepts:
- Epistemic dyscalculia: deficit in quantitative reasoning
- Number sense: poor intuition for magnitudes and proportions
- Procedural: difficulty with step-by-step quantitative operations
- Conceptual: struggling with what numbers represent
- Spatial-temporal: difficulty with quantitative relationships
- Estimation: poor approximation abilities
- Math anxiety: emotional avoidance of quantitative thinking

When epistemic dyscalculia IS present:
- Deficit in quantitative reasoning
- Poor magnitude intuition
- Difficulty with operations
- Struggling with representations
- Difficulty with relationships
- Poor approximation
- Emotional avoidance

When no dyscalculia:
- Strong quantitative reasoning
- Good magnitude intuition
- Fluent operations
- Clear representations
- Natural relationships
- Good approximation
- Comfortable with numbers

Output JSON with: dyscalculia_detected (bool), severity (none/mild/moderate/severe), number_sense (what intuition deficit), procedural_difficulty (what operation struggle), conceptual_gap (what representation problem), estimation_ability (what approximation), recommendation (no_dyscalculia/mild_concrete_supports/significant_structured_remediation/major_intensive_program/emergency_complete_quantitative_failure)."""

EPISTEMIC_DYSCALCULIA_PROMPT = """Detect epistemic dyscalculia:

Number sense: {number_sense}
Procedural difficulty: {procedural_difficulty}
Conceptual gap: {conceptual_gap}
Estimation ability: {estimation_ability}
Domain: {domain}
Context: {context}

Is there specific deficit in quantitative reasoning and numerical processing? Return ONLY valid JSON."""


class EpistemicDyscalculiaService:
    """Detects epistemic dyscalculia — quantitative reasoning deficit."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        number_sense: str,
        *,
        procedural_difficulty: str = "",
        conceptual_gap: str = "",
        estimation_ability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dyscalculia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DYSCALCULIA_PROMPT.format(
                number_sense=number_sense,
                procedural_difficulty=procedural_difficulty or "Not specified",
                conceptual_gap=conceptual_gap or "Not specified",
                estimation_ability=estimation_ability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DYSCALCULIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "number_sense": number_sense[:200],
            "dyscalculia_detected": data.get("dyscalculia_detected", False),
            "severity": data.get("severity", ""),
            "procedural_difficulty": data.get("procedural_difficulty", ""),
            "conceptual_gap": data.get("conceptual_gap", ""),
            "estimation_ability": data.get("estimation_ability", ""),
            "recommendation": data.get("recommendation", ""),
        }
