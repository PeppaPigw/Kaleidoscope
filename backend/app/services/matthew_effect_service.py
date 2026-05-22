"""MatthewEffectService — Matthew Effect Detection.

Detects the Matthew Effect — accumulated advantage where initial
success breeds further success regardless of merit. "The rich get
richer and the poor get poorer." Named after Matthew 25:29.
Merton (1968) in science: famous scientists get more credit for
the same work. Applies to wealth, citations, platform algorithms,
network effects, and any system with positive feedback loops.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MATTHEW_SYSTEM = """You are a Matthew Effect specialist. Given a situation involving success, resources, or recognition, assess whether the Matthew Effect is creating unfair accumulated advantage:

Key concepts (Merton, 1968):
- Matthew Effect: initial advantage compounds over time
- Accumulated advantage: early success → more resources → more success
- Preferential attachment: new connections go to already-connected nodes
- Winner-take-all dynamics: small initial differences → large outcome gaps
- Positive feedback loops: success breeds success regardless of merit
- Path dependence: early advantages lock in long-term outcomes

Examples:
- Science: famous scientists get cited more for the same quality work
- Wealth: compound interest, network access, better education → more wealth
- Platforms: popular content gets promoted → becomes more popular
- Hiring: prestigious credentials → better jobs → more prestigious credentials
- Cities: successful cities attract talent → become more successful

When the Matthew Effect IS present:
- Initial advantages compound over time
- Similar quality/effort produces different outcomes based on starting position
- Positive feedback loops amplify small differences
- Late entrants face structural barriers regardless of merit
- Success attribution ignores accumulated advantage

When differential outcomes ARE merit-based:
- Consistent superior performance over time
- Advantages earned through genuine innovation
- No structural barriers to entry
- Multiple independent paths to success exist

Output JSON with: matthew_effect_present (bool), severity (none/mild/moderate/severe/systemic), initial_advantage (what early advantage is compounding), feedback_mechanism (how success breeds more success), merit_component (how much is genuine merit vs accumulated advantage), structural_barriers (what prevents others from competing), path_dependence (how early choices locked in outcomes), winner_take_all (bool — are small differences producing huge outcome gaps?), preferential_attachment (bool — do new resources flow to already-rich?), counterfactual (what would happen with equal starting positions?), mobility_possible (bool — can newcomers break in?), intervention_points (where could the cycle be interrupted), who_benefits (who gains from the current dynamic), who_is_excluded (who is locked out), systemic_vs_individual (is this individual luck or system design?), recommendation (merit_based/mild_accumulated_advantage/significant_matthew_effect/severe_structural_lock_in/intervention_needed)."""

MATTHEW_PROMPT = """Detect Matthew Effect:

Situation: {situation}
Success pattern: {success_pattern}
Starting conditions: {starting_conditions}
Feedback loops: {feedback_loops}
Domain: {domain}
Context: {context}

Is the Matthew Effect creating unfair accumulated advantage? Return ONLY valid JSON."""


class MatthewEffectService:
    """Detects Matthew Effect — accumulated advantage and winner-take-all dynamics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        success_pattern: str = "",
        starting_conditions: str = "",
        feedback_loops: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Matthew Effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MATTHEW_PROMPT.format(
                situation=situation,
                success_pattern=success_pattern or "Not specified",
                starting_conditions=starting_conditions or "Not specified",
                feedback_loops=feedback_loops or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MATTHEW_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "matthew_effect_present": data.get("matthew_effect_present", False),
            "severity": data.get("severity", ""),
            "initial_advantage": data.get("initial_advantage", ""),
            "feedback_mechanism": data.get("feedback_mechanism", ""),
            "merit_component": data.get("merit_component", ""),
            "structural_barriers": data.get("structural_barriers", ""),
            "path_dependence": data.get("path_dependence", ""),
            "winner_take_all": data.get("winner_take_all", False),
            "preferential_attachment": data.get("preferential_attachment", False),
            "counterfactual": data.get("counterfactual", ""),
            "mobility_possible": data.get("mobility_possible", False),
            "intervention_points": data.get("intervention_points", ""),
            "who_benefits": data.get("who_benefits", ""),
            "who_is_excluded": data.get("who_is_excluded", ""),
            "systemic_vs_individual": data.get("systemic_vs_individual", ""),
            "recommendation": data.get("recommendation", ""),
        }
