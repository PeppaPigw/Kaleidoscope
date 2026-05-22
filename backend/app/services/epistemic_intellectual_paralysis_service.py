"""EpistemicIntellectualParalysisService — Epistemic Intellectual Paralysis Detection.

Detects epistemic intellectual paralysis — paralysis from overwhelming
options or information preventing any action.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_PARALYSIS_SYSTEM = """You are an epistemic intellectual paralysis specialist. Given paralysis from overwhelming options, assess intellectual paralysis:

Key concepts:
- Epistemic intellectual paralysis: paralysis from overwhelming options
- Analysis paralysis: analyzing endlessly without deciding
- Information overwhelm: too much information preventing action
- Option overload: too many choices preventing any choice
- Perfectionism freeze: waiting for perfect information before acting
- Decision avoidance: avoiding decisions by seeking more information
- Infinite regress: always needing more before acting

When epistemic intellectual paralysis IS present:
- Paralysis from overwhelming options
- Analyzing endlessly without deciding
- Too much information preventing action
- Too many choices preventing choice
- Waiting for perfect information
- Avoiding decisions by seeking more
- Always needing more before acting

When no intellectual paralysis:
- Able to act with available information
- Analyzing then deciding
- Information enabling action
- Choosing from options
- Acting with imperfect information
- Making decisions
- Acting with sufficient information

Output JSON with: intellectual_paralysis_detected (bool), severity (none/mild/moderate/severe), analysis_paralysis (what analyzing endlessly), information_overwhelm (what too much information about), option_overload (what too many choices about), perfectionism_freeze (what waiting for perfect information about), recommendation (no_intellectual_paralysis/mild_action_practice/significant_decision_recovery/major_intensive_agency_work/emergency_complete_intellectual_paralysis)."""

EPISTEMIC_INTELLECTUAL_PARALYSIS_PROMPT = """Detect epistemic intellectual paralysis:

Analysis paralysis: {analysis_paralysis}
Information overwhelm: {information_overwhelm}
Option overload: {option_overload}
Perfectionism freeze: {perfectionism_freeze}
Domain: {domain}
Context: {context}

Is there paralysis from overwhelming options or information preventing any action? Return ONLY valid JSON."""


class EpistemicIntellectualParalysisService:
    """Detects epistemic intellectual paralysis — paralysis from overwhelming options."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        analysis_paralysis: str,
        *,
        information_overwhelm: str = "",
        option_overload: str = "",
        perfectionism_freeze: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual paralysis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_PARALYSIS_PROMPT.format(
                analysis_paralysis=analysis_paralysis,
                information_overwhelm=information_overwhelm or "Not specified",
                option_overload=option_overload or "Not specified",
                perfectionism_freeze=perfectionism_freeze or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_PARALYSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analysis_paralysis": analysis_paralysis[:200],
            "intellectual_paralysis_detected": data.get("intellectual_paralysis_detected", False),
            "severity": data.get("severity", ""),
            "information_overwhelm": data.get("information_overwhelm", ""),
            "option_overload": data.get("option_overload", ""),
            "perfectionism_freeze": data.get("perfectionism_freeze", ""),
            "recommendation": data.get("recommendation", ""),
        }
