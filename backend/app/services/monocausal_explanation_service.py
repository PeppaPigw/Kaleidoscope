"""MonocausalExplanationService — Monocausal Explanation Detection.

Detects monocausal explanation — attributing complex outcomes to a
single cause when multiple interacting causes are at work, reducing
multicausal reality to a single factor.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MONOCAUSAL_EXPLANATION_SYSTEM = """You are a monocausal explanation specialist. Given an explanation, assess whether complex outcomes are being attributed to a single cause:

Key concepts:
- Monocausal explanation: single cause for multicausal outcome
- Causal reductionism: reducing multiple causes to one
- Silver bullet thinking: one factor explains everything
- Overdetermination blindness: missing that multiple causes suffice
- Interaction effects: causes that work together, not alone
- Necessary vs sufficient: confusing one cause with the only cause
- Causal web: interconnected causes treated as single chain

When monocausal explanation IS present:
- Complex outcome attributed to single factor
- Multiple known causes reduced to one
- Interaction effects ignored
- Other contributing factors dismissed
- Single cause treated as both necessary and sufficient
- Causal complexity flattened to simple narrative
- Multicausal evidence ignored for clean story

When single-cause focus is appropriate:
- One cause genuinely dominant (explains most variance)
- Other causes acknowledged but shown to be minor
- Focus on one cause for analytical purposes with caveats
- Proximate cause identified within acknowledged causal web
- Single cause is genuinely necessary and sufficient
- Simplification acknowledged as simplification
- Multicausal nature noted even if one cause highlighted

Output JSON with: monocausal_present (bool), severity (none/mild/moderate/severe), explanation (what is explained), single_cause (what single cause is cited), other_causes (what other causes exist), interactions (what interaction effects are missed), recommendation (appropriate_focus/mild_oversimplification/significant_monocausal/major_causal_reductionism/acknowledge_multicausality)."""

MONOCAUSAL_EXPLANATION_PROMPT = """Detect monocausal explanation:

Explanation: {explanation}
Cause cited: {cause}
Other factors: {factors}
Outcome: {outcome}
Domain: {domain}
Context: {context}

Is a complex outcome being attributed to a single cause when multiple causes are at work? Return ONLY valid JSON."""


class MonocausalExplanationService:
    """Detects monocausal explanation — single cause for multicausal outcomes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanation: str,
        *,
        cause: str = "",
        factors: str = "",
        outcome: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect monocausal explanation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MONOCAUSAL_EXPLANATION_PROMPT.format(
                explanation=explanation,
                cause=cause or "Not specified",
                factors=factors or "Not specified",
                outcome=outcome or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MONOCAUSAL_EXPLANATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanation": explanation[:200],
            "monocausal_present": data.get("monocausal_present", False),
            "severity": data.get("severity", ""),
            "single_cause": data.get("single_cause", ""),
            "other_causes": data.get("other_causes", ""),
            "interactions": data.get("interactions", ""),
            "recommendation": data.get("recommendation", ""),
        }
