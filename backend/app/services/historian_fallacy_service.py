"""HistorianFallacyService — Historian's Fallacy Detection.

Detects historian's fallacy — judging past decisions using information
that was not available to the decision-makers at the time. Fischer (1970).
Assumes historical actors had access to knowledge that only became
available later.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HISTORIAN_FALLACY_SYSTEM = """You are a historian's fallacy specialist. Given a judgment about a past decision, assess whether it uses information unavailable at the time:

Key concepts (Fischer, 1970):
- Historian's fallacy: judging past decisions with present knowledge
- Hindsight bias: "they should have known" when they couldn't have
- Information asymmetry: what we know now vs what they knew then
- Counterfactual reasoning: what was reasonable given available information
- Temporal context: the information environment of the decision
- Outcome bias: judging decisions by outcomes rather than process
- Anachronistic judgment: applying later knowledge to earlier decisions

When historian's fallacy IS present:
- "They should have seen X coming" when X was not predictable
- Judging decisions using information discovered after the fact
- "Obviously they should have done Y" when Y wasn't obvious then
- Assuming decision-makers had access to data that didn't exist yet
- Criticizing choices without considering the information available
- Using outcomes to judge the quality of decisions made under uncertainty
- "Any reasonable person would have..." without considering temporal context

When retrospective judgment IS appropriate:
- The information WAS available at the time and was ignored
- The judgment accounts for what was knowable then
- Warning signs existed and were documented at the time
- The criticism is about process, not just outcomes
- Contemporary critics raised the same concerns
- The decision violated principles understood at the time
- The judgment explicitly considers the information environment

Output JSON with: historian_fallacy_present (bool), severity (none/mild/moderate/severe), decision (what past decision is judged), judgment (what judgment is made), information_used (what information informs the judgment), availability (was this information available at the time), temporal_context (what was known then), recommendation (judgment_appropriate/mild_hindsight/significant_historian_fallacy/major_anachronistic_judgment/consider_information_available_at_time)."""

HISTORIAN_FALLACY_PROMPT = """Detect historian's fallacy:

Decision judged: {decision}
Judgment: {judgment}
Information used: {information}
Time period: {time_period}
Domain: {domain}
Context: {context}

Is this judgment using information that wasn't available when the decision was made? Return ONLY valid JSON."""


class HistorianFallacyService:
    """Detects historian's fallacy — judging past decisions with present knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        judgment: str = "",
        information: str = "",
        time_period: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect historian's fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HISTORIAN_FALLACY_PROMPT.format(
                decision=decision,
                judgment=judgment or "Not specified",
                information=information or "Not specified",
                time_period=time_period or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HISTORIAN_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "historian_fallacy_present": data.get("historian_fallacy_present", False),
            "severity": data.get("severity", ""),
            "information_used": data.get("information_used", ""),
            "availability": data.get("availability", ""),
            "temporal_context": data.get("temporal_context", ""),
            "recommendation": data.get("recommendation", ""),
        }
