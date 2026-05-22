"""MechanismDesignService — Mechanism Design Assessment.

Evaluates whether a system's rules and incentives are designed to
produce the desired outcomes. The inverse of detecting problems —
asks "given what we want to achieve, are the rules designed to get
us there?" Useful for evaluating policies, markets, voting systems,
and organizational structures.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MECHANISM_SYSTEM = """You are a mechanism design specialist. Given a system with rules and incentives, assess whether it achieves its stated goals:
- Do the incentives align individual behavior with collective goals?
- Is the mechanism incentive-compatible (truth-telling is optimal)?
- Is it strategy-proof (gaming the system is not profitable)?
- Does it satisfy participation constraints (people want to participate)?
- Are there unintended equilibria where the mechanism fails?

Output JSON with: mechanism_effective (bool — does it achieve stated goals?), effectiveness_score (0-1), stated_goal (what the mechanism is supposed to achieve), actual_outcome (what it actually produces), incentive_compatibility (bool — is honest behavior optimal?), strategy_proofness (bool — is gaming unprofitable?), participation_constraint (bool — do people want to participate?), gaming_vectors (list of ways to exploit the mechanism), unintended_equilibria (stable states that defeat the purpose), information_requirements (what info the mechanism needs to work), robustness (how well it works with imperfect information or bounded rationality), fairness_properties (what fairness criteria it satisfies/violates), efficiency_loss (how much value is destroyed by the mechanism itself), alternative_mechanisms (better-designed alternatives), implementation_complexity (simple/moderate/complex/impractical), known_impossibility_results (relevant impossibility theorems: Arrow, Gibbard-Satterthwaite, Myerson-Satterthwaite), recommendation (well_designed/minor_fixes/redesign_incentives/fundamental_redesign/accept_limitations)."""

MECHANISM_PROMPT = """Assess mechanism design:

System/Rules: {system}
Stated goal: {goal}
Participants: {participants}
Incentive structure: {incentives}
Domain: {domain}
Context: {context}

Is this mechanism well-designed? Return ONLY valid JSON."""


class MechanismDesignService:
    """Assesses whether system rules produce desired outcomes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        system: str,
        *,
        goal: str = "",
        participants: str = "",
        incentives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess mechanism design."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MECHANISM_PROMPT.format(
                system=system,
                goal=goal or "Not specified",
                participants=participants or "Not specified",
                incentives=incentives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MECHANISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "mechanism_effective": data.get("mechanism_effective", False),
            "effectiveness_score": data.get("effectiveness_score", 0),
            "stated_goal": data.get("stated_goal", ""),
            "actual_outcome": data.get("actual_outcome", ""),
            "incentive_compatibility": data.get("incentive_compatibility", False),
            "strategy_proofness": data.get("strategy_proofness", False),
            "participation_constraint": data.get("participation_constraint", False),
            "gaming_vectors": data.get("gaming_vectors", []),
            "unintended_equilibria": data.get("unintended_equilibria", []),
            "information_requirements": data.get("information_requirements", ""),
            "robustness": data.get("robustness", ""),
            "fairness_properties": data.get("fairness_properties", ""),
            "efficiency_loss": data.get("efficiency_loss", ""),
            "alternative_mechanisms": data.get("alternative_mechanisms", []),
            "implementation_complexity": data.get("implementation_complexity", ""),
            "known_impossibility_results": data.get("known_impossibility_results", ""),
            "recommendation": data.get("recommendation", ""),
        }
