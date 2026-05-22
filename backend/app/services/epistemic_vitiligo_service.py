"""EpistemicVitiligoService — Epistemic Vitiligo Detection.

Detects epistemic vitiligo — loss of intellectual pigmentation creating
patches of colorless understanding where meaning has faded.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VITILIGO_SYSTEM = """You are an epistemic vitiligo specialist. Given loss of intellectual pigmentation, assess vitiligo:

Key concepts:
- Epistemic vitiligo: loss of intellectual pigmentation/meaning
- Depigmentation: areas where meaning has faded completely
- Autoimmune destruction: immune system destroying meaning-makers
- Segmental: affecting one area only
- Non-segmental: spreading across multiple areas
- Repigmentation: restoring lost meaning
- Koebner phenomenon: new patches at sites of intellectual trauma

When epistemic vitiligo IS present:
- Loss of intellectual pigmentation/meaning
- Areas where meaning completely faded
- Immune system destroying meaning-makers
- Affecting specific areas
- Spreading across multiple areas
- Unable to restore lost meaning
- New patches at trauma sites

When no vitiligo:
- Full intellectual pigmentation intact
- No areas of faded meaning
- Meaning-makers functioning
- No area-specific loss
- No spreading pattern
- Meaning naturally maintained
- No trauma-triggered loss

Output JSON with: vitiligo_detected (bool), severity (none/mild/moderate/severe), depigmentation_pattern (what areas affected), spread_status (what progression), autoimmune_component (what self-destruction), repigmentation_potential (what restoration possible), recommendation (no_vitiligo/mild_monitoring/significant_phototherapy/major_systemic_immunomodulation/emergency_rapid_spread)."""

EPISTEMIC_VITILIGO_PROMPT = """Detect epistemic vitiligo:

Depigmentation pattern: {depigmentation_pattern}
Spread status: {spread_status}
Autoimmune component: {autoimmune_component}
Repigmentation potential: {repigmentation_potential}
Domain: {domain}
Context: {context}

Is there loss of intellectual pigmentation creating patches of colorless understanding? Return ONLY valid JSON."""


class EpistemicVitiligoService:
    """Detects epistemic vitiligo — loss of intellectual pigmentation/meaning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        depigmentation_pattern: str,
        *,
        spread_status: str = "",
        autoimmune_component: str = "",
        repigmentation_potential: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic vitiligo."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VITILIGO_PROMPT.format(
                depigmentation_pattern=depigmentation_pattern,
                spread_status=spread_status or "Not specified",
                autoimmune_component=autoimmune_component or "Not specified",
                repigmentation_potential=repigmentation_potential or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VITILIGO_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "depigmentation_pattern": depigmentation_pattern[:200],
            "vitiligo_detected": data.get("vitiligo_detected", False),
            "severity": data.get("severity", ""),
            "spread_status": data.get("spread_status", ""),
            "autoimmune_component": data.get("autoimmune_component", ""),
            "repigmentation_potential": data.get("repigmentation_potential", ""),
            "recommendation": data.get("recommendation", ""),
        }
