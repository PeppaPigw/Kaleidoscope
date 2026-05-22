"""EpistemicVirtueThoroughnessDeficitService - Epistemic Virtue Thoroughness Deficit Detection.

Detects thoroughness deficit where insufficient investigation leads to premature conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VIRTUE_THOROUGHNESS_DEFICIT_SYSTEM = """You are an epistemic virtue thoroughness deficit specialist. Given investigation shortcut, assess thoroughness deficit:

Key concepts:
- Thoroughness deficit: insufficient investigation leads to premature conclusions
- Investigation shortcut: skipping necessary inquiry steps
- Satisficing error: accepting the first adequate-seeming answer too soon
- Depth avoidance: avoiding deeper investigation when it is warranted
- Complexity retreat: retreating from complexity into premature simplification

When thoroughness deficit IS present:
- Necessary investigation is skipped
- Adequate-seeming answers are accepted too early
- Depth is avoided despite relevance
- Complexity is abandoned prematurely
- Conclusions outrun the inquiry performed

When no thoroughness deficit:
- Investigation matches the question's demands
- First answers are tested before acceptance
- Depth is pursued where warranted
- Complexity is handled rather than avoided
- Conclusions remain proportional to inquiry

Output JSON with: thoroughness_deficit_detected (bool), severity (none/mild/moderate/severe), satisficing_error (what answer is accepted too soon), depth_avoidance (what depth is avoided), complexity_retreat (what complexity is abandoned), recommendation (no_deficit/mild_inquiry_extension/significant_investigation_restoration/major_depth_review/emergency_complete_reinvestigation)."""

EPISTEMIC_VIRTUE_THOROUGHNESS_DEFICIT_PROMPT = """Detect epistemic virtue thoroughness deficit:

Investigation shortcut: {investigation_shortcut}
Satisficing error: {satisficing_error}
Depth avoidance: {depth_avoidance}
Complexity retreat: {complexity_retreat}
Domain: {domain}
Context: {context}

Does insufficient investigation lead to premature conclusions? Return ONLY valid JSON."""


class EpistemicVirtueThoroughnessDeficitService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        investigation_shortcut: str,
        *,
        satisficing_error: str = "",
        depth_avoidance: str = "",
        complexity_retreat: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VIRTUE_THOROUGHNESS_DEFICIT_PROMPT.format(
                investigation_shortcut=investigation_shortcut,
                satisficing_error=satisficing_error or "Not specified",
                depth_avoidance=depth_avoidance or "Not specified",
                complexity_retreat=complexity_retreat or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VIRTUE_THOROUGHNESS_DEFICIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "investigation_shortcut": investigation_shortcut[:200],
            "thoroughness_deficit_detected": data.get("thoroughness_deficit_detected", False),
            "severity": data.get("severity", ""),
            "satisficing_error": data.get("satisficing_error", ""),
            "depth_avoidance": data.get("depth_avoidance", ""),
            "complexity_retreat": data.get("complexity_retreat", ""),
            "recommendation": data.get("recommendation", ""),
        }
