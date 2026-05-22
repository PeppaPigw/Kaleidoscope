"""FeaturePositiveService — Feature-Positive Effect Detection.

Detects the feature-positive effect — the tendency to notice
and weight the presence of features more than their absence.
Jenkins & Sainsbury (1969). People are better at detecting
what IS there than what ISN'T. Missing features, absent
evidence, and things that didn't happen are systematically
underweighted in judgment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FEATURE_POSITIVE_SYSTEM = """You are a feature-positive effect specialist. Given a judgment or evaluation, assess whether presence is being noticed and weighted more than absence:

Key concepts (Jenkins & Sainsbury, 1969):
- Feature-positive effect: presence noticed more than absence
- Absence blindness: what's missing is invisible
- Non-events: things that didn't happen are hard to notice
- Confirmation bias interaction: looking for presence, not absence
- Dogs that didn't bark: critical absences overlooked
- Positive test strategy: testing for presence rather than absence
- Omission detection failure: missing items not noticed

When the feature-positive effect IS distorting:
- Evaluating a plan by what it includes, not what it's missing
- Noticing features present in a product but not gaps
- Judging evidence by what's there, not what's conspicuously absent
- "It has X, Y, and Z" without asking "but where is W?"
- Failing to notice the dog that didn't bark
- Checklists of what's present without checking for what's absent
- Risk assessment focused on visible threats, not invisible ones

When presence-focus IS appropriate:
- The relevant features are genuinely the ones present
- Absence is genuinely uninformative in this context
- The evaluation criteria are about positive attributes
- What's missing is genuinely not relevant to the decision
- The domain doesn't have meaningful absences to detect

Output JSON with: feature_positive_present (bool), severity (none/mild/moderate/severe), evaluation (what is being evaluated), features_noticed (what presence is being noticed), absences_missed (what absence is being overlooked), importance_of_absence (how important is what's missing), detection_asymmetry (how much harder is absence to detect), critical_gap (what critical absence is being missed), recommendation (presence_focus_appropriate/mild_absence_blindness/significant_feature_positive_effect/major_critical_absence_missed/actively_check_for_absence)."""

FEATURE_POSITIVE_PROMPT = """Detect feature-positive effect:

Evaluation: {evaluation}
Present features: {present}
Potential absences: {absent}
Decision context: {decision}
Domain: {domain}
Context: {context}

Is presence being noticed and weighted while absence is being overlooked? Return ONLY valid JSON."""


class FeaturePositiveService:
    """Detects feature-positive effect — noticing presence more than absence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        present: str = "",
        absent: str = "",
        decision: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect feature-positive effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FEATURE_POSITIVE_PROMPT.format(
                evaluation=evaluation,
                present=present or "Not specified",
                absent=absent or "Not specified",
                decision=decision or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FEATURE_POSITIVE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "feature_positive_present": data.get("feature_positive_present", False),
            "severity": data.get("severity", ""),
            "features_noticed": data.get("features_noticed", ""),
            "absences_missed": data.get("absences_missed", ""),
            "importance_of_absence": data.get("importance_of_absence", ""),
            "detection_asymmetry": data.get("detection_asymmetry", ""),
            "critical_gap": data.get("critical_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
