"""EpistemicComplexityAddictionService — Epistemic Complexity Addiction Detection.

Detects epistemic complexity addiction — compulsive pursuit of ever-greater
complexity, unable to accept simple explanations.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPLEXITY_ADDICTION_SYSTEM = """You are an epistemic complexity addiction specialist. Given compulsive pursuit of complexity, assess addiction:

Key concepts:
- Epistemic complexity addiction: compulsive need for more complexity
- Simplicity rejection: simple answers feel wrong or insufficient
- Elaboration compulsion: must always add more layers
- Occam's razor violation: preferring complex over parsimonious
- Intellectual elitism: complexity as status marker
- Paralysis by analysis: too complex to act on
- Diminishing returns: complexity without added understanding

When epistemic complexity addiction IS present:
- Compulsive need for more complexity
- Simple answers feel wrong
- Must always add layers
- Preferring complex over simple
- Complexity as status
- Too complex to act
- Complexity without understanding

When no complexity addiction:
- Comfortable with simplicity
- Simple answers accepted
- Appropriate elaboration
- Parsimony valued
- Substance over complexity
- Actionable understanding
- Complexity adds value

Output JSON with: complexity_addiction_detected (bool), severity (none/mild/moderate/severe), simplicity_rejection (what rejecting), elaboration_compulsion (what adding), occam_violation (what preferring complex), paralysis_pattern (what too complex), recommendation (no_complexity_addiction/mild_simplicity_practice/significant_parsimony_building/major_intensive_addiction_work/emergency_severe_paralysis)."""

EPISTEMIC_COMPLEXITY_ADDICTION_PROMPT = """Detect epistemic complexity addiction:

Simplicity rejection: {simplicity_rejection}
Elaboration compulsion: {elaboration_compulsion}
Occam violation: {occam_violation}
Paralysis pattern: {paralysis_pattern}
Domain: {domain}
Context: {context}

Is there compulsive pursuit of ever-greater complexity unable to accept simple? Return ONLY valid JSON."""


class EpistemicComplexityAddictionService:
    """Detects epistemic complexity addiction — compulsive pursuit of complexity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        simplicity_rejection: str,
        *,
        elaboration_compulsion: str = "",
        occam_violation: str = "",
        paralysis_pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic complexity addiction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPLEXITY_ADDICTION_PROMPT.format(
                simplicity_rejection=simplicity_rejection,
                elaboration_compulsion=elaboration_compulsion or "Not specified",
                occam_violation=occam_violation or "Not specified",
                paralysis_pattern=paralysis_pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPLEXITY_ADDICTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "simplicity_rejection": simplicity_rejection[:200],
            "complexity_addiction_detected": data.get("complexity_addiction_detected", False),
            "severity": data.get("severity", ""),
            "elaboration_compulsion": data.get("elaboration_compulsion", ""),
            "occam_violation": data.get("occam_violation", ""),
            "paralysis_pattern": data.get("paralysis_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }
