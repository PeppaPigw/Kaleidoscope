"""LucasCritiqueService — Lucas Critique Detection.

Detects the Lucas Critique — when policy changes alter the
behavioral relationships they're trying to exploit. Robert Lucas
(1976). Historical correlations break down when you try to use
them for policy because agents adapt their behavior to the new
policy. "When a measure becomes a target, it ceases to be a
good measure" (Goodhart overlap, but Lucas is specifically about
policy-induced behavioral change).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

LUCAS_SYSTEM = """You are a Lucas Critique specialist. Given a policy or intervention based on historical patterns, assess whether the Lucas Critique applies:

Key concepts (Lucas, 1976):
- Lucas Critique: policy changes alter the behavioral relationships they exploit
- Rational expectations: agents anticipate and adapt to policy changes
- Structural vs reduced-form: historical correlations aren't structural invariants
- Policy invariance failure: relationships that held historically break under new policy
- Goodhart overlap: "when a measure becomes a target, it ceases to be a good measure"
- Campbell's Law: the more a metric is used for decisions, the more it's corrupted

When the Lucas Critique APPLIES:
- Policy is based on historical correlations that will change under the policy
- Agents can observe and adapt to the intervention
- The behavioral relationship is not a structural invariant
- Past patterns assumed to continue despite changed incentives
- The policy changes the information/incentive environment

When historical patterns ARE reliable:
- The relationship is based on physical/structural constraints (not behavior)
- Agents cannot observe or adapt to the change
- The policy doesn't alter the underlying incentive structure
- The relationship has been stable across different policy regimes
- Micro-foundations support the relationship independently of history

Output JSON with: lucas_critique_applies (bool), severity (none/mild/moderate/severe), policy_intervention (what policy/change is being proposed), historical_pattern (what past relationship is being relied on), behavioral_adaptation (how agents will change behavior in response), relationship_structural (bool — is the relationship a structural invariant?), agent_awareness (bool — can agents observe and adapt to the policy?), incentive_change (how the policy changes incentives), expected_breakdown (how the historical pattern will break), unintended_consequences (what behavioral changes will the policy cause), goodhart_overlap (bool — is a measure becoming a target?), alternative_approach (what policy would be robust to behavioral adaptation), micro_foundations (does theory support the relationship independent of history?), recommendation (pattern_robust/mild_adaptation_risk/significant_lucas_critique/major_behavioral_shift_expected/redesign_for_adaptation)."""

LUCAS_PROMPT = """Detect Lucas Critique:

Policy/Intervention: {policy}
Historical basis: {historical_basis}
Target behavior: {target_behavior}
Agent characteristics: {agents}
Domain: {domain}
Context: {context}

Will this policy change the behavior it's trying to exploit? Return ONLY valid JSON."""


class LucasCritiqueService:
    """Detects Lucas Critique — policy changes altering the relationships they exploit."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        policy: str,
        *,
        historical_basis: str = "",
        target_behavior: str = "",
        agents: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Lucas Critique."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=LUCAS_PROMPT.format(
                policy=policy,
                historical_basis=historical_basis or "Not specified",
                target_behavior=target_behavior or "Not specified",
                agents=agents or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=LUCAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "policy": policy[:200],
            "lucas_critique_applies": data.get("lucas_critique_applies", False),
            "severity": data.get("severity", ""),
            "policy_intervention": data.get("policy_intervention", ""),
            "historical_pattern": data.get("historical_pattern", ""),
            "behavioral_adaptation": data.get("behavioral_adaptation", ""),
            "relationship_structural": data.get("relationship_structural", False),
            "agent_awareness": data.get("agent_awareness", False),
            "incentive_change": data.get("incentive_change", ""),
            "expected_breakdown": data.get("expected_breakdown", ""),
            "unintended_consequences": data.get("unintended_consequences", ""),
            "goodhart_overlap": data.get("goodhart_overlap", False),
            "alternative_approach": data.get("alternative_approach", ""),
            "micro_foundations": data.get("micro_foundations", ""),
            "recommendation": data.get("recommendation", ""),
        }
