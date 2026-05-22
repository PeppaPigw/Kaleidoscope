"""ThoughtExperimentService — Rigorous Thought Experiment Design.

Creates thought experiments to test claims where real experiments are
impractical. Designs scenarios that isolate the key variable, identifies
what intuitions they pump, and flags where thought experiments mislead.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

THOUGHT_EXP_SYSTEM = """You are a thought experiment designer. Given a claim to test, design thought experiments that:
- Isolate the key variable (change one thing, hold everything else constant)
- Pump clear intuitions (the answer should feel obvious once you consider the scenario)
- Are internally consistent (no hidden contradictions)
- Reveal something non-obvious about the claim
- Cover both supporting and undermining scenarios

Output JSON with: experiments (list of: name, scenario, what_it_tests, expected_intuition, what_it_reveals, limitations (where this thought experiment might mislead), variant (a modification that changes the intuition)), strongest_experiment (which is most illuminating and why), collective_verdict (what the thought experiments together suggest), thought_experiment_limitations (general caveats about using thought experiments here), real_experiment_possible (bool, could we actually test this empirically instead)."""

THOUGHT_EXP_PROMPT = """Design thought experiments for this claim:

Claim: {claim}
Domain: {domain}
Purpose: {purpose}
Constraints: {constraints}

Design illuminating thought experiments. Return ONLY valid JSON."""


class ThoughtExperimentService:
    """Designs rigorous thought experiments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def design(
        self,
        claim: str,
        *,
        domain: str = "",
        purpose: str = "",
        constraints: str = "",
    ) -> dict:
        """Design thought experiments for a claim."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=THOUGHT_EXP_PROMPT.format(
                claim=claim,
                domain=domain or "general",
                purpose=purpose or "Test the claim's validity",
                constraints=constraints or "None",
            ),
            system=THOUGHT_EXP_SYSTEM,
            max_tokens=4096,
            temperature=0.5,
        )
        data = parse_llm_json(raw)

        experiments = data.get("experiments", [])
        return {
            "claim": claim[:200],
            "experiments_count": len(experiments),
            "experiments": experiments,
            "strongest_experiment": data.get("strongest_experiment", ""),
            "collective_verdict": data.get("collective_verdict", ""),
            "limitations": data.get("thought_experiment_limitations", ""),
            "real_experiment_possible": data.get("real_experiment_possible", False),
        }
