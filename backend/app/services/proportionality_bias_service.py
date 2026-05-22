"""ProportionalityBiasService — Proportionality Bias Detection.

Detects proportionality bias — expecting big effects to have big
causes and small effects to have small causes. Kahneman (2011).
A major event "must" have a major cause. A small change "can't"
have large consequences. Leads to conspiracy thinking (big events
need big explanations) and underestimating butterfly effects.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PROPORTIONALITY_SYSTEM = """You are a proportionality bias specialist. Given a causal attribution, assess whether the expectation of proportional causes and effects is distorting analysis:

Key concepts:
- Proportionality bias: expecting effect magnitude to match cause magnitude
- Big effects need big causes: major events "must" have major explanations
- Small causes can't have big effects: underestimating butterfly effects
- Conspiracy thinking: proportionality bias drives need for "big" explanations
- Complexity blindness: simple causes of complex outcomes feel unsatisfying
- Narrative satisfaction: proportional stories feel more "right"

When proportionality bias IS present:
- Rejecting simple explanations for major events ("it can't be that simple")
- Seeking elaborate causes for significant outcomes
- Dismissing small factors that could have large effects (tipping points)
- Conspiracy theories driven by "something this big needs a big explanation"
- Underestimating cascading effects from small initial conditions
- Overestimating the complexity of causes for complex outcomes

When proportional thinking IS appropriate:
- In well-understood linear systems where proportionality holds
- When the causal mechanism genuinely requires proportional input
- When energy conservation or similar physical laws apply
- When historical patterns show proportional cause-effect in this domain
- When the "small cause" explanation lacks a plausible mechanism

Output JSON with: proportionality_bias_present (bool), severity (none/mild/moderate/severe), effect (what outcome is being explained), attributed_cause (what cause is being proposed), cause_magnitude (how "big" is the proposed cause), effect_magnitude (how "big" is the outcome), proportionality_expected (bool — is the person expecting proportional causes?), actual_mechanism (what is the likely actual causal mechanism?), nonlinear_possibility (could a small cause produce this large effect?), conspiracy_risk (bool — is this driving conspiratorial thinking?), cascade_potential (could small causes cascade to large effects here?), narrative_satisfaction (is the explanation chosen for narrative fit?), recommendation (proportional_reasoning_valid/mild_proportionality_bias/significant_bias/major_proportionality_error/consider_nonlinear_causes)."""

PROPORTIONALITY_PROMPT = """Detect proportionality bias:

Event/effect: {effect}
Attributed cause: {cause}
Reasoning: {reasoning}
Alternative explanations: {alternatives}
Domain: {domain}
Context: {context}

Is proportionality bias distorting causal attribution? Return ONLY valid JSON."""


class ProportionalityBiasService:
    """Detects proportionality bias — expecting effects proportional to causes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        effect: str,
        *,
        cause: str = "",
        reasoning: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect proportionality bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PROPORTIONALITY_PROMPT.format(
                effect=effect,
                cause=cause or "Not specified",
                reasoning=reasoning or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PROPORTIONALITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "effect": effect[:200],
            "proportionality_bias_present": data.get("proportionality_bias_present", False),
            "severity": data.get("severity", ""),
            "attributed_cause": data.get("attributed_cause", ""),
            "cause_magnitude": data.get("cause_magnitude", ""),
            "effect_magnitude": data.get("effect_magnitude", ""),
            "proportionality_expected": data.get("proportionality_expected", False),
            "actual_mechanism": data.get("actual_mechanism", ""),
            "nonlinear_possibility": data.get("nonlinear_possibility", ""),
            "conspiracy_risk": data.get("conspiracy_risk", False),
            "cascade_potential": data.get("cascade_potential", ""),
            "narrative_satisfaction": data.get("narrative_satisfaction", ""),
            "recommendation": data.get("recommendation", ""),
        }
