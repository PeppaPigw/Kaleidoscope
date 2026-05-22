"""EpistemicBadFaithService — Epistemic Bad Faith Detection.

Detects epistemic bad faith — engaging in discourse without genuine
commitment to truth, where the appearance of inquiry masks
indifference to accuracy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BAD_FAITH_SYSTEM = """You are an epistemic bad faith specialist. Given a discourse participation, assess whether engagement lacks genuine commitment to truth:

Key concepts:
- Epistemic bad faith: discourse without truth commitment
- Performative engagement: appearing to engage without caring about truth
- Truth indifference: indifferent to accuracy of claims
- Instrumental discourse: using discourse for non-truth goals
- Insincere inquiry: asking questions without wanting answers
- Bad faith argumentation: arguing without commitment to conclusions
- Discourse exploitation: exploiting discourse norms without honoring them

When epistemic bad faith IS present:
- Engagement without genuine commitment to truth
- Appearance of inquiry masking indifference
- Discourse used for non-truth goals
- Questions asked without wanting answers
- Arguments made without commitment to conclusions
- Discourse norms exploited without being honored
- Truth irrelevant to the participant's goals

When genuine engagement is present:
- Commitment to truth evident in behavior
- Inquiry genuinely seeking answers
- Discourse serving understanding
- Questions reflecting genuine curiosity
- Arguments reflecting genuine beliefs
- Discourse norms honored in practice
- Truth relevant to participant's goals

Output JSON with: bad_faith_present (bool), severity (none/mild/moderate/severe), discourse (what discourse occurs), engagement (how participant engages), truth_commitment (what commitment to truth exists), instrumental_goal (what non-truth goal is served), recommendation (genuine_engagement/mild_instrumentalism/significant_epistemic_bad_faith/major_truth_indifference/engage_with_genuine_truth_commitment)."""

EPISTEMIC_BAD_FAITH_PROMPT = """Detect epistemic bad faith:

Discourse: {discourse}
Engagement pattern: {engagement}
Truth commitment: {commitment}
Goals served: {goals}
Domain: {domain}
Context: {context}

Is discourse engagement lacking genuine commitment to truth? Return ONLY valid JSON."""


class EpistemicBadFaithService:
    """Detects epistemic bad faith — discourse without truth commitment."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        discourse: str,
        *,
        engagement: str = "",
        commitment: str = "",
        goals: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic bad faith."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BAD_FAITH_PROMPT.format(
                discourse=discourse,
                engagement=engagement or "Not specified",
                commitment=commitment or "Not specified",
                goals=goals or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BAD_FAITH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "discourse": discourse[:200],
            "bad_faith_present": data.get("bad_faith_present", False),
            "severity": data.get("severity", ""),
            "engagement": data.get("engagement", ""),
            "truth_commitment": data.get("truth_commitment", ""),
            "instrumental_goal": data.get("instrumental_goal", ""),
            "recommendation": data.get("recommendation", ""),
        }
