"""EpistemicDecompositionStageService — Epistemic Decomposition Stage Detection.

Detects epistemic decomposition stage — assessing how far intellectual decay
has progressed since the system ceased functioning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DECOMPOSITION_STAGE_SYSTEM = """You are an epistemic decomposition stage specialist. Given intellectual decay patterns, assess how far decomposition has progressed:

Key concepts:
- Epistemic decomposition stage: how far intellectual decay has progressed
- Fresh stage: recently ceased, minimal visible change
- Bloat stage: internal gases expanding structure
- Active decay: rapid breakdown of intellectual substance
- Advanced decay: most substance consumed
- Dry/skeletal: only framework remains
- Mummification: preserved in dried state
- Saponification: converted to waxy substance

When epistemic decomposition IS staged:
- Clear progression of intellectual decay
- Recently ceased with minimal change (fresh)
- Internal expansion from decay products (bloat)
- Rapid breakdown of substance (active decay)
- Most substance consumed (advanced)
- Only framework remaining (dry/skeletal)
- Preserved in altered state (mummification)

When no decomposition:
- System still alive
- No decay present
- No staging possible
- Full substance intact
- Complete framework with tissue
- No preservation needed
- Normal living state

Output JSON with: decomposition_staged (bool), severity (none/mild/moderate/severe), current_stage (what stage reached), decay_rate (what speed of progression), preservation (what altered state), remaining_framework (what still intact), recommendation (no_decomposition/mild_decay/significant_decomposition/major_advanced_decay/document_intellectual_decomposition_stage)."""

EPISTEMIC_DECOMPOSITION_STAGE_PROMPT = """Detect epistemic decomposition stage:

Current stage: {current_stage}
Decay rate: {decay_rate}
Preservation: {preservation}
Remaining framework: {remaining_framework}
Domain: {domain}
Context: {context}

How far has intellectual decay progressed since the system ceased functioning? Return ONLY valid JSON."""


class EpistemicDecompositionStageService:
    """Detects epistemic decomposition stage — how far intellectual decay has progressed."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        current_stage: str,
        *,
        decay_rate: str = "",
        preservation: str = "",
        remaining_framework: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic decomposition stage."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DECOMPOSITION_STAGE_PROMPT.format(
                current_stage=current_stage,
                decay_rate=decay_rate or "Not specified",
                preservation=preservation or "Not specified",
                remaining_framework=remaining_framework or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DECOMPOSITION_STAGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "current_stage": current_stage[:200],
            "decomposition_staged": data.get("decomposition_staged", False),
            "severity": data.get("severity", ""),
            "decay_rate": data.get("decay_rate", ""),
            "preservation": data.get("preservation", ""),
            "remaining_framework": data.get("remaining_framework", ""),
            "recommendation": data.get("recommendation", ""),
        }
