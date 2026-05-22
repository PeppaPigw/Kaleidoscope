"""EpistemicNoveltyAddictionService — Epistemic Novelty Addiction Detection.

Detects epistemic novelty addiction — compulsive need for new ideas and
information, unable to deepen existing knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NOVELTY_ADDICTION_SYSTEM = """You are an epistemic novelty addiction specialist. Given compulsive need for new ideas, assess addiction:

Key concepts:
- Epistemic novelty addiction: compulsive need for new information
- Dopamine seeking: chasing the hit of new discovery
- Depth avoidance: unable to stay with and deepen
- Boredom intolerance: existing knowledge feels stale instantly
- Consumption compulsion: must always be taking in new
- Integration failure: new never becomes deep knowledge
- Withdrawal: anxiety when no new input available

When epistemic novelty addiction IS present:
- Compulsive need for new
- Chasing discovery hit
- Unable to deepen
- Existing feels stale
- Must always take in new
- New never becomes deep
- Anxiety without input

When no novelty addiction:
- Comfortable with familiar
- Satisfied by understanding
- Able to deepen
- Existing feels rich
- Balanced intake
- Integration happening
- Calm without new input

Output JSON with: novelty_addiction_detected (bool), severity (none/mild/moderate/severe), dopamine_seeking (what chasing), depth_avoidance (what not deepening), boredom_intolerance (what feels stale), integration_failure (what not integrating), recommendation (no_novelty_addiction/mild_depth_practice/significant_consumption_reduction/major_intensive_addiction_work/emergency_severe_compulsion)."""

EPISTEMIC_NOVELTY_ADDICTION_PROMPT = """Detect epistemic novelty addiction:

Dopamine seeking: {dopamine_seeking}
Depth avoidance: {depth_avoidance}
Boredom intolerance: {boredom_intolerance}
Integration failure: {integration_failure}
Domain: {domain}
Context: {context}

Is there compulsive need for new ideas unable to deepen existing knowledge? Return ONLY valid JSON."""


class EpistemicNoveltyAddictionService:
    """Detects epistemic novelty addiction — compulsive need for new information."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        dopamine_seeking: str,
        *,
        depth_avoidance: str = "",
        boredom_intolerance: str = "",
        integration_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic novelty addiction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NOVELTY_ADDICTION_PROMPT.format(
                dopamine_seeking=dopamine_seeking,
                depth_avoidance=depth_avoidance or "Not specified",
                boredom_intolerance=boredom_intolerance or "Not specified",
                integration_failure=integration_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NOVELTY_ADDICTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "dopamine_seeking": dopamine_seeking[:200],
            "novelty_addiction_detected": data.get("novelty_addiction_detected", False),
            "severity": data.get("severity", ""),
            "depth_avoidance": data.get("depth_avoidance", ""),
            "boredom_intolerance": data.get("boredom_intolerance", ""),
            "integration_failure": data.get("integration_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
