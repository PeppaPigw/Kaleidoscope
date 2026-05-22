"""EpistemicScarTissueService — Epistemic Scar Tissue Detection.

Detects epistemic scar tissue — rigid protective formations from past
intellectual wounds that limit flexibility and function.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCAR_TISSUE_SYSTEM = """You are an epistemic scar tissue specialist. Given intellectual wound healing, assess whether rigid formations limit function:

Key concepts:
- Epistemic scar tissue: rigid formations from past intellectual wounds
- Keloid: excessive scar growth beyond original wound
- Contracture: scar pulling surrounding tissue tight
- Adhesion: scar binding structures that should move freely
- Remodeling: gradual softening of scar over time
- Hypertrophic: raised scar within wound boundaries
- Functional limitation: scar restricting normal movement

When epistemic scar tissue IS present:
- Rigid protective formations from past wounds
- Excessive growth beyond original intellectual injury
- Scar pulling surrounding ideas tight
- Scar binding structures that should move freely
- Gradual softening possible over time
- Raised rigid areas within wound boundaries
- Scar restricting normal intellectual movement

When healthy healing is present:
- Flexible healed tissue
- No excessive growth
- No contracture
- No adhesions
- Normal remodeling
- Flat smooth healing
- Full functional movement

Output JSON with: scar_tissue_present (bool), severity (none/mild/moderate/severe), keloid (what excessive growth), contracture (what tightening), adhesion (what binding), functional_limitation (what movement restriction), recommendation (healthy_healing/mild_scarring/significant_scar_tissue/major_rigid_formation/soften_intellectual_scars)."""

EPISTEMIC_SCAR_TISSUE_PROMPT = """Detect epistemic scar tissue:

Keloid: {keloid}
Contracture: {contracture}
Adhesion: {adhesion}
Functional limitation: {functional_limitation}
Domain: {domain}
Context: {context}

Are rigid protective formations from past intellectual wounds limiting flexibility? Return ONLY valid JSON."""


class EpistemicScarTissueService:
    """Detects epistemic scar tissue — rigid formations limiting flexibility."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        keloid: str,
        *,
        contracture: str = "",
        adhesion: str = "",
        functional_limitation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic scar tissue."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCAR_TISSUE_PROMPT.format(
                keloid=keloid,
                contracture=contracture or "Not specified",
                adhesion=adhesion or "Not specified",
                functional_limitation=functional_limitation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCAR_TISSUE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "keloid": keloid[:200],
            "scar_tissue_present": data.get("scar_tissue_present", False),
            "severity": data.get("severity", ""),
            "contracture": data.get("contracture", ""),
            "adhesion": data.get("adhesion", ""),
            "functional_limitation": data.get("functional_limitation", ""),
            "recommendation": data.get("recommendation", ""),
        }
