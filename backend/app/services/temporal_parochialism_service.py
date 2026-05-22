"""TemporalParochialismService — Temporal Parochialism Detection.

Detects temporal parochialism — assuming current conditions, values,
or frameworks are universal across time, inability to think outside
one's temporal context.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TEMPORAL_PAROCHIALISM_SYSTEM = """You are a temporal parochialism specialist. Given an analysis or claim, assess whether it assumes current conditions are universal across time:

Key concepts:
- Temporal parochialism: treating present as universal
- Presentism: judging past by present standards
- Chronocentrism: assuming current era is special or normative
- Historical contingency blindness: missing that things could be otherwise
- Temporal provincialism: inability to think outside current moment
- Future blindness: assuming current trends continue indefinitely
- Era-specific assumptions: treating temporary conditions as permanent

When temporal parochialism IS present:
- Current conditions assumed to be permanent or universal
- Present values projected onto all of history
- Current frameworks treated as the only possible ones
- Temporary conditions treated as natural laws
- Historical contingency ignored
- Future assumed to resemble present
- Era-specific assumptions treated as timeless truths

When present-focused analysis is appropriate:
- Current conditions acknowledged as historically specific
- Temporal limitations of analysis stated
- Historical contingency recognized
- Present used as starting point, not universal frame
- Awareness of how conditions have changed
- Future uncertainty acknowledged
- Era-specific nature of claims noted

Output JSON with: parochialism_present (bool), severity (none/mild/moderate/severe), claim (what is claimed), temporal_assumption (what temporal assumption is made), historical_variation (how conditions have varied), contingency (what is contingent not permanent), recommendation (appropriate_present_focus/mild_temporal_assumption/significant_parochialism/major_chronocentrism/acknowledge_temporal_contingency)."""

TEMPORAL_PAROCHIALISM_PROMPT = """Detect temporal parochialism:

Analysis: {analysis}
Time frame assumed: {timeframe}
Historical variation: {variation}
Contingency: {contingency}
Domain: {domain}
Context: {context}

Are current conditions being assumed universal across time? Return ONLY valid JSON."""


class TemporalParochialismService:
    """Detects temporal parochialism — treating present as universal across time."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        analysis: str,
        *,
        timeframe: str = "",
        variation: str = "",
        contingency: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect temporal parochialism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TEMPORAL_PAROCHIALISM_PROMPT.format(
                analysis=analysis,
                timeframe=timeframe or "Not specified",
                variation=variation or "Not specified",
                contingency=contingency or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TEMPORAL_PAROCHIALISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analysis": analysis[:200],
            "parochialism_present": data.get("parochialism_present", False),
            "severity": data.get("severity", ""),
            "temporal_assumption": data.get("temporal_assumption", ""),
            "historical_variation": data.get("historical_variation", ""),
            "contingency": data.get("contingency", ""),
            "recommendation": data.get("recommendation", ""),
        }
