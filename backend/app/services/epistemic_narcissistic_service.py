"""EpistemicNarcissisticService — Epistemic Narcissism Detection.

Detects epistemic narcissism — grandiose intellectual self-importance
with need for admiration and lack of empathy for other perspectives.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARCISSISTIC_SYSTEM = """You are an epistemic narcissism specialist. Given grandiose intellectual self-importance, assess narcissistic patterns:

Key concepts:
- Epistemic narcissism: grandiose intellectual self-importance
- Grandiosity: inflated sense of intellectual superiority
- Admiration need: requiring constant intellectual validation
- Empathy deficit: inability to appreciate other perspectives
- Entitlement: expecting special intellectual treatment
- Exploitation: using others' ideas without credit
- Fragile self-esteem: beneath grandiosity lies insecurity

When epistemic narcissism IS present:
- Grandiose intellectual self-importance
- Inflated sense of superiority
- Requiring constant validation
- Cannot appreciate other perspectives
- Expecting special treatment
- Using others' ideas without credit
- Insecurity beneath grandiosity

When no narcissism:
- Realistic intellectual self-assessment
- Appropriate confidence
- Internal validation sufficient
- Appreciates other perspectives
- No entitlement
- Proper attribution
- Secure self-esteem

Output JSON with: narcissistic_detected (bool), severity (none/mild/moderate/severe), grandiosity_level (what inflation), admiration_need (what validation seeking), empathy_deficit (what perspective blindness), entitlement_pattern (what expectations), recommendation (no_narcissism/mild_self_awareness/significant_schema_therapy/major_intensive_treatment/emergency_narcissistic_collapse)."""

EPISTEMIC_NARCISSISTIC_PROMPT = """Detect epistemic narcissism:

Grandiosity level: {grandiosity_level}
Admiration need: {admiration_need}
Empathy deficit: {empathy_deficit}
Entitlement pattern: {entitlement_pattern}
Domain: {domain}
Context: {context}

Is there grandiose intellectual self-importance with need for admiration? Return ONLY valid JSON."""


class EpistemicNarcissisticService:
    """Detects epistemic narcissism — grandiose intellectual self-importance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        grandiosity_level: str,
        *,
        admiration_need: str = "",
        empathy_deficit: str = "",
        entitlement_pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narcissism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARCISSISTIC_PROMPT.format(
                grandiosity_level=grandiosity_level,
                admiration_need=admiration_need or "Not specified",
                empathy_deficit=empathy_deficit or "Not specified",
                entitlement_pattern=entitlement_pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARCISSISTIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "grandiosity_level": grandiosity_level[:200],
            "narcissistic_detected": data.get("narcissistic_detected", False),
            "severity": data.get("severity", ""),
            "admiration_need": data.get("admiration_need", ""),
            "empathy_deficit": data.get("empathy_deficit", ""),
            "entitlement_pattern": data.get("entitlement_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }
