"""EpistemicCriticalExponentService — Epistemic Critical Exponent Detection.

Detects epistemic critical exponent — universal scaling behavior near
intellectual phase transitions, independent of microscopic details.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CRITICAL_EXPONENT_SYSTEM = """You are an epistemic critical exponent specialist. Given an intellectual transition, assess whether universal scaling behavior appears:

Key concepts:
- Epistemic critical exponent: universal scaling near transitions
- Universality class: different systems sharing same exponents
- Power law: quantities diverging as power of distance from transition
- Correlation length: range of intellectual influence diverging
- Scaling relation: exponents related by mathematical identities
- Renormalization group: flow explaining universality
- Critical slowing: dynamics slowing near transition

When epistemic critical exponent IS present:
- Universal scaling behavior near intellectual transitions
- Different systems sharing same scaling behavior
- Quantities diverging as power laws
- Range of influence diverging near transition
- Exponents related by mathematical identities
- Flow explaining why different systems behave same
- Dynamics slowing dramatically near transition

When non-critical behavior is present:
- No universal scaling
- Each system behaving uniquely
- No power law divergences
- Finite range of influence
- No exponent relations
- No universality explanation
- Normal dynamics

Output JSON with: critical_exponent_present (bool), severity (none/mild/moderate/severe), universality_class (what shared behavior), power_law (what divergence), correlation_length (what influence range), critical_slowing (what dynamics slowdown), recommendation (non_critical/mild_critical/significant_critical_exponent/major_universality/identify_universality_class)."""

EPISTEMIC_CRITICAL_EXPONENT_PROMPT = """Detect epistemic critical exponent:

Universality class: {universality_class}
Power law: {power_law}
Correlation length: {correlation_length}
Critical slowing: {critical_slowing}
Domain: {domain}
Context: {context}

Is universal scaling behavior appearing near intellectual phase transitions, independent of microscopic details? Return ONLY valid JSON."""


class EpistemicCriticalExponentService:
    """Detects epistemic critical exponent — universal scaling near transitions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        universality_class: str,
        *,
        power_law: str = "",
        correlation_length: str = "",
        critical_slowing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic critical exponent."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CRITICAL_EXPONENT_PROMPT.format(
                universality_class=universality_class,
                power_law=power_law or "Not specified",
                correlation_length=correlation_length or "Not specified",
                critical_slowing=critical_slowing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CRITICAL_EXPONENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "universality_class": universality_class[:200],
            "critical_exponent_present": data.get("critical_exponent_present", False),
            "severity": data.get("severity", ""),
            "power_law": data.get("power_law", ""),
            "correlation_length": data.get("correlation_length", ""),
            "critical_slowing": data.get("critical_slowing", ""),
            "recommendation": data.get("recommendation", ""),
        }
