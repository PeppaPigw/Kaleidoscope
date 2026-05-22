"""TypicalMindFallacyService — Typical Mind Fallacy Detection.

Detects the typical mind fallacy — assuming that other people's
mental experiences, preferences, and cognitive processes are
similar to one's own. "I can't imagine wanting X, so no one
really wants X." People differ enormously in visualization
ability, internal monologue, emotional intensity, and cognitive
style — but each person assumes their experience is typical.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TYPICAL_MIND_SYSTEM = """You are a typical mind fallacy specialist. Given an assumption about others' mental states, assess whether one's own cognitive experience is being projected as universal:

Key concepts:
- Typical mind fallacy: assuming others think/feel like you do
- Mind blindness: inability to model different cognitive styles
- Projection of experience: "everyone does this" based on self
- Cognitive diversity denial: assuming uniform mental processes
- Empathy gap variant: can't imagine different internal experiences
- False consensus on cognition: "doesn't everyone think in pictures?"
- Introspection illusion: assuming introspective access is universal

When typical mind fallacy IS present:
- "Everyone procrastinates" (projecting own experience)
- "Just visualize it" (assuming everyone can visualize)
- "How can you not have an internal monologue?"
- "Nobody actually enjoys that" (projecting preferences)
- "It's obvious that..." (assuming shared intuitions)
- Designing for one cognitive style assuming it's universal
- "Just think about it logically" (assuming same reasoning style)

When generalization IS appropriate:
- Based on empirical data about population distributions
- Acknowledged as a generalization with known exceptions
- The mental process in question is genuinely universal
- Individual differences are accounted for
- The claim is about averages, not universals

Output JSON with: typical_mind_present (bool), severity (none/mild/moderate/severe), assumption (what is being assumed about others), own_experience (what is the person's own experience), actual_variation (what variation actually exists), affected_decision (how does this assumption affect decisions), population_data (what do we know about actual distribution), empathy_gap (what experiences can't be imagined), recommendation (generalization_valid/mild_projection/significant_typical_mind/major_cognitive_blindness/account_for_cognitive_diversity)."""

TYPICAL_MIND_PROMPT = """Detect typical mind fallacy:

Assumption: {assumption}
Own experience: {own_experience}
Others' experience: {others_experience}
Decision affected: {decision}
Domain: {domain}
Context: {context}

Is one's own cognitive experience being projected as universal? Return ONLY valid JSON."""


class TypicalMindFallacyService:
    """Detects typical mind fallacy — assuming others think like you."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        assumption: str,
        *,
        own_experience: str = "",
        others_experience: str = "",
        decision: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect typical mind fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TYPICAL_MIND_PROMPT.format(
                assumption=assumption,
                own_experience=own_experience or "Not specified",
                others_experience=others_experience or "Not specified",
                decision=decision or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TYPICAL_MIND_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "assumption": assumption[:200],
            "typical_mind_present": data.get("typical_mind_present", False),
            "severity": data.get("severity", ""),
            "own_experience": data.get("own_experience", ""),
            "actual_variation": data.get("actual_variation", ""),
            "affected_decision": data.get("affected_decision", ""),
            "population_data": data.get("population_data", ""),
            "empathy_gap": data.get("empathy_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
