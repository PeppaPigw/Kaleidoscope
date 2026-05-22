"""EpistemicStagnationService — Epistemic Stagnation Detection.

Detects epistemic stagnation — knowledge pools that have stopped
flowing and are becoming stale or toxic.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STAGNATION_SYSTEM = """You are an epistemic stagnation specialist. Given a knowledge pool, assess whether it has stopped flowing and is becoming stale:

Key concepts:
- Epistemic stagnation: knowledge pool stopped flowing
- Staleness: knowledge becoming stale from lack of flow
- Toxicity buildup: toxic ideas accumulating in stagnant pool
- Circulation failure: failure of knowledge circulation
- Freshness loss: loss of fresh input
- Decay accumulation: decay products accumulating
- Oxygen depletion: intellectual vitality depleting

When epistemic stagnation IS present:
- Knowledge pool has stopped flowing
- Knowledge becoming stale from lack of circulation
- Toxic ideas accumulating in stagnant pool
- Knowledge circulation has failed
- No fresh input entering the pool
- Decay products accumulating
- Intellectual vitality depleting

When healthy flow is present:
- Knowledge flowing and circulating
- Knowledge fresh and regularly updated
- No toxic accumulation
- Healthy circulation maintained
- Fresh input regularly entering
- Decay products flushed out
- Intellectual vitality maintained

Output JSON with: stagnation_present (bool), severity (none/mild/moderate/severe), pool (what knowledge pool stagnates), staleness (how stale it has become), toxicity (what toxicity accumulates), circulation (what circulation has failed), recommendation (healthy_flow/mild_slowdown/significant_stagnation/major_toxic_accumulation/restore_circulation)."""

EPISTEMIC_STAGNATION_PROMPT = """Detect epistemic stagnation:

Pool: {pool}
Staleness: {staleness}
Toxicity: {toxicity}
Circulation: {circulation}
Domain: {domain}
Context: {context}

Has this knowledge pool stopped flowing and become stale or toxic? Return ONLY valid JSON."""


class EpistemicStagnationService:
    """Detects epistemic stagnation — knowledge pools becoming stale."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pool: str,
        *,
        staleness: str = "",
        toxicity: str = "",
        circulation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic stagnation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STAGNATION_PROMPT.format(
                pool=pool,
                staleness=staleness or "Not specified",
                toxicity=toxicity or "Not specified",
                circulation=circulation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STAGNATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pool": pool[:200],
            "stagnation_present": data.get("stagnation_present", False),
            "severity": data.get("severity", ""),
            "staleness": data.get("staleness", ""),
            "toxicity": data.get("toxicity", ""),
            "circulation": data.get("circulation", ""),
            "recommendation": data.get("recommendation", ""),
        }
