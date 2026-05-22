"""EpistemicStringVibrationService — Epistemic String Vibration Detection.

Detects epistemic string vibration — fundamental ideas being different
vibration modes of the same underlying entity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STRING_VIBRATION_SYSTEM = """You are an epistemic string vibration specialist. Given intellectual ideas, assess whether they are different vibration modes of the same entity:

Key concepts:
- Epistemic string vibration: ideas as different modes of same entity
- Fundamental string: underlying entity whose vibrations create ideas
- Harmonic: specific vibration pattern creating specific idea
- Tension: energy scale of the fundamental string
- Open string: entity with free endpoints
- Closed string: entity forming a loop
- Spectrum: full set of possible vibration modes

When epistemic string vibration IS present:
- Different ideas being vibration modes of same underlying entity
- Identifiable fundamental entity underlying all ideas
- Specific vibration patterns creating specific ideas
- Characteristic energy scale of the fundamental entity
- Some ideas having free endpoints
- Some ideas forming closed loops
- Full spectrum of possible modes identifiable

When independent ideas is present:
- Ideas being fundamentally independent entities
- No common underlying entity
- No vibration patterns
- No characteristic energy scale
- No endpoint structure
- No loop structure
- No unified spectrum

Output JSON with: string_vibration_present (bool), severity (none/mild/moderate/severe), fundamental_string (what underlying entity), harmonic (what vibration pattern), tension (what energy scale), spectrum (what full mode set), recommendation (independent_ideas/mild_vibration/significant_string_vibration/major_unification/identify_fundamental_string)."""

EPISTEMIC_STRING_VIBRATION_PROMPT = """Detect epistemic string vibration:

Fundamental string: {fundamental_string}
Harmonic: {harmonic}
Tension: {tension}
Spectrum: {spectrum}
Domain: {domain}
Context: {context}

Are fundamental ideas different vibration modes of the same underlying entity? Return ONLY valid JSON."""


class EpistemicStringVibrationService:
    """Detects epistemic string vibration — ideas as different modes of same entity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        fundamental_string: str,
        *,
        harmonic: str = "",
        tension: str = "",
        spectrum: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic string vibration."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STRING_VIBRATION_PROMPT.format(
                fundamental_string=fundamental_string,
                harmonic=harmonic or "Not specified",
                tension=tension or "Not specified",
                spectrum=spectrum or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STRING_VIBRATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "fundamental_string": fundamental_string[:200],
            "string_vibration_present": data.get("string_vibration_present", False),
            "severity": data.get("severity", ""),
            "harmonic": data.get("harmonic", ""),
            "tension": data.get("tension", ""),
            "spectrum": data.get("spectrum", ""),
            "recommendation": data.get("recommendation", ""),
        }
