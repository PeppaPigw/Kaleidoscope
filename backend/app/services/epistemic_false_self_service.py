"""EpistemicFalseSelfService — Epistemic False Self Detection.

Detects epistemic false self — presenting a compliant intellectual facade
while the true intellectual self remains hidden and protected.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FALSE_SELF_SYSTEM = """You are an epistemic false self specialist. Given compliant intellectual facade, assess false self:

Key concepts:
- Epistemic false self: compliant facade hiding true thinking
- Compliance: saying what others want to hear intellectually
- True self hiding: real thoughts kept secret
- Performance: intellectual life as act not authenticity
- Adaptation: becoming what environment demands
- Inauthenticity: disconnect between expressed and felt beliefs
- Protection: false self shields vulnerable true self

When epistemic false self IS present:
- Compliant facade hiding true thinking
- Saying what others want
- Real thoughts kept secret
- Intellectual life as act
- Becoming what demanded
- Disconnect expressed vs felt
- False self shielding true

When no false self:
- Authentic expression
- Saying what one thinks
- Thoughts shared openly
- Genuine intellectual life
- Being oneself
- Congruent expression
- No need for shield

Output JSON with: false_self_detected (bool), severity (none/mild/moderate/severe), compliance_pattern (what performing), true_self_hiding (what concealing), inauthenticity_level (what disconnect), protection_function (what shielding), recommendation (no_false_self/mild_authenticity_practice/significant_true_self_exploration/major_intensive_integration/emergency_complete_facade)."""

EPISTEMIC_FALSE_SELF_PROMPT = """Detect epistemic false self:

Compliance pattern: {compliance_pattern}
True self hiding: {true_self_hiding}
Inauthenticity level: {inauthenticity_level}
Protection function: {protection_function}
Domain: {domain}
Context: {context}

Is there a compliant intellectual facade hiding the true intellectual self? Return ONLY valid JSON."""


class EpistemicFalseSelfService:
    """Detects epistemic false self — compliant facade hiding true thinking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        compliance_pattern: str,
        *,
        true_self_hiding: str = "",
        inauthenticity_level: str = "",
        protection_function: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic false self."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FALSE_SELF_PROMPT.format(
                compliance_pattern=compliance_pattern,
                true_self_hiding=true_self_hiding or "Not specified",
                inauthenticity_level=inauthenticity_level or "Not specified",
                protection_function=protection_function or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FALSE_SELF_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "compliance_pattern": compliance_pattern[:200],
            "false_self_detected": data.get("false_self_detected", False),
            "severity": data.get("severity", ""),
            "true_self_hiding": data.get("true_self_hiding", ""),
            "inauthenticity_level": data.get("inauthenticity_level", ""),
            "protection_function": data.get("protection_function", ""),
            "recommendation": data.get("recommendation", ""),
        }
