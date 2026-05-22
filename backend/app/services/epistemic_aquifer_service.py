"""EpistemicAquiferService — Epistemic Aquifer Detection.

Detects epistemic aquifers — hidden reservoirs of knowledge that
are being depleted without replenishment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AQUIFER_SYSTEM = """You are an epistemic aquifer specialist. Given a knowledge reservoir pattern, assess whether hidden knowledge reserves are being depleted:

Key concepts:
- Epistemic aquifer: hidden knowledge reservoir being depleted
- Hidden reserve: knowledge reserve not visible on surface
- Depletion: drawing down without replenishment
- Unsustainable extraction: extracting faster than replenishment
- Invisible decline: decline not visible until too late
- Replenishment failure: failure to replenish reserves
- Collapse risk: risk of sudden collapse when depleted

When epistemic aquifer depletion IS present:
- Hidden knowledge reserves being depleted
- Knowledge reserve not visible but declining
- Drawing down knowledge without replenishment
- Extracting knowledge faster than it can be replenished
- Decline not visible until reserves are exhausted
- Failure to replenish knowledge reserves
- Risk of sudden collapse when reserves run out

When sustainable reserves are present:
- Knowledge reserves maintained at healthy levels
- Reserves visible and monitored
- Extraction balanced with replenishment
- Sustainable rate of knowledge use
- Reserve levels visible and tracked
- Active replenishment of reserves
- No risk of sudden depletion

Output JSON with: aquifer_depletion_present (bool), severity (none/mild/moderate/severe), reserve (what reserve is depleted), extraction (how it is extracted), replenishment (what replenishment fails), collapse_risk (risk of collapse), recommendation (sustainable_reserves/mild_depletion/significant_aquifer_decline/major_unsustainable_extraction/replenish_reserves)."""

EPISTEMIC_AQUIFER_PROMPT = """Detect epistemic aquifer depletion:

Reserve: {reserve}
Extraction: {extraction}
Replenishment: {replenishment}
Collapse risk: {collapse_risk}
Domain: {domain}
Context: {context}

Are hidden knowledge reserves being depleted without replenishment? Return ONLY valid JSON."""


class EpistemicAquiferService:
    """Detects epistemic aquifer depletion — hidden reserves being depleted."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reserve: str,
        *,
        extraction: str = "",
        replenishment: str = "",
        collapse_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic aquifer depletion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AQUIFER_PROMPT.format(
                reserve=reserve,
                extraction=extraction or "Not specified",
                replenishment=replenishment or "Not specified",
                collapse_risk=collapse_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AQUIFER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reserve": reserve[:200],
            "aquifer_depletion_present": data.get("aquifer_depletion_present", False),
            "severity": data.get("severity", ""),
            "extraction": data.get("extraction", ""),
            "replenishment": data.get("replenishment", ""),
            "collapse_risk": data.get("collapse_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
