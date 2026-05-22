"""RationalizationDetectService — Rationalization vs Rationality Detection.

Detects rationalization — constructing reasons after the fact to
justify a conclusion already reached, rather than reasoning from
evidence to conclusions. The direction of inference is reversed:
conclusion → reasons (rationalization) vs evidence → conclusion
(rationality). Haidt (2001): moral reasoning is often post-hoc
justification of intuitive judgments.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

RATIONALIZATION_SYSTEM = """You are a rationalization specialist. Given a reasoning process, assess whether reasons are being constructed after the fact to justify a pre-existing conclusion:

Key concepts (Haidt, 2001):
- Rationalization: constructing reasons to justify existing conclusions
- Rationality: reasoning from evidence to conclusions
- Post-hoc justification: finding reasons after deciding
- Motivated reasoning: reasoning toward desired conclusions
- Confabulation: generating explanations for decisions made unconsciously
- Elephant and rider: intuition decides, reason justifies
- Bottom-up vs top-down: evidence-driven vs conclusion-driven

When rationalization IS present:
- The conclusion was reached before the reasons were found
- Reasons change but conclusion stays the same
- If one justification is refuted, another is immediately produced
- The person would reach the same conclusion regardless of evidence
- Reasons are generated to persuade others, not to inform self
- "I just feel it's right" followed by post-hoc reasoning
- The reasoning process is suspiciously convenient

When reasoning IS genuine:
- The conclusion could change if evidence changed
- The person can specify what evidence would change their mind
- Reasons were generated before or during conclusion formation
- The reasoning process is transparent and follows evidence
- Counter-evidence is genuinely engaged with
- The person has changed conclusions when evidence warranted it

Output JSON with: rationalization_present (bool), severity (none/mild/moderate/severe), conclusion (what conclusion is being justified), reasons_given (what reasons are offered), temporal_order (did conclusion or reasons come first), reason_stability (do reasons change while conclusion stays fixed), falsifiability (what would change the conclusion), evidence_engagement (how is counter-evidence handled), direction_of_inference (conclusion→reasons or evidence→conclusion), recommendation (reasoning_genuine/mild_post_hoc/significant_rationalization/major_conclusion_first/reverse_inference_direction)."""

RATIONALIZATION_PROMPT = """Detect rationalization:

Reasoning: {reasoning}
Conclusion: {conclusion}
Evidence: {evidence}
Temporal order: {temporal}
Domain: {domain}
Context: {context}

Are reasons being constructed after the fact to justify a pre-existing conclusion? Return ONLY valid JSON."""


class RationalizationDetectService:
    """Detects rationalization — post-hoc justification of pre-existing conclusions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reasoning: str,
        *,
        conclusion: str = "",
        evidence: str = "",
        temporal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect rationalization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RATIONALIZATION_PROMPT.format(
                reasoning=reasoning,
                conclusion=conclusion or "Not specified",
                evidence=evidence or "Not specified",
                temporal=temporal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=RATIONALIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reasoning": reasoning[:200],
            "rationalization_present": data.get("rationalization_present", False),
            "severity": data.get("severity", ""),
            "conclusion": data.get("conclusion", ""),
            "reasons_given": data.get("reasons_given", ""),
            "temporal_order": data.get("temporal_order", ""),
            "reason_stability": data.get("reason_stability", ""),
            "falsifiability": data.get("falsifiability", ""),
            "direction_of_inference": data.get("direction_of_inference", ""),
            "recommendation": data.get("recommendation", ""),
        }
