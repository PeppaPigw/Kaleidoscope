"""EpistemicDecisionAnalysisParalysisService - Analysis Paralysis Detection.

Detects analysis paralysis where excessive analysis prevents decision-making.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DECISION_ANALYSIS_PARALYSIS_SYSTEM = """You are an epistemic decision analysis paralysis specialist. Given decision contexts, assess whether excessive analysis prevents action:

Key concepts:
- Analysis paralysis: inability to decide due to overthinking or information overload
- Information addiction: seeking more data when sufficient exists
- Perfect information fallacy: waiting for certainty that cannot be achieved
- Decision avoidance: using analysis as excuse to avoid commitment

When analysis paralysis IS present:
- Decision delayed despite sufficient information
- More analysis sought without clear benefit
- Perfect information demanded
- Analysis used to avoid commitment
- Opportunity costs ignored

When no analysis paralysis:
- Analysis proportionate to stakes
- Decision made with available information
- Uncertainty acknowledged and managed
- Commitment made appropriately
- Opportunity costs considered

Output JSON with: analysis_paralysis_detected (bool), severity (none/mild/moderate/severe), information_addiction (what information addiction), perfect_information_fallacy (what perfection demanded), decision_avoidance (what decision avoided), recommendation (no_analysis_paralysis/mild_decision_prompt/significant_action_needed/major_commitment_reconstruction/emergency_complete_analysis_paralysis)."""

EPISTEMIC_DECISION_ANALYSIS_PARALYSIS_PROMPT = """Detect epistemic decision analysis paralysis:

Decision context: {decision_context}
Information addiction: {information_addiction}
Perfect information fallacy: {perfect_information_fallacy}
Decision avoidance: {decision_avoidance}
Domain: {domain}
Context: {context}

Is excessive analysis preventing decision-making? Return ONLY valid JSON."""


class EpistemicDecisionAnalysisParalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision_context: str,
        *,
        information_addiction: str = "",
        perfect_information_fallacy: str = "",
        decision_avoidance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DECISION_ANALYSIS_PARALYSIS_PROMPT.format(
                decision_context=decision_context,
                information_addiction=information_addiction or "Not specified",
                perfect_information_fallacy=perfect_information_fallacy or "Not specified",
                decision_avoidance=decision_avoidance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DECISION_ANALYSIS_PARALYSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision_context": decision_context[:200],
            "analysis_paralysis_detected": data.get("analysis_paralysis_detected", False),
            "severity": data.get("severity", ""),
            "information_addiction": data.get("information_addiction", ""),
            "perfect_information_fallacy": data.get("perfect_information_fallacy", ""),
            "decision_avoidance": data.get("decision_avoidance", ""),
            "recommendation": data.get("recommendation", ""),
        }
