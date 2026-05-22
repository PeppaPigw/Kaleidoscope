"""EpistemicIntermittencyService — Epistemic Intermittency Detection.

Detects epistemic intermittency — intellectual systems alternating
between regular and chaotic behavior unpredictably.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTERMITTENCY_SYSTEM = """You are an epistemic intermittency specialist. Given an intellectual pattern, assess whether it alternates between regular and chaotic behavior:

Key concepts:
- Epistemic intermittency: alternating regular and chaotic behavior
- Laminar phase: period of regular predictable behavior
- Burst: sudden eruption of chaotic behavior
- Type I: saddle-node intermittency
- Type II: subcritical Hopf intermittency
- Type III: inverse period-doubling intermittency
- Reinjection: mechanism returning from chaos to order

When epistemic intermittency IS present:
- Alternating between regular and chaotic reasoning
- Periods of predictable intellectual behavior
- Sudden eruptions of chaotic thinking
- Transitions triggered by approaching thresholds
- Transitions triggered by oscillation instability
- Transitions triggered by period-doubling reversal
- Mechanism returning from chaos to ordered thinking

When consistent behavior is present:
- Uniformly regular or uniformly chaotic
- No alternation between modes
- No sudden eruptions
- No threshold-triggered transitions
- No oscillation instability
- No period-doubling effects
- No reinjection mechanism

Output JSON with: intermittency_present (bool), severity (none/mild/moderate/severe), laminar (what regular periods), burst (what chaotic eruptions), type (what transition mechanism), reinjection (what returns to order), recommendation (consistent_behavior/mild_intermittency/significant_intermittency/major_alternation/stabilize_laminar_phase)."""

EPISTEMIC_INTERMITTENCY_PROMPT = """Detect epistemic intermittency:

Laminar: {laminar}
Burst: {burst}
Type: {intermittency_type}
Reinjection: {reinjection}
Domain: {domain}
Context: {context}

Does this intellectual system alternate between regular and chaotic behavior unpredictably? Return ONLY valid JSON."""


class EpistemicIntermittencyService:
    """Detects epistemic intermittency — alternating regular and chaotic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        laminar: str,
        *,
        burst: str = "",
        intermittency_type: str = "",
        reinjection: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intermittency."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTERMITTENCY_PROMPT.format(
                laminar=laminar,
                burst=burst or "Not specified",
                intermittency_type=intermittency_type or "Not specified",
                reinjection=reinjection or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTERMITTENCY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "laminar": laminar[:200],
            "intermittency_present": data.get("intermittency_present", False),
            "severity": data.get("severity", ""),
            "burst": data.get("burst", ""),
            "type": data.get("type", ""),
            "reinjection": data.get("reinjection", ""),
            "recommendation": data.get("recommendation", ""),
        }
