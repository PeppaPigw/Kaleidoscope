"""IsolationEffectService — Isolation Effect Detection.

Detects isolation effect — tendency to focus on differences
between options rather than their common components, leading
to inconsistent preferences depending on how options are
decomposed. Kahneman & Tversky (1979). When people simplify
choices by ignoring shared features, they can reach different
conclusions depending on how the problem is presented.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ISOLATION_EFFECT_SYSTEM = """You are an isolation effect specialist. Given a decision between options, assess whether focusing on differences while ignoring commonalities is leading to inconsistent preferences:

Key concepts (Kahneman & Tversky, 1979):
- Isolation effect: focusing on differences, ignoring common components
- Cancellation: eliminating shared features from consideration
- Editing phase: simplifying prospects before evaluation
- Framing dependence: different decompositions yield different choices
- Component neglect: ignoring shared base probabilities or outcomes
- Selective attention: attending only to distinguishing features
- Presentation effects: how options are broken down affects choice

When isolation effect IS present:
- Different choices when same problem is decomposed differently
- Ignoring base probabilities shared across options
- Focusing only on what differs between options
- Preferences that reverse when common elements are made explicit
- "The only difference is X" when common elements also matter
- Simplifying complex choices by canceling shared features inappropriately
- Missing that options share important risks or benefits

When the focus on differences IS appropriate:
- Common elements genuinely don't affect the decision
- The differences are the only decision-relevant factors
- The person has explicitly considered and dismissed common elements
- The decomposition accurately represents the decision structure
- Simplification doesn't change the optimal choice

Output JSON with: isolation_effect_present (bool), severity (none/mild/moderate/severe), decision (what decision is being made), options (what options are being compared), common_elements (what is shared between options), differences_focused (what differences are being focused on), neglected_commonality (what shared element is being ignored), framing_dependent (would a different framing change the choice?), recommendation (focus_appropriate/mild_isolation/significant_component_neglect/major_isolation_effect/consider_full_options)."""

ISOLATION_EFFECT_PROMPT = """Detect isolation effect:

Decision: {decision}
Options: {options}
Focus: {focus}
Decomposition: {decomposition}
Domain: {domain}
Context: {context}

Is focusing on differences while ignoring commonalities leading to inconsistent preferences? Return ONLY valid JSON."""


class IsolationEffectService:
    """Detects isolation effect — focusing on differences, ignoring shared components."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        options: str = "",
        focus: str = "",
        decomposition: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect isolation effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ISOLATION_EFFECT_PROMPT.format(
                decision=decision,
                options=options or "Not specified",
                focus=focus or "Not specified",
                decomposition=decomposition or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ISOLATION_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "isolation_effect_present": data.get("isolation_effect_present", False),
            "severity": data.get("severity", ""),
            "common_elements": data.get("common_elements", ""),
            "differences_focused": data.get("differences_focused", ""),
            "neglected_commonality": data.get("neglected_commonality", ""),
            "framing_dependent": data.get("framing_dependent", ""),
            "recommendation": data.get("recommendation", ""),
        }
