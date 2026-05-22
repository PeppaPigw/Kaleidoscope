"""PresentismImpositionService — Presentism Imposition Detection.

Detects presentism imposition — judging past decisions, beliefs, or
actions by present knowledge, values, or standards that were not
available or applicable at the time.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PRESENTISM_IMPOSITION_SYSTEM = """You are a presentism imposition specialist. Given a judgment about the past, assess whether present standards are being inappropriately imposed:

Key concepts:
- Presentism imposition: judging past by present standards
- Anachronistic evaluation: applying current knowledge to past
- Value projection: projecting current values backward
- Knowledge asymmetry: judging by what we know now
- Context erasure: ignoring historical context
- Standards anachronism: applying current standards to past
- Temporal arrogance: assuming present superiority

When presentism imposition IS present:
- Past judged by knowledge unavailable at the time
- Current values imposed on different historical context
- Historical actors evaluated by standards they couldn't know
- Context of past decisions ignored
- Present knowledge treated as if always available
- Current standards assumed to be timeless
- Historical complexity reduced by present perspective

When present-informed analysis is appropriate:
- Historical context acknowledged and respected
- Knowledge available at the time identified
- Standards of the era considered
- Present perspective explicitly marked as retrospective
- Lessons drawn without condemning past actors
- Evolution of understanding traced
- Both past and present perspectives held

Output JSON with: presentism_present (bool), severity (none/mild/moderate/severe), judgment (what judgment is made), past_context (what context is ignored), present_standard (what present standard is imposed), available_knowledge (what was known at the time), recommendation (appropriate_retrospective_analysis/mild_presentism/significant_presentism_imposition/major_anachronistic_judgment/respect_historical_context)."""

PRESENTISM_IMPOSITION_PROMPT = """Detect presentism imposition:

Judgment: {judgment}
Historical period: {period}
Context of the time: {past_context}
Present standard applied: {standard}
Domain: {domain}
Context: {context}

Are present standards being inappropriately imposed on past decisions? Return ONLY valid JSON."""


class PresentismImpositionService:
    """Detects presentism imposition — judging past by present standards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        period: str = "",
        past_context: str = "",
        standard: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect presentism imposition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PRESENTISM_IMPOSITION_PROMPT.format(
                judgment=judgment,
                period=period or "Not specified",
                past_context=past_context or "Not specified",
                standard=standard or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PRESENTISM_IMPOSITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "presentism_present": data.get("presentism_present", False),
            "severity": data.get("severity", ""),
            "past_context": data.get("past_context", ""),
            "present_standard": data.get("present_standard", ""),
            "available_knowledge": data.get("available_knowledge", ""),
            "recommendation": data.get("recommendation", ""),
        }
