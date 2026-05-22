"""MentalSimulationService — Mental Simulation Bias Detection.

Detects mental simulation bias — tendency for ease of mentally
simulating an event to influence probability judgments and
emotional reactions. Kahneman & Tversky (1982). Events that
are easy to imagine feel more likely. "Almost" outcomes
generate stronger emotions. Counterfactual ease drives
regret and perceived probability.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MENTAL_SIMULATION_SYSTEM = """You are a mental simulation bias specialist. Given a probability judgment or emotional reaction, assess whether ease of mental simulation is inappropriately influencing the assessment:

Key concepts (Kahneman & Tversky, 1982):
- Simulation heuristic: ease of imagining → perceived probability
- Counterfactual closeness: "almost" outcomes feel more significant
- Undoing: mentally changing events to alter outcomes
- Emotional amplification: easy-to-simulate alternatives intensify emotion
- Scenario availability: vivid scenarios feel more likely
- Downhill change: easier to simulate removing obstacles than adding them
- Exceptional vs routine: exceptional events easier to undo mentally

When mental simulation bias IS present:
- "I can easily imagine how X could happen" → overestimating probability
- Intense regret over "near misses" that weren't actually close
- Vivid disaster scenarios driving excessive fear
- "If only I had..." when the counterfactual wasn't actually likely
- Easy-to-imagine outcomes treated as more probable
- Emotional intensity driven by simulation ease, not actual closeness
- Planning based on most imaginable scenario rather than most likely

When the simulation IS informative:
- Ease of simulation reflects genuine causal proximity
- The imagined scenario is based on realistic mechanisms
- The person distinguishes imaginability from probability
- Simulation is used for planning, not probability estimation
- The emotional response is proportional to actual risk

Output JSON with: mental_simulation_bias_present (bool), severity (none/mild/moderate/severe), judgment (what judgment or reaction is occurring), simulated_scenario (what is being mentally simulated), simulation_ease (how easy is it to imagine), actual_probability (what is the actual probability), emotional_impact (how is the simulation affecting emotions), counterfactual (what counterfactual is being generated), recommendation (simulation_informative/mild_simulation_bias/significant_imaginability_effect/major_simulation_distortion/separate_imaginability_from_probability)."""

MENTAL_SIMULATION_PROMPT = """Detect mental simulation bias:

Judgment: {judgment}
Scenario: {scenario}
Ease: {ease}
Reaction: {reaction}
Domain: {domain}
Context: {context}

Is ease of mental simulation inappropriately influencing probability or emotion? Return ONLY valid JSON."""


class MentalSimulationService:
    """Detects mental simulation bias — imaginability distorting probability/emotion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        scenario: str = "",
        ease: str = "",
        reaction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect mental simulation bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MENTAL_SIMULATION_PROMPT.format(
                judgment=judgment,
                scenario=scenario or "Not specified",
                ease=ease or "Not specified",
                reaction=reaction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MENTAL_SIMULATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "mental_simulation_bias_present": data.get("mental_simulation_bias_present", False),
            "severity": data.get("severity", ""),
            "simulated_scenario": data.get("simulated_scenario", ""),
            "simulation_ease": data.get("simulation_ease", ""),
            "actual_probability": data.get("actual_probability", ""),
            "emotional_impact": data.get("emotional_impact", ""),
            "counterfactual": data.get("counterfactual", ""),
            "recommendation": data.get("recommendation", ""),
        }
