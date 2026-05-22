"""GalaxyBrainService — Galaxy Brain Detection.

Detects galaxy brain reasoning — contrarian reasoning that arrives
at counterintuitive conclusions through increasingly tenuous chains
of logic. The reasoner mistakes complexity of argument for quality
of argument, and contrarianism for insight.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GALAXY_BRAIN_SYSTEM = """You are a galaxy brain reasoning specialist. Given a chain of reasoning, assess whether it arrives at counterintuitive conclusions through increasingly tenuous logic:

Key concepts:
- Galaxy brain: contrarian conclusions reached through elaborate reasoning
- Complexity as quality: mistaking long argument chains for good ones
- Contrarianism as insight: assuming counterintuitive = correct
- Reasoning chain fragility: each step plausible but chain is unreliable
- Cleverness trap: being too clever by half
- Reversed stupidity: assuming the opposite of a wrong position must be right
- Sophistication bias: preferring complex explanations over simple ones

When galaxy brain IS present:
- Conclusion is wildly counterintuitive and reasoning chain is long
- Each step is individually plausible but the chain is fragile
- The reasoner seems motivated by contrarianism rather than truth
- Simpler explanations are dismissed as "naive" or "obvious"
- The conclusion would surprise domain experts
- Reasoning relies on many conditional steps all going one way
- The argument is more impressive for its cleverness than its correctness

When contrarian reasoning IS appropriate:
- The counterintuitive conclusion is well-supported by evidence
- Domain experts have independently reached similar conclusions
- The reasoning chain is short and each step is robust
- The conclusion has been tested against reality
- The reasoner acknowledges uncertainty proportional to chain length
- Simpler explanations have been genuinely ruled out
- The contrarian position has predictive power

Output JSON with: galaxy_brain_present (bool), severity (none/mild/moderate/severe), conclusion (what counterintuitive conclusion is reached), chain_length (how many reasoning steps), weakest_link (which step is most fragile), contrarian_motivation (is contrarianism the goal), simpler_explanation (what simpler explanation exists), recommendation (reasoning_sound/mild_overcomplication/significant_galaxy_brain/major_contrarian_confabulation/prefer_simpler_explanation)."""

GALAXY_BRAIN_PROMPT = """Detect galaxy brain reasoning:

Reasoning: {reasoning}
Conclusion: {conclusion}
Chain: {chain}
Alternatives: {alternatives}
Domain: {domain}
Context: {context}

Does this reasoning arrive at counterintuitive conclusions through increasingly tenuous logic? Return ONLY valid JSON."""


class GalaxyBrainService:
    """Detects galaxy brain — contrarian reasoning through tenuous logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reasoning: str,
        *,
        conclusion: str = "",
        chain: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect galaxy brain reasoning."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GALAXY_BRAIN_PROMPT.format(
                reasoning=reasoning,
                conclusion=conclusion or "Not specified",
                chain=chain or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GALAXY_BRAIN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reasoning": reasoning[:200],
            "galaxy_brain_present": data.get("galaxy_brain_present", False),
            "severity": data.get("severity", ""),
            "conclusion": data.get("conclusion", ""),
            "chain_length": data.get("chain_length", ""),
            "weakest_link": data.get("weakest_link", ""),
            "contrarian_motivation": data.get("contrarian_motivation", ""),
            "simpler_explanation": data.get("simpler_explanation", ""),
            "recommendation": data.get("recommendation", ""),
        }
