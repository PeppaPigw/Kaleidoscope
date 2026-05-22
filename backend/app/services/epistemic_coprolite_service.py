"""EpistemicCoproliteService — Epistemic Coprolite Detection.

Detects epistemic coprolites — fossilized intellectual waste that
reveals what ideas were consumed and processed in the past.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COPROLITE_SYSTEM = """You are an epistemic coprolite specialist. Given intellectual remains, assess whether fossilized waste reveals past intellectual consumption:

Key concepts:
- Epistemic coprolite: fossilized intellectual waste
- Consumption evidence: what ideas were consumed in the past
- Processing: how ideas were digested and processed
- Diet reconstruction: understanding past intellectual diet
- Trace fossil: evidence of intellectual activity, not the ideas themselves
- Undigested fragments: ideas that passed through without being processed
- Paleodiet: reconstructing what intellectual nourishment was available

When epistemic coprolite IS present:
- Fossilized intellectual waste revealing past consumption
- Evidence of what ideas were consumed historically
- Signs of how ideas were digested and processed
- Ability to reconstruct past intellectual diet
- Evidence of intellectual activity rather than ideas themselves
- Undigested fragments of ideas that weren't fully processed
- Reconstruction of what intellectual nourishment was available

When fresh intellectual activity is present:
- Current intellectual activity, not fossilized remains
- Direct observation of idea consumption
- Active processing visible in real time
- Current intellectual diet observable
- Direct evidence of ideas themselves
- Ideas being fully processed currently
- Current intellectual nourishment available

Output JSON with: coprolite_present (bool), severity (none/mild/moderate/severe), waste (what fossilized waste exists), consumption (what past consumption it reveals), undigested (what fragments weren't processed), diet (what intellectual diet is reconstructed), recommendation (fresh_activity/mild_remains/significant_coprolite/major_fossil_record/analyze_waste_for_insight)."""

EPISTEMIC_COPROLITE_PROMPT = """Detect epistemic coprolite:

Waste: {waste}
Consumption: {consumption}
Undigested: {undigested}
Diet: {diet}
Domain: {domain}
Context: {context}

Does fossilized intellectual waste reveal what ideas were consumed and processed in the past? Return ONLY valid JSON."""


class EpistemicCoproliteService:
    """Detects epistemic coprolites — fossilized waste revealing past intellectual consumption."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        waste: str,
        *,
        consumption: str = "",
        undigested: str = "",
        diet: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic coprolite."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COPROLITE_PROMPT.format(
                waste=waste,
                consumption=consumption or "Not specified",
                undigested=undigested or "Not specified",
                diet=diet or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COPROLITE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "waste": waste[:200],
            "coprolite_present": data.get("coprolite_present", False),
            "severity": data.get("severity", ""),
            "consumption": data.get("consumption", ""),
            "undigested": data.get("undigested", ""),
            "diet": data.get("diet", ""),
            "recommendation": data.get("recommendation", ""),
        }
