"""EpistemicIntellectualMirroringService — Epistemic Intellectual Mirroring Detection.

Detects epistemic intellectual mirroring — unconsciously mirroring another's
intellectual positions without awareness.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_MIRRORING_SYSTEM = """You are an epistemic intellectual mirroring specialist. Given unconsciously mirroring positions, assess intellectual mirroring:

Key concepts:
- Epistemic intellectual mirroring: unconsciously mirroring another's positions
- Unconscious adoption: adopting views without realizing it
- Intellectual chameleon: changing views to match whoever one is with
- Social epistemic pressure: views shaped by social pressure
- Conformity without awareness: conforming without knowing one is conforming
- Borrowed thinking: thinking that is borrowed not generated
- Intellectual ventriloquism: speaking another's thoughts as one's own

When epistemic intellectual mirroring IS present:
- Unconsciously mirroring positions
- Adopting views without realizing
- Changing views to match company
- Views shaped by social pressure
- Conforming without awareness
- Thinking borrowed not generated
- Speaking another's thoughts as own

When no intellectual mirroring:
- Aware of influences
- Conscious adoption of views
- Consistent views across contexts
- Views independent of social pressure
- Aware of conformity tendencies
- Thinking genuinely generated
- Speaking own thoughts

Output JSON with: intellectual_mirroring_detected (bool), severity (none/mild/moderate/severe), unconscious_adoption (what adopting without realizing), intellectual_chameleon (how changing to match), social_epistemic_pressure (what shaped by social pressure), borrowed_thinking (what thinking borrowed from whom), recommendation (no_intellectual_mirroring/mild_awareness_practice/significant_independence_building/major_intensive_self_differentiation/emergency_complete_unconscious_mirroring)."""

EPISTEMIC_INTELLECTUAL_MIRRORING_PROMPT = """Detect epistemic intellectual mirroring:

Unconscious adoption: {unconscious_adoption}
Intellectual chameleon: {intellectual_chameleon}
Social epistemic pressure: {social_epistemic_pressure}
Borrowed thinking: {borrowed_thinking}
Domain: {domain}
Context: {context}

Is there unconsciously mirroring another's intellectual positions? Return ONLY valid JSON."""


class EpistemicIntellectualMirroringService:
    """Detects epistemic intellectual mirroring — unconsciously mirroring positions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        unconscious_adoption: str,
        *,
        intellectual_chameleon: str = "",
        social_epistemic_pressure: str = "",
        borrowed_thinking: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual mirroring."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_MIRRORING_PROMPT.format(
                unconscious_adoption=unconscious_adoption,
                intellectual_chameleon=intellectual_chameleon or "Not specified",
                social_epistemic_pressure=social_epistemic_pressure or "Not specified",
                borrowed_thinking=borrowed_thinking or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_MIRRORING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "unconscious_adoption": unconscious_adoption[:200],
            "intellectual_mirroring_detected": data.get("intellectual_mirroring_detected", False),
            "severity": data.get("severity", ""),
            "intellectual_chameleon": data.get("intellectual_chameleon", ""),
            "social_epistemic_pressure": data.get("social_epistemic_pressure", ""),
            "borrowed_thinking": data.get("borrowed_thinking", ""),
            "recommendation": data.get("recommendation", ""),
        }
