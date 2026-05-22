"""InformationOverloadParalysisService — Information Overload Paralysis Detection.

Detects information overload paralysis — too much information
preventing any decision or action, where abundance of data
creates inability to process, prioritize, or act.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INFORMATION_OVERLOAD_PARALYSIS_SYSTEM = """You are an information overload paralysis specialist. Given a decision situation, assess whether information abundance is causing paralysis:

Key concepts:
- Information overload paralysis: too much info preventing action
- Analysis paralysis: endless analysis without decision
- Data abundance inaction: more data leading to less action
- Decision avoidance: using need for more info to avoid deciding
- Perfectionism trap: seeking complete info before any action
- Signal drowning: signal lost in noise abundance
- Prioritization failure: inability to rank information

When information overload paralysis IS present:
- Abundance of information preventing decision
- Endless analysis without reaching conclusion
- More data sought to avoid deciding
- Complete information demanded before any action
- Signal lost in noise
- Inability to prioritize among information
- Information gathering substituting for action

When thorough analysis is appropriate:
- Information gathering proportionate to stakes
- Analysis bounded by decision timeline
- Sufficient information identified and sought
- Signal distinguished from noise
- Prioritization among information sources
- Analysis leads to decision not avoidance
- Information gathering serves action

Output JSON with: paralysis_present (bool), severity (none/mild/moderate/severe), situation (what situation is analyzed), information_volume (how much info exists), decision_needed (what decision is needed), blocking_factor (what prevents decision), recommendation (appropriate_thoroughness/mild_over_analysis/significant_overload_paralysis/major_decision_avoidance/bound_analysis_and_decide)."""

INFORMATION_OVERLOAD_PARALYSIS_PROMPT = """Detect information overload paralysis:

Situation: {situation}
Information available: {information}
Decision needed: {decision}
Action taken: {action}
Domain: {domain}
Context: {context}

Is information abundance preventing decision or action? Return ONLY valid JSON."""


class InformationOverloadParalysisService:
    """Detects information overload paralysis — too much info preventing action."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        information: str = "",
        decision: str = "",
        action: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect information overload paralysis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INFORMATION_OVERLOAD_PARALYSIS_PROMPT.format(
                situation=situation,
                information=information or "Not specified",
                decision=decision or "Not specified",
                action=action or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INFORMATION_OVERLOAD_PARALYSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "paralysis_present": data.get("paralysis_present", False),
            "severity": data.get("severity", ""),
            "information_volume": data.get("information_volume", ""),
            "decision_needed": data.get("decision_needed", ""),
            "blocking_factor": data.get("blocking_factor", ""),
            "recommendation": data.get("recommendation", ""),
        }
