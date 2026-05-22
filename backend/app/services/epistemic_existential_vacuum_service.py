"""EpistemicExistentialVacuumService — Epistemic Existential Vacuum Detection.

Detects epistemic existential vacuum — profound emptiness from loss of
intellectual purpose or meaning, the void left when frameworks collapse.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXISTENTIAL_VACUUM_SYSTEM = """You are an epistemic existential vacuum specialist. Given intellectual emptiness, assess existential vacuum:

Key concepts:
- Epistemic existential vacuum: profound emptiness from lost purpose
- Meaninglessness: nothing matters intellectually
- Boredom: chronic intellectual understimulation
- Purposelessness: no direction or goal
- Nihilism: rejection of all intellectual value
- Apathy: inability to care about ideas
- Void: the space left by collapsed frameworks

When epistemic existential vacuum IS present:
- Profound emptiness
- Nothing matters intellectually
- Chronic understimulation
- No direction or goal
- Rejecting all value
- Unable to care
- Void from collapse

When no existential vacuum:
- Fullness of purpose
- Things matter
- Intellectually engaged
- Clear direction
- Values intact
- Caring deeply
- Frameworks supporting

Output JSON with: existential_vacuum_detected (bool), severity (none/mild/moderate/severe), meaninglessness_level (what emptiness), purposelessness (what no direction), apathy_pattern (what cannot care), void_source (what collapsed), recommendation (no_existential_vacuum/mild_meaning_exploration/significant_existential_therapy/major_intensive_reconstruction/emergency_complete_nihilism)."""

EPISTEMIC_EXISTENTIAL_VACUUM_PROMPT = """Detect epistemic existential vacuum:

Meaninglessness level: {meaninglessness_level}
Purposelessness: {purposelessness}
Apathy pattern: {apathy_pattern}
Void source: {void_source}
Domain: {domain}
Context: {context}

Is there profound emptiness from loss of intellectual purpose or meaning? Return ONLY valid JSON."""


class EpistemicExistentialVacuumService:
    """Detects epistemic existential vacuum — profound intellectual emptiness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        meaninglessness_level: str,
        *,
        purposelessness: str = "",
        apathy_pattern: str = "",
        void_source: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic existential vacuum."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXISTENTIAL_VACUUM_PROMPT.format(
                meaninglessness_level=meaninglessness_level,
                purposelessness=purposelessness or "Not specified",
                apathy_pattern=apathy_pattern or "Not specified",
                void_source=void_source or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXISTENTIAL_VACUUM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "meaninglessness_level": meaninglessness_level[:200],
            "existential_vacuum_detected": data.get("existential_vacuum_detected", False),
            "severity": data.get("severity", ""),
            "purposelessness": data.get("purposelessness", ""),
            "apathy_pattern": data.get("apathy_pattern", ""),
            "void_source": data.get("void_source", ""),
            "recommendation": data.get("recommendation", ""),
        }
