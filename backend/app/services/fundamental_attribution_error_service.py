"""FundamentalAttributionErrorService — Attribution Error Detection.

Detects the fundamental attribution error (correspondence bias) —
the tendency to attribute others' behavior to their character/
disposition while attributing one's own behavior to situational
factors. "They did it because they're lazy; I did it because
I was busy." Ross (1977). Distorts judgment of people, policies,
and institutions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ATTRIBUTION_SYSTEM = """You are a fundamental attribution error specialist. Given a judgment about behavior, assess whether the fundamental attribution error is distorting the explanation:

Key concepts:
- Dispositional attribution: explaining behavior by character traits ("they're lazy/evil/stupid")
- Situational attribution: explaining behavior by circumstances ("the system made it hard")
- Actor-observer asymmetry: we explain our own behavior situationally, others' dispositionally
- Self-serving bias: success = my character, failure = my circumstances
- Ultimate attribution error: extending individual attribution to entire groups
- Just-world hypothesis: bad things happen to bad people (dispositional explanation of outcomes)

When dispositional attribution IS appropriate:
- Consistent behavior across many different situations
- Behavior that deviates from what most people do in the same situation
- Freely chosen behavior with no external pressure

When situational attribution is more likely correct:
- Many people behave the same way in that situation
- Strong incentives/pressures exist
- The person behaves differently in other contexts
- Structural/systemic factors are present

Output JSON with: attribution_error_present (bool), severity (none/mild/moderate/severe), behavior_being_explained (what behavior is being attributed), attribution_given (dispositional/situational/mixed), attribution_likely_correct (dispositional/situational/mixed), actor_observer_asymmetry (bool — different standards for self vs others?), dispositional_explanation (what character trait is being invoked), situational_factors_ignored (what circumstances are being overlooked), consistency_evidence (does the person always behave this way?), consensus_evidence (do others behave similarly in this situation?), distinctiveness_evidence (does the person behave differently elsewhere?), just_world_thinking (bool — assuming outcomes reflect character?), group_attribution (bool — extending to an entire group?), self_serving_component (bool — favorable attribution for self?), structural_factors (what systemic/institutional factors exist), who_benefits_from_dispositional (who gains from blaming character), policy_implication (how attribution affects proposed solutions), recommendation (attribution_appropriate/mild_error/significant_error/major_attribution_error/consider_structural_factors)."""

ATTRIBUTION_PROMPT = """Detect fundamental attribution error:

Judgment: {judgment}
Behavior observed: {behavior}
Situation/Context: {situation}
Who is judging whom: {judge_target}
Domain: {domain}
Context: {context}

Is the fundamental attribution error at play? Return ONLY valid JSON."""


class FundamentalAttributionErrorService:
    """Detects fundamental attribution error — character vs circumstance misattribution."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        behavior: str = "",
        situation: str = "",
        judge_target: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect fundamental attribution error."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ATTRIBUTION_PROMPT.format(
                judgment=judgment,
                behavior=behavior or "Not specified",
                situation=situation or "Not specified",
                judge_target=judge_target or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ATTRIBUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "attribution_error_present": data.get("attribution_error_present", False),
            "severity": data.get("severity", ""),
            "behavior_being_explained": data.get("behavior_being_explained", ""),
            "attribution_given": data.get("attribution_given", ""),
            "attribution_likely_correct": data.get("attribution_likely_correct", ""),
            "actor_observer_asymmetry": data.get("actor_observer_asymmetry", False),
            "dispositional_explanation": data.get("dispositional_explanation", ""),
            "situational_factors_ignored": data.get("situational_factors_ignored", ""),
            "consistency_evidence": data.get("consistency_evidence", ""),
            "consensus_evidence": data.get("consensus_evidence", ""),
            "distinctiveness_evidence": data.get("distinctiveness_evidence", ""),
            "just_world_thinking": data.get("just_world_thinking", False),
            "group_attribution": data.get("group_attribution", False),
            "self_serving_component": data.get("self_serving_component", False),
            "structural_factors": data.get("structural_factors", ""),
            "who_benefits_from_dispositional": data.get("who_benefits_from_dispositional", ""),
            "policy_implication": data.get("policy_implication", ""),
            "recommendation": data.get("recommendation", ""),
        }
