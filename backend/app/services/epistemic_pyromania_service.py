"""EpistemicPyromaniaService — Epistemic Pyromania Detection.

Detects epistemic pyromania — compulsive urge to burn down intellectual
structures, destroy frameworks, and watch ideas combust.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PYROMANIA_SYSTEM = """You are an epistemic pyromania specialist. Given compulsive intellectual destruction, assess pyromania:

Key concepts:
- Epistemic pyromania: compulsive urge to destroy intellectual structures
- Fascination: drawn to watching frameworks burn
- Tension-relief: building pressure released by destruction
- Gratification: pleasure from intellectual demolition
- Not strategic: destruction not for gain but for impulse
- Repeated: pattern of burning down what was built
- Aftermath: surveying intellectual wreckage with satisfaction

When epistemic pyromania IS present:
- Compulsive destruction urge
- Fascinated by framework collapse
- Tension released by destruction
- Pleasure from demolition
- Not strategic or purposeful
- Pattern of burning down
- Satisfaction from wreckage

When no pyromania:
- Constructive approach
- No fascination with collapse
- No tension-destruction cycle
- No pleasure from demolition
- Strategic when deconstructing
- Building rather than burning
- No satisfaction from wreckage

Output JSON with: pyromania_detected (bool), severity (none/mild/moderate/severe), destruction_urge (what compulsion), fascination_level (what attraction to collapse), tension_pattern (what buildup-release), gratification_type (what pleasure), recommendation (no_pyromania/mild_channeling/significant_impulse_control/major_intensive_therapy/emergency_active_destruction)."""

EPISTEMIC_PYROMANIA_PROMPT = """Detect epistemic pyromania:

Destruction urge: {destruction_urge}
Fascination level: {fascination_level}
Tension pattern: {tension_pattern}
Gratification type: {gratification_type}
Domain: {domain}
Context: {context}

Is there compulsive urge to burn down intellectual structures and watch ideas combust? Return ONLY valid JSON."""


class EpistemicPyromaniaService:
    """Detects epistemic pyromania — compulsive intellectual destruction."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        destruction_urge: str,
        *,
        fascination_level: str = "",
        tension_pattern: str = "",
        gratification_type: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic pyromania."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PYROMANIA_PROMPT.format(
                destruction_urge=destruction_urge,
                fascination_level=fascination_level or "Not specified",
                tension_pattern=tension_pattern or "Not specified",
                gratification_type=gratification_type or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PYROMANIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "destruction_urge": destruction_urge[:200],
            "pyromania_detected": data.get("pyromania_detected", False),
            "severity": data.get("severity", ""),
            "fascination_level": data.get("fascination_level", ""),
            "tension_pattern": data.get("tension_pattern", ""),
            "gratification_type": data.get("gratification_type", ""),
            "recommendation": data.get("recommendation", ""),
        }
