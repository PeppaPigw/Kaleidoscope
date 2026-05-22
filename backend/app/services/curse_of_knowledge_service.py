"""CurseOfKnowledgeService — Curse of Knowledge Detection.

Detects the curse of knowledge — the inability to think from the
perspective of someone who doesn't know what you know. Once you
know something, you can't un-know it, making it hard to
communicate with or predict the behavior of the uninformed.
Camerer, Loewenstein & Weber (1989).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CURSE_SYSTEM = """You are a curse of knowledge specialist. Given a communication or prediction, assess whether the curse of knowledge is creating a gap between the informed and uninformed perspective:

Key concepts (Camerer, Loewenstein & Weber, 1989):
- Curse of knowledge: once you know something, you can't imagine not knowing it
- Hindsight bias component: "it was obvious" (only because you know the answer)
- Expert blind spot: experts forget what it's like to be a beginner
- Illusion of transparency: overestimating how well others understand you
- Empathy gap: difficulty modeling the mental state of the uninformed
- Tappers and listeners: tappers think listeners can identify the song (they can't)

When the curse IS present:
- Expert communication assumes knowledge the audience doesn't have
- Predictions assume others have information they don't
- "It's obvious" or "everyone knows" about non-obvious things
- Instructions skip steps that seem unnecessary to the expert
- Surprise that others don't understand or can't predict outcomes

When communication IS appropriately calibrated:
- The audience genuinely has the assumed background
- Jargon is defined or the context makes it clear
- The communicator has tested comprehension
- Predictions account for information asymmetry

Output JSON with: curse_of_knowledge_present (bool), severity (none/mild/moderate/severe), knowledge_assumed (what the communicator assumes the audience knows), knowledge_actual (what the audience likely knows), gap_size (how large the knowledge gap is), expert_blind_spot (bool — forgetting what it's like to not know?), illusion_of_transparency (bool — overestimating how clear the communication is?), jargon_unexplained (list of terms/concepts used without explanation), steps_skipped (what logical steps are assumed but not stated), audience_model (who the actual audience is), audience_assumed (who the communicator thinks the audience is), comprehension_tested (bool — has understanding been verified?), prediction_error (if predicting behavior, what information asymmetry is ignored), empathy_gap (what the communicator can't imagine not knowing), recommendation (communication_calibrated/mild_assumption_gap/significant_curse/major_knowledge_gap/redesign_for_audience)."""

CURSE_PROMPT = """Detect curse of knowledge:

Communication/Prediction: {communication}
Communicator expertise: {expertise}
Audience: {audience}
Assumed knowledge: {assumed_knowledge}
Domain: {domain}
Context: {context}

Is the curse of knowledge creating a comprehension gap? Return ONLY valid JSON."""


class CurseOfKnowledgeService:
    """Detects curse of knowledge — inability to think from uninformed perspective."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        communication: str,
        *,
        expertise: str = "",
        audience: str = "",
        assumed_knowledge: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect curse of knowledge."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CURSE_PROMPT.format(
                communication=communication,
                expertise=expertise or "Not specified",
                audience=audience or "Not specified",
                assumed_knowledge=assumed_knowledge or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CURSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "communication": communication[:200],
            "curse_of_knowledge_present": data.get("curse_of_knowledge_present", False),
            "severity": data.get("severity", ""),
            "knowledge_assumed": data.get("knowledge_assumed", ""),
            "knowledge_actual": data.get("knowledge_actual", ""),
            "gap_size": data.get("gap_size", ""),
            "expert_blind_spot": data.get("expert_blind_spot", False),
            "illusion_of_transparency": data.get("illusion_of_transparency", False),
            "jargon_unexplained": data.get("jargon_unexplained", []),
            "steps_skipped": data.get("steps_skipped", ""),
            "audience_model": data.get("audience_model", ""),
            "audience_assumed": data.get("audience_assumed", ""),
            "comprehension_tested": data.get("comprehension_tested", False),
            "prediction_error": data.get("prediction_error", ""),
            "empathy_gap": data.get("empathy_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
