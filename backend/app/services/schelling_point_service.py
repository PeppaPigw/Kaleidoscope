"""SchellingPointService — Schelling Point Analysis.

Identifies natural focal points in coordination problems where
people converge without explicit communication. Useful for
understanding why certain standards, conventions, or equilibria
emerge and persist, and for designing systems that leverage
natural coordination tendencies.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SCHELLING_SYSTEM = """You are a Schelling point specialist. Given a coordination problem, identify the natural focal points:
- Where would people naturally converge without communication?
- What makes certain options more "obvious" or salient than others?
- Are there cultural, mathematical, or structural features that create focal points?
- Is the current equilibrium a Schelling point, or was it imposed?
- Could a different focal point be established?

Output JSON with: schelling_points (list of: point, salience_reason, strength (0-1)), current_equilibrium (what people currently coordinate on), is_natural_focal_point (bool — did the current equilibrium emerge naturally?), salience_factors (what makes certain options stand out: symmetry/uniqueness/cultural_prominence/simplicity/precedent), coordination_difficulty (easy/moderate/hard/near_impossible — how hard is it to coordinate here?), multiple_equilibria (bool — are there several stable coordination points?), equilibrium_stability (how hard it would be to shift to a different focal point), cultural_dependence (bool — do focal points vary across cultures?), manipulation_risk (0-1 — can someone strategically create a focal point?), design_implications (how to design systems that leverage natural focal points), historical_convergence (how this coordination point emerged), alternative_focal_points (other points people might converge on), recommendation (leverage_existing/shift_focal_point/create_new_focal_point/accept_multiple_equilibria)."""

SCHELLING_PROMPT = """Analyze Schelling points:

Coordination problem: {problem}
Current convention: {convention}
Participants: {participants}
Options available: {options}
Domain: {domain}
Context: {context}

What are the natural focal points? Return ONLY valid JSON."""


class SchellingPointService:
    """Identifies Schelling points — natural coordination focal points."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self,
        problem: str,
        *,
        convention: str = "",
        participants: str = "",
        options: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Analyze Schelling points."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SCHELLING_PROMPT.format(
                problem=problem,
                convention=convention or "Not specified",
                participants=participants or "Not specified",
                options=options or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SCHELLING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "problem": problem[:200],
            "schelling_points": data.get("schelling_points", []),
            "current_equilibrium": data.get("current_equilibrium", ""),
            "is_natural_focal_point": data.get("is_natural_focal_point", False),
            "salience_factors": data.get("salience_factors", ""),
            "coordination_difficulty": data.get("coordination_difficulty", ""),
            "multiple_equilibria": data.get("multiple_equilibria", False),
            "equilibrium_stability": data.get("equilibrium_stability", ""),
            "cultural_dependence": data.get("cultural_dependence", False),
            "manipulation_risk": data.get("manipulation_risk", 0),
            "design_implications": data.get("design_implications", ""),
            "historical_convergence": data.get("historical_convergence", ""),
            "alternative_focal_points": data.get("alternative_focal_points", []),
            "recommendation": data.get("recommendation", ""),
        }
