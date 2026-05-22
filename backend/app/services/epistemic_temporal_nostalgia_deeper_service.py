"""EpistemicTemporalNostalgiaDeeperService — Epistemic Temporal Nostalgia Detection.

Detects epistemic temporal nostalgia — nostalgia distorting assessment
of past epistemic states and making the past seem better than it was.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_NOSTALGIA_DEEPER_SYSTEM = """You are an epistemic temporal nostalgia specialist. Given nostalgia distorting assessment of past, assess temporal nostalgia:

Key concepts:
- Epistemic temporal nostalgia: nostalgia distorting assessment of past epistemic states
- Past idealization: idealizing past knowledge or understanding
- Decline narrative: narrating decline from better past
- Selective past memory: remembering only good from past
- Lost golden age: believing in a lost golden age of knowing
- Deterioration assumption: assuming things have gotten worse
- Romanticized history: romanticizing past epistemic conditions

When epistemic temporal nostalgia IS present:
- Nostalgia distorting past assessment
- Past idealized
- Decline narrated
- Past selectively remembered
- Golden age invoked
- Deterioration assumed
- History romanticized

When no temporal nostalgia:
- Past assessed accurately
- Past seen realistically
- No decline narrative
- Past remembered fully
- No golden age myth
- Change assessed neutrally
- History seen clearly

Output JSON with: temporal_nostalgia_detected (bool), severity (none/mild/moderate/severe), past_idealization (what past idealized), decline_narrative (what decline narrated), selective_past_memory (what selectively remembered), romanticized_history (what history romanticized), recommendation (no_temporal_nostalgia/mild_reality_checking/significant_past_reassessment/major_intensive_temporal_accuracy/emergency_complete_temporal_nostalgia)."""

EPISTEMIC_TEMPORAL_NOSTALGIA_DEEPER_PROMPT = """Detect epistemic temporal nostalgia:

Past idealization: {past_idealization}
Decline narrative: {decline_narrative}
Selective past memory: {selective_past_memory}
Romanticized history: {romanticized_history}
Domain: {domain}
Context: {context}

Is nostalgia distorting assessment of past epistemic states? Return ONLY valid JSON."""


class EpistemicTemporalNostalgiaDeeperService:
    """Detects epistemic temporal nostalgia — nostalgia distorting past assessment."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        past_idealization: str,
        *,
        decline_narrative: str = "",
        selective_past_memory: str = "",
        romanticized_history: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal nostalgia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_NOSTALGIA_DEEPER_PROMPT.format(
                past_idealization=past_idealization,
                decline_narrative=decline_narrative or "Not specified",
                selective_past_memory=selective_past_memory or "Not specified",
                romanticized_history=romanticized_history or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_NOSTALGIA_DEEPER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "past_idealization": past_idealization[:200],
            "temporal_nostalgia_detected": data.get("temporal_nostalgia_detected", False),
            "severity": data.get("severity", ""),
            "decline_narrative": data.get("decline_narrative", ""),
            "selective_past_memory": data.get("selective_past_memory", ""),
            "romanticized_history": data.get("romanticized_history", ""),
            "recommendation": data.get("recommendation", ""),
        }
