"""EpistemicMiddenService — Epistemic Midden Detection.

Detects epistemic middens — accumulated intellectual refuse heaps
that reveal patterns of intellectual activity over time.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MIDDEN_SYSTEM = """You are an epistemic midden specialist. Given an intellectual refuse pattern, assess whether accumulated waste reveals activity patterns:

Key concepts:
- Epistemic midden: accumulated intellectual refuse heap
- Accumulation: waste building up over time
- Activity pattern: what the refuse reveals about intellectual habits
- Seasonal variation: changes in intellectual activity over time
- Discard pattern: what is thrown away and why
- Resource use: what intellectual resources were consumed
- Site formation: how the midden formed and grew

When epistemic midden IS present:
- Accumulated intellectual refuse revealing patterns
- Waste building up over time in identifiable heaps
- Refuse revealing intellectual habits and activities
- Changes in intellectual activity visible over time
- Clear patterns in what is discarded and why
- Evidence of what intellectual resources were consumed
- Clear formation process of the refuse heap

When clean intellectual space is present:
- No accumulated intellectual refuse
- No waste building up over time
- No refuse to analyze for patterns
- No temporal variation visible
- No discard patterns
- No evidence of past resource consumption
- No formation of refuse heaps

Output JSON with: midden_present (bool), severity (none/mild/moderate/severe), refuse (what intellectual refuse accumulates), pattern (what activity pattern it reveals), seasonal (what temporal variation exists), discard (what is thrown away and why), recommendation (clean_space/mild_accumulation/significant_midden/major_refuse_heap/analyze_midden_for_patterns)."""

EPISTEMIC_MIDDEN_PROMPT = """Detect epistemic midden:

Refuse: {refuse}
Pattern: {pattern}
Seasonal: {seasonal}
Discard: {discard}
Domain: {domain}
Context: {context}

Does accumulated intellectual refuse reveal patterns of intellectual activity over time? Return ONLY valid JSON."""


class EpistemicMiddenService:
    """Detects epistemic middens — refuse heaps revealing intellectual activity patterns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        refuse: str,
        *,
        pattern: str = "",
        seasonal: str = "",
        discard: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic midden."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MIDDEN_PROMPT.format(
                refuse=refuse,
                pattern=pattern or "Not specified",
                seasonal=seasonal or "Not specified",
                discard=discard or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MIDDEN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "refuse": refuse[:200],
            "midden_present": data.get("midden_present", False),
            "severity": data.get("severity", ""),
            "pattern": data.get("pattern", ""),
            "seasonal": data.get("seasonal", ""),
            "discard": data.get("discard", ""),
            "recommendation": data.get("recommendation", ""),
        }
