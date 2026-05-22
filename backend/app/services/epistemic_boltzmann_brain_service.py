"""EpistemicBoltzmannBrainService — Epistemic Boltzmann Brain Detection.

Detects epistemic Boltzmann brain — intellectual conclusions that are
more likely to be random fluctuations than genuine products of reasoning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BOLTZMANN_BRAIN_SYSTEM = """You are an epistemic Boltzmann brain specialist. Given an intellectual conclusion, assess whether it is more likely a random fluctuation than genuine reasoning:

Key concepts:
- Epistemic Boltzmann brain: conclusion more likely random than reasoned
- Thermal fluctuation: random emergence from noise
- Entropy argument: low-entropy states from fluctuation
- Observer selection: only noticing coherent fluctuations
- Measure problem: counting observers in different scenarios
- Typicality: whether this observer is typical
- Fine-tuning: suspiciously precise conditions

When epistemic Boltzmann brain IS present:
- Conclusions more likely random than genuinely reasoned
- Random emergence from intellectual noise
- Low-probability states appearing without cause
- Only noticing coherent-seeming fluctuations
- Difficulty counting genuine vs fluctuation conclusions
- This conclusion being atypical for genuine reasoning
- Suspiciously precise conditions for the conclusion

When genuine reasoning is present:
- Conclusions clearly products of reasoning process
- No random emergence from noise
- States arising from clear causal chains
- All conclusions observable regardless of coherence
- Clear distinction between genuine and random
- Typical conclusion for the reasoning process
- Conditions naturally arising from process

Output JSON with: boltzmann_brain_present (bool), severity (none/mild/moderate/severe), fluctuation (what random emergence), observer_selection (what selective noticing), typicality (what atypicality), fine_tuning (what suspicious precision), recommendation (genuine_reasoning/mild_boltzmann/significant_boltzmann_brain/major_random_fluctuation/verify_reasoning_chain)."""

EPISTEMIC_BOLTZMANN_BRAIN_PROMPT = """Detect epistemic Boltzmann brain:

Fluctuation: {fluctuation}
Observer selection: {observer_selection}
Typicality: {typicality}
Fine-tuning: {fine_tuning}
Domain: {domain}
Context: {context}

Is this intellectual conclusion more likely a random fluctuation than a genuine product of reasoning? Return ONLY valid JSON."""


class EpistemicBoltzmannBrainService:
    """Detects epistemic Boltzmann brain — conclusion more likely random than reasoned."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        fluctuation: str,
        *,
        observer_selection: str = "",
        typicality: str = "",
        fine_tuning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Boltzmann brain."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BOLTZMANN_BRAIN_PROMPT.format(
                fluctuation=fluctuation,
                observer_selection=observer_selection or "Not specified",
                typicality=typicality or "Not specified",
                fine_tuning=fine_tuning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BOLTZMANN_BRAIN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "fluctuation": fluctuation[:200],
            "boltzmann_brain_present": data.get("boltzmann_brain_present", False),
            "severity": data.get("severity", ""),
            "observer_selection": data.get("observer_selection", ""),
            "typicality": data.get("typicality", ""),
            "fine_tuning": data.get("fine_tuning", ""),
            "recommendation": data.get("recommendation", ""),
        }
