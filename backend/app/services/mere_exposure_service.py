"""MereExposureService — Mere Exposure Effect Detection.

Detects mere exposure effect — developing preference for things
simply because they are familiar. Zajonc (1968). Familiarity
breeds liking, not contempt. Leads to preferring the known over
the objectively better, resistance to change, and status quo
bias reinforcement.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MERE_EXPOSURE_SYSTEM = """You are a mere exposure effect specialist. Given a preference or choice, assess whether familiarity rather than objective quality is driving the preference:

Key concepts (Zajonc, 1968):
- Mere exposure effect: repeated exposure increases liking
- Familiarity preference: choosing the known over the unknown
- Processing fluency: familiar things are easier to process, which feels good
- Perceptual fluency: ease of perception mistaken for quality
- Status quo reinforcement: familiarity makes current state feel "right"
- Novelty aversion: avoiding the unfamiliar regardless of merit
- Exposure-attitude link: more exposure → more positive attitude (up to a point)

When mere exposure IS driving preference:
- Choosing familiar options without evaluating alternatives
- "I prefer X" when the only advantage is familiarity
- Resistance to new tools/methods despite objective superiority
- Brand loyalty without quality justification
- Preferring familiar faces, places, or processes without reason
- "We've always done it this way" as the primary justification

When the preference IS justified:
- The familiar option is genuinely superior on objective criteria
- Familiarity provides real benefits (lower learning curve, proven reliability)
- The switching costs genuinely outweigh the benefits of change
- The person has evaluated alternatives and chosen the familiar for good reasons
- Experience with the familiar has revealed genuine advantages

Output JSON with: mere_exposure_present (bool), severity (none/mild/moderate/severe), preference (what is being preferred), familiarity_source (how did familiarity develop?), alternatives_evaluated (bool — were alternatives genuinely considered?), objective_comparison (how does the familiar compare objectively?), switching_cost (what would switching cost?), switching_benefit (what would switching gain?), processing_fluency (is ease of processing driving the preference?), novelty_aversion (bool — is unfamiliarity being penalized?), recommendation (preference_justified/mild_familiarity_bias/significant_exposure_effect/major_novelty_aversion/evaluate_alternatives_objectively)."""

MERE_EXPOSURE_PROMPT = """Detect mere exposure effect:

Preference: {preference}
Familiarity: {familiarity}
Alternatives: {alternatives}
Justification: {justification}
Domain: {domain}
Context: {context}

Is familiarity rather than quality driving this preference? Return ONLY valid JSON."""


class MereExposureService:
    """Detects mere exposure effect — preferring things simply because they're familiar."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        preference: str,
        *,
        familiarity: str = "",
        alternatives: str = "",
        justification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect mere exposure effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MERE_EXPOSURE_PROMPT.format(
                preference=preference,
                familiarity=familiarity or "Not specified",
                alternatives=alternatives or "Not specified",
                justification=justification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MERE_EXPOSURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "preference": preference[:200],
            "mere_exposure_present": data.get("mere_exposure_present", False),
            "severity": data.get("severity", ""),
            "familiarity_source": data.get("familiarity_source", ""),
            "alternatives_evaluated": data.get("alternatives_evaluated", True),
            "objective_comparison": data.get("objective_comparison", ""),
            "switching_cost": data.get("switching_cost", ""),
            "switching_benefit": data.get("switching_benefit", ""),
            "processing_fluency": data.get("processing_fluency", ""),
            "novelty_aversion": data.get("novelty_aversion", False),
            "recommendation": data.get("recommendation", ""),
        }
