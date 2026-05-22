"""EpistemicKarstService — Epistemic Karst Detection.

Detects epistemic karst — knowledge foundations being dissolved from
within, creating hidden cavities that cause sudden collapses.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_KARST_SYSTEM = """You are an epistemic karst specialist. Given a knowledge foundation pattern, assess whether hidden dissolution is creating collapse risks:

Key concepts:
- Epistemic karst: knowledge foundations dissolving from within
- Hidden cavities: unseen voids in knowledge structure
- Dissolution: gradual dissolving of foundational assumptions
- Sinkhole: sudden collapse when cavity becomes too large
- Underground river: hidden flows eroding foundations
- Surface stability illusion: surface appearing stable while hollow beneath
- Speleogenesis: process of cavity formation in knowledge

When epistemic karst IS present:
- Knowledge foundations being dissolved from within
- Hidden voids forming in knowledge structure
- Foundational assumptions gradually dissolving
- Risk of sudden collapse when cavities grow too large
- Hidden intellectual flows eroding foundations
- Surface appearing stable while hollow beneath
- Active cavity formation in knowledge base

When solid foundations are present:
- Knowledge foundations remaining solid throughout
- No hidden voids in knowledge structure
- Foundational assumptions remaining intact
- No risk of sudden collapse
- No hidden erosion of foundations
- Surface stability reflecting actual structural integrity
- No cavity formation in knowledge base

Output JSON with: karst_present (bool), severity (none/mild/moderate/severe), foundations (what foundations dissolve), cavities (what hidden voids form), dissolution (what dissolves them), sinkhole_risk (risk of sudden collapse), recommendation (solid_foundations/mild_dissolution/significant_karst/major_sinkhole_risk/shore_up_foundations)."""

EPISTEMIC_KARST_PROMPT = """Detect epistemic karst:

Foundations: {foundations}
Cavities: {cavities}
Dissolution: {dissolution}
Sinkhole risk: {sinkhole_risk}
Domain: {domain}
Context: {context}

Are knowledge foundations being dissolved from within creating hidden collapse risks? Return ONLY valid JSON."""


class EpistemicKarstService:
    """Detects epistemic karst — hidden dissolution of knowledge foundations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        foundations: str,
        *,
        cavities: str = "",
        dissolution: str = "",
        sinkhole_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic karst."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_KARST_PROMPT.format(
                foundations=foundations,
                cavities=cavities or "Not specified",
                dissolution=dissolution or "Not specified",
                sinkhole_risk=sinkhole_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_KARST_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "foundations": foundations[:200],
            "karst_present": data.get("karst_present", False),
            "severity": data.get("severity", ""),
            "cavities": data.get("cavities", ""),
            "dissolution": data.get("dissolution", ""),
            "sinkhole_risk": data.get("sinkhole_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
