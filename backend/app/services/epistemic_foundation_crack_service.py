"""EpistemicFoundationCrackService — Epistemic Foundation Crack Detection.

Detects epistemic foundation cracks — cracks in foundational
assumptions threatening entire knowledge structure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FOUNDATION_CRACK_SYSTEM = """You are an epistemic foundation crack specialist. Given a knowledge structure, assess whether cracks in foundational assumptions threaten the whole:

Key concepts:
- Epistemic foundation crack: cracks in foundational assumptions
- Structural threat: threat to entire knowledge structure
- Foundation weakness: weakness at foundational level
- Propagation risk: cracks propagating upward
- Hidden damage: damage not visible at surface
- Stress concentration: stress concentrated at crack points
- Catastrophic failure risk: risk of sudden total failure

When epistemic foundation crack IS present:
- Cracks in foundational assumptions visible
- Entire knowledge structure threatened
- Weakness at foundational level detected
- Cracks propagating upward through structure
- Damage not visible at surface level
- Stress concentrated at crack points
- Risk of sudden catastrophic failure

When solid foundation is present:
- Foundational assumptions intact and tested
- Knowledge structure well-supported
- Foundation strong and maintained
- No propagation of weakness
- Foundation visible and inspectable
- Stress distributed appropriately
- No risk of sudden failure

Output JSON with: foundation_crack_present (bool), severity (none/mild/moderate/severe), structure (what structure is affected), crack (what crack exists), propagation (how crack propagates), threat (what is threatened), recommendation (solid_foundation/mild_weakness/significant_crack/major_structural_threat/repair_foundation)."""

EPISTEMIC_FOUNDATION_CRACK_PROMPT = """Detect epistemic foundation crack:

Structure: {structure}
Crack: {crack}
Propagation: {propagation}
Threat: {threat}
Domain: {domain}
Context: {context}

Are cracks in foundational assumptions threatening the knowledge structure? Return ONLY valid JSON."""


class EpistemicFoundationCrackService:
    """Detects epistemic foundation cracks — cracks threatening knowledge structures."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        structure: str,
        *,
        crack: str = "",
        propagation: str = "",
        threat: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic foundation crack."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FOUNDATION_CRACK_PROMPT.format(
                structure=structure,
                crack=crack or "Not specified",
                propagation=propagation or "Not specified",
                threat=threat or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FOUNDATION_CRACK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "structure": structure[:200],
            "foundation_crack_present": data.get("foundation_crack_present", False),
            "severity": data.get("severity", ""),
            "crack": data.get("crack", ""),
            "propagation": data.get("propagation", ""),
            "threat": data.get("threat", ""),
            "recommendation": data.get("recommendation", ""),
        }
