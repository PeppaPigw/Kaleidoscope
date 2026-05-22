"""EpistemicCartilageDegenerationService — Epistemic Cartilage Degeneration Detection.

Detects epistemic cartilage degeneration — loss of cushioning between
intellectual structures causing friction and wear.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CARTILAGE_DEGENERATION_SYSTEM = """You are an epistemic cartilage degeneration specialist. Given intellectual cushioning, assess whether degeneration is causing friction:

Key concepts:
- Epistemic cartilage degeneration: loss of cushioning between structures
- Articular surface erosion: smooth interface wearing away
- Bone-on-bone contact: structures grinding without cushion
- Osteophyte formation: compensatory growths at margins
- Synovial inflammation: lubricating system inflamed
- Crepitus: grinding sensation during movement
- Joint space narrowing: measurable loss of cushion thickness

When epistemic cartilage degeneration IS present:
- Loss of cushioning between intellectual structures
- Smooth interfaces wearing away
- Structures grinding against each other without cushion
- Compensatory growths forming at margins
- Lubricating systems becoming inflamed
- Grinding sensation during intellectual movement
- Measurable loss of cushion thickness

When healthy cartilage is present:
- Adequate cushioning between structures
- Smooth intact interfaces
- No grinding contact
- No compensatory growths
- Healthy lubrication
- Smooth movement
- Full cushion thickness

Output JSON with: cartilage_degeneration_present (bool), severity (none/mild/moderate/severe), surface_erosion (what interface wearing), bone_on_bone (what grinding contact), osteophyte (what compensatory growth), crepitus (what grinding sensation), recommendation (healthy_cartilage/mild_degeneration/significant_cartilage_degeneration/major_cushion_loss/restore_intellectual_cushioning)."""

EPISTEMIC_CARTILAGE_DEGENERATION_PROMPT = """Detect epistemic cartilage degeneration:

Surface erosion: {surface_erosion}
Bone-on-bone: {bone_on_bone}
Osteophyte: {osteophyte}
Crepitus: {crepitus}
Domain: {domain}
Context: {context}

Is cushioning between intellectual structures degenerating, causing friction and wear? Return ONLY valid JSON."""


class EpistemicCartilageDegenerationService:
    """Detects epistemic cartilage degeneration — loss of intellectual cushioning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        surface_erosion: str,
        *,
        bone_on_bone: str = "",
        osteophyte: str = "",
        crepitus: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cartilage degeneration."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CARTILAGE_DEGENERATION_PROMPT.format(
                surface_erosion=surface_erosion,
                bone_on_bone=bone_on_bone or "Not specified",
                osteophyte=osteophyte or "Not specified",
                crepitus=crepitus or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CARTILAGE_DEGENERATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "surface_erosion": surface_erosion[:200],
            "cartilage_degeneration_present": data.get("cartilage_degeneration_present", False),
            "severity": data.get("severity", ""),
            "bone_on_bone": data.get("bone_on_bone", ""),
            "osteophyte": data.get("osteophyte", ""),
            "crepitus": data.get("crepitus", ""),
            "recommendation": data.get("recommendation", ""),
        }
