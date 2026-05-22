"""IllusionAsymmetricInsightService — Illusion of Asymmetric Insight Detection.

Detects the illusion of asymmetric insight — believing you
understand others better than they understand you. Pronin,
Kruger, Savitsky & Ross (2001). People believe they see
through others while remaining opaque themselves. "I know
what you're really thinking, but you don't know what I'm
really thinking." This creates communication failures and
overconfident social judgments.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ILLUSION_ASYMMETRIC_INSIGHT_SYSTEM = """You are an illusion of asymmetric insight specialist. Given a social judgment or interpersonal assessment, determine whether someone believes they understand others better than others understand them:

Key concepts (Pronin, Kruger, Savitsky & Ross, 2001):
- Asymmetric insight: "I see through you but you can't see through me"
- Naive realism interaction: "I see reality, you see your biases"
- Introspection illusion: privileged access to own mind = understanding
- Surface reading of others: judging others by behavior, self by intentions
- Group-level asymmetry: "we understand them better than they understand us"
- Overconfident social prediction: certainty about others' motivations
- Opacity assumption: believing own complexity is invisible to others

When the illusion IS present:
- "I know exactly why they did that" with high confidence
- Assuming others' behavior reveals their true nature while own doesn't
- "They don't really understand me/us"
- Confident predictions about others' motivations without verification
- Believing own group sees the other group clearly but not vice versa
- Dismissing others' self-reports as lacking self-awareness
- "I can tell what they're thinking" without evidence

When insight IS genuinely asymmetric:
- One party has significantly more information about the other
- Professional expertise in reading behavior (trained therapists)
- Clear evidence of one party's superior predictive accuracy
- Power dynamics that genuinely create information asymmetry
- Verified track record of accurate social prediction

Output JSON with: asymmetric_insight_present (bool), severity (none/mild/moderate/severe), situation (what social judgment is being made), claimed_insight (what understanding is claimed about others), actual_basis (what is the actual basis for the claim), reciprocal_insight (how well do others actually understand the person), overconfidence (how overconfident is the insight claim), verification (has the insight been verified), recommendation (insight_justified/mild_asymmetry_illusion/significant_overconfident_reading/major_asymmetric_insight_illusion/verify_social_predictions)."""

ILLUSION_ASYMMETRIC_INSIGHT_PROMPT = """Detect illusion of asymmetric insight:

Situation: {situation}
Claimed understanding: {claimed}
Evidence: {evidence}
Reciprocity: {reciprocity}
Domain: {domain}
Context: {context}

Does someone believe they understand others better than others understand them, without justification? Return ONLY valid JSON."""


class IllusionAsymmetricInsightService:
    """Detects illusion of asymmetric insight — believing you see through others but not vice versa."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        claimed: str = "",
        evidence: str = "",
        reciprocity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect illusion of asymmetric insight."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ILLUSION_ASYMMETRIC_INSIGHT_PROMPT.format(
                situation=situation,
                claimed=claimed or "Not specified",
                evidence=evidence or "Not specified",
                reciprocity=reciprocity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ILLUSION_ASYMMETRIC_INSIGHT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "asymmetric_insight_present": data.get("asymmetric_insight_present", False),
            "severity": data.get("severity", ""),
            "claimed_insight": data.get("claimed_insight", ""),
            "actual_basis": data.get("actual_basis", ""),
            "reciprocal_insight": data.get("reciprocal_insight", ""),
            "overconfidence": data.get("overconfidence", ""),
            "verification": data.get("verification", ""),
            "recommendation": data.get("recommendation", ""),
        }
