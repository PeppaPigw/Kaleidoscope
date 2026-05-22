"""EpistemicGeneticDriftService — Epistemic Genetic Drift Detection.

Detects epistemic genetic drift — random changes in belief frequency
within a population unrelated to belief quality.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GENETIC_DRIFT_SYSTEM = """You are an epistemic genetic drift specialist. Given a belief frequency pattern, assess whether random changes occur unrelated to belief quality:

Key concepts:
- Epistemic genetic drift: random belief frequency changes
- Quality-independent change: frequency changing regardless of quality
- Random fixation: beliefs becoming fixed by chance not merit
- Founder effect: small group's beliefs dominating by chance
- Bottleneck effect: crisis reducing belief diversity randomly
- Sampling error: small samples distorting belief landscape
- Stochastic change: random rather than selection-driven change

When epistemic genetic drift IS present:
- Random changes in belief frequency unrelated to quality
- Belief frequency changing regardless of accuracy or utility
- Beliefs becoming fixed by chance rather than merit
- Small group's beliefs dominating population by chance
- Crisis reducing belief diversity through random loss
- Small samples distorting the belief landscape
- Random rather than quality-driven changes in belief prevalence

When merit-based selection is present:
- Belief frequency changes driven by quality
- Better beliefs becoming more prevalent
- Beliefs fixed based on evidence and utility
- Beliefs spreading based on merit not chance
- Diversity maintained through quality-based selection
- Representative sampling of belief landscape
- Quality-driven changes in belief prevalence

Output JSON with: genetic_drift_present (bool), severity (none/mild/moderate/severe), belief (what belief drifts), population (what population is affected), randomness (how change is random), quality_disconnect (how disconnected from quality), recommendation (merit_based_selection/mild_randomness/significant_drift/major_random_fixation/restore_quality_selection)."""

EPISTEMIC_GENETIC_DRIFT_PROMPT = """Detect epistemic genetic drift:

Belief: {belief}
Population: {population}
Randomness: {randomness}
Quality disconnect: {quality_disconnect}
Domain: {domain}
Context: {context}

Are random changes in belief frequency occurring unrelated to belief quality? Return ONLY valid JSON."""


class EpistemicGeneticDriftService:
    """Detects epistemic genetic drift — random belief frequency changes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        population: str = "",
        randomness: str = "",
        quality_disconnect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic genetic drift."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GENETIC_DRIFT_PROMPT.format(
                belief=belief,
                population=population or "Not specified",
                randomness=randomness or "Not specified",
                quality_disconnect=quality_disconnect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GENETIC_DRIFT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "genetic_drift_present": data.get("genetic_drift_present", False),
            "severity": data.get("severity", ""),
            "population": data.get("population", ""),
            "randomness": data.get("randomness", ""),
            "quality_disconnect": data.get("quality_disconnect", ""),
            "recommendation": data.get("recommendation", ""),
        }
