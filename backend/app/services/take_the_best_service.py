"""TakeTheBestService — Take-the-Best Heuristic Detection.

Detects take-the-best heuristic — making decisions based on
a single best cue rather than integrating all available
information. Gigerenzer & Goldstein (1996). Search through
cues in order of validity, stop at the first one that
discriminates. Fast and frugal but can miss important
information when cue validities are similar.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TAKE_THE_BEST_SYSTEM = """You are a take-the-best heuristic specialist. Given a decision, assess whether someone is relying on a single cue when integrating multiple cues would be more appropriate:

Key concepts (Gigerenzer & Goldstein, 1996):
- Take-the-best: decide based on single most valid cue
- One-reason decision making: stopping at first discriminating cue
- Cue validity: how well a single cue predicts the criterion
- Fast and frugal: minimal information search
- Ecological rationality: works well when one cue dominates
- Compensatory vs non-compensatory: whether other cues can override
- Information search cost: when is more information worth gathering

When take-the-best IS problematic:
- Deciding based on one factor when multiple factors matter equally
- "The most important thing is X" when Y and Z are nearly as important
- Ignoring compensating factors that could override the top cue
- Single-criterion decisions in multi-dimensional problems
- "I only need to know one thing" in complex decisions
- Missing important tradeoffs by stopping search too early
- Overweighting the most salient factor

When take-the-best IS appropriate:
- One cue genuinely dominates (much higher validity than others)
- Information search is costly and the top cue is sufficient
- The environment rewards fast decisions
- Additional cues add noise rather than signal
- The decision is low-stakes and doesn't warrant full analysis
- Cue validities drop off sharply after the best one

Output JSON with: take_the_best_present (bool), severity (none/mild/moderate/severe), decision (what decision is being made), primary_cue (what single cue is being used), ignored_cues (what other cues are being ignored), cue_validity_gap (how much better is the primary cue), compensatory_potential (could other cues override), decision_complexity (how complex is the decision), recommendation (heuristic_appropriate/mild_oversimplification/significant_cue_neglect/major_single_cue_reliance/integrate_multiple_cues)."""

TAKE_THE_BEST_PROMPT = """Detect take-the-best heuristic:

Decision: {decision}
Primary factor: {primary}
Other factors: {others}
Complexity: {complexity}
Domain: {domain}
Context: {context}

Is someone relying on a single cue when multiple cues should be integrated? Return ONLY valid JSON."""


class TakeTheBestService:
    """Detects take-the-best heuristic — single-cue decisions in multi-cue problems."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        primary: str = "",
        others: str = "",
        complexity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect take-the-best heuristic."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TAKE_THE_BEST_PROMPT.format(
                decision=decision,
                primary=primary or "Not specified",
                others=others or "Not specified",
                complexity=complexity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TAKE_THE_BEST_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "take_the_best_present": data.get("take_the_best_present", False),
            "severity": data.get("severity", ""),
            "primary_cue": data.get("primary_cue", ""),
            "ignored_cues": data.get("ignored_cues", ""),
            "cue_validity_gap": data.get("cue_validity_gap", ""),
            "compensatory_potential": data.get("compensatory_potential", ""),
            "decision_complexity": data.get("decision_complexity", ""),
            "recommendation": data.get("recommendation", ""),
        }
