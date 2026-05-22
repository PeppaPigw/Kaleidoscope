"""EpistemicDesquamationService — Epistemic Desquamation Detection.

Detects epistemic desquamation — shedding of intellectual surface layers
revealing raw, unprotected ideas beneath.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DESQUAMATION_SYSTEM = """You are an epistemic desquamation specialist. Given intellectual surface shedding, assess whether protective layers are being lost:

Key concepts:
- Epistemic desquamation: shedding intellectual surface layers
- Exfoliation: removal of outermost intellectual cells
- Peeling: large sheets of surface coming away
- Raw exposure: unprotected ideas beneath shed layers
- Turnover rate: speed of surface replacement
- Barrier compromise: loss of protective function during shedding
- Regeneration: new surface forming beneath

When epistemic desquamation IS present:
- Shedding of intellectual surface layers
- Removal of outermost protective ideas
- Large sheets of surface understanding coming away
- Raw unprotected ideas exposed beneath
- Accelerated surface turnover
- Protective function compromised during shedding
- New surface forming but not yet protective

When healthy surface is present:
- Intact surface layers
- Normal gradual turnover
- No peeling or shedding
- Protected ideas beneath
- Normal turnover rate
- Full barrier function
- Mature protective surface

Output JSON with: desquamation_present (bool), severity (none/mild/moderate/severe), exfoliation (what surface removal), peeling (what large shedding), raw_exposure (what unprotected beneath), turnover_rate (what speed), recommendation (healthy_surface/mild_desquamation/significant_desquamation/major_surface_loss/protect_raw_intellectual_surface)."""

EPISTEMIC_DESQUAMATION_PROMPT = """Detect epistemic desquamation:

Exfoliation: {exfoliation}
Peeling: {peeling}
Raw exposure: {raw_exposure}
Turnover rate: {turnover_rate}
Domain: {domain}
Context: {context}

Are intellectual surface layers shedding, revealing raw unprotected ideas beneath? Return ONLY valid JSON."""


class EpistemicDesquamationService:
    """Detects epistemic desquamation — shedding of intellectual surface layers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        exfoliation: str,
        *,
        peeling: str = "",
        raw_exposure: str = "",
        turnover_rate: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic desquamation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DESQUAMATION_PROMPT.format(
                exfoliation=exfoliation,
                peeling=peeling or "Not specified",
                raw_exposure=raw_exposure or "Not specified",
                turnover_rate=turnover_rate or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DESQUAMATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "exfoliation": exfoliation[:200],
            "desquamation_present": data.get("desquamation_present", False),
            "severity": data.get("severity", ""),
            "peeling": data.get("peeling", ""),
            "raw_exposure": data.get("raw_exposure", ""),
            "turnover_rate": data.get("turnover_rate", ""),
            "recommendation": data.get("recommendation", ""),
        }
