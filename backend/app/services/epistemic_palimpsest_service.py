"""EpistemicPalimpsestService — Epistemic Palimpsest Detection.

Detects epistemic palimpsests — new beliefs written over old ones
where traces of the original still influence thinking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PALIMPSEST_SYSTEM = """You are an epistemic palimpsest specialist. Given a belief layering pattern, assess whether old beliefs still influence through new ones:

Key concepts:
- Epistemic palimpsest: old beliefs showing through new ones
- Overwriting: new beliefs written over old
- Trace influence: traces of old beliefs still influencing
- Incomplete erasure: old beliefs not fully erased
- Layer bleeding: old layers bleeding through new
- Ghost text: ghost of old beliefs visible in new
- Substrate influence: old substrate influencing new content

When epistemic palimpsest IS present:
- Old beliefs showing through new ones
- New beliefs written over incompletely erased old ones
- Traces of old beliefs still influencing thinking
- Old beliefs not fully erased before new ones written
- Old layers bleeding through into new thinking
- Ghost of old beliefs visible in new reasoning
- Old substrate influencing new content

When clean slate is present:
- New beliefs formed independently
- Old beliefs fully processed before new ones
- No traces of old beliefs influencing inappropriately
- Clean transition between belief systems
- No bleeding between layers
- No ghost influences from old beliefs
- New content independent of old substrate

Output JSON with: palimpsest_present (bool), severity (none/mild/moderate/severe), new_belief (what new belief is written), old_belief (what old belief shows through), trace (what trace influence exists), interference (how old interferes with new), recommendation (clean_slate/mild_trace/significant_palimpsest/major_layer_bleeding/fully_process_old_beliefs)."""

EPISTEMIC_PALIMPSEST_PROMPT = """Detect epistemic palimpsest:

New belief: {new_belief}
Old belief: {old_belief}
Trace: {trace}
Interference: {interference}
Domain: {domain}
Context: {context}

Are old beliefs still influencing thinking through traces in new beliefs? Return ONLY valid JSON."""


class EpistemicPalimpsestService:
    """Detects epistemic palimpsests — old beliefs showing through new ones."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        new_belief: str,
        *,
        old_belief: str = "",
        trace: str = "",
        interference: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic palimpsest."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PALIMPSEST_PROMPT.format(
                new_belief=new_belief,
                old_belief=old_belief or "Not specified",
                trace=trace or "Not specified",
                interference=interference or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PALIMPSEST_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "new_belief": new_belief[:200],
            "palimpsest_present": data.get("palimpsest_present", False),
            "severity": data.get("severity", ""),
            "old_belief": data.get("old_belief", ""),
            "trace": data.get("trace", ""),
            "interference": data.get("interference", ""),
            "recommendation": data.get("recommendation", ""),
        }
