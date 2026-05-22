"""CounterexampleGeneratorService — Adversarial Counterexample Discovery.

Given a claim or theory, generates the most challenging counterexamples
that would stress-test it. Finds edge cases, boundary conditions, and
scenarios where the claim might fail — the intellectual equivalent of
adversarial testing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COUNTER_SYSTEM = """You are a counterexample generation specialist. Given a claim or theory, generate the most challenging counterexamples. Good counterexamples:
- Target the claim's weakest point
- Are plausible (not contrived or impossible scenarios)
- Are specific (concrete, not vague)
- Are diverse (attack from different angles)
- Range from clear refutations to subtle edge cases

For each counterexample, assess whether it actually refutes the claim or just limits its scope.

Output JSON with: counterexamples (list of: example, type (refutation/limitation/edge_case/thought_experiment), plausibility (0-1), damage_to_claim (none/minor/moderate/severe/fatal), how_defender_might_respond, is_genuine_refutation (bool)), strongest_counterexample (which and why), claim_survives (bool, does the claim survive all counterexamples), revised_claim (if the claim needs modification to survive, what's the revised version), overall_robustness (0-1, how well does the claim hold up under adversarial pressure)."""

COUNTER_PROMPT = """Generate counterexamples for this claim:

Claim: {claim}
Domain: {domain}
Context: {context}

What are the most challenging counterexamples? Return ONLY valid JSON."""


class CounterexampleGeneratorService:
    """Generates adversarial counterexamples to stress-test claims."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(
        self,
        claim: str,
        *,
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Generate counterexamples for a claim."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COUNTER_PROMPT.format(
                claim=claim,
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COUNTER_SYSTEM,
            max_tokens=4096,
            temperature=0.5,
        )
        data = parse_llm_json(raw)

        counterexamples = data.get("counterexamples", [])
        return {
            "claim": claim[:200],
            "counterexamples_found": len(counterexamples),
            "counterexamples": counterexamples,
            "strongest": data.get("strongest_counterexample", ""),
            "claim_survives": data.get("claim_survives", True),
            "revised_claim": data.get("revised_claim", ""),
            "overall_robustness": data.get("overall_robustness", 0),
        }
