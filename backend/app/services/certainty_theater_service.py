"""CertaintyTheaterService — Certainty Theater Detection.

Detects certainty theater — performing confidence and certainty
to appear competent or authoritative when genuine uncertainty
exists. This suppresses important caveats and creates false
precision in communication.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CERTAINTY_THEATER_SYSTEM = """You are a certainty theater specialist. Given a communication, assess whether certainty is being performed rather than warranted:

Key concepts:
- Certainty theater: performing confidence beyond what evidence supports
- False precision: using specific numbers when ranges are appropriate
- Caveat suppression: hiding important uncertainties
- Authority performance: projecting certainty to maintain credibility
- Epistemic courage: willingness to express appropriate uncertainty
- Precision vs accuracy: precise statements can be inaccurate
- Confidence signaling: social pressure to appear certain

When certainty theater IS present:
- Definitive statements where hedging would be more honest
- Specific numbers without confidence intervals or ranges
- Important caveats omitted to appear more authoritative
- "Definitely" and "certainly" where "probably" or "likely" is warranted
- Predictions stated as facts
- Complexity hidden behind simple confident assertions
- Uncertainty acknowledged privately but not publicly

When certainty theater is NOT present:
- Confidence calibrated to evidence strength
- Appropriate hedging and qualification
- Uncertainty ranges provided where relevant
- Caveats included even when they reduce impact
- Distinction made between high and low confidence claims
- Complexity acknowledged rather than hidden
- Epistemic humility demonstrated without undermining credibility

Output JSON with: theater_present (bool), severity (none/mild/moderate/severe), claim (what is being stated with certainty), actual_uncertainty (what uncertainty exists), suppressed_caveats (what qualifications are missing), motivation (why certainty is being performed), recommendation (no_theater/mild_overconfidence/significant_certainty_theater/major_false_precision/add_appropriate_uncertainty)."""

CERTAINTY_THEATER_PROMPT = """Detect certainty theater:

Statement: {statement}
Evidence basis: {evidence}
Known uncertainties: {uncertainties}
Audience: {audience}
Domain: {domain}
Context: {context}

Is certainty being performed beyond what evidence warrants? Return ONLY valid JSON."""


class CertaintyTheaterService:
    """Detects certainty theater — performing confidence beyond evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        statement: str,
        *,
        evidence: str = "",
        uncertainties: str = "",
        audience: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect certainty theater."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CERTAINTY_THEATER_PROMPT.format(
                statement=statement,
                evidence=evidence or "Not specified",
                uncertainties=uncertainties or "Not specified",
                audience=audience or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CERTAINTY_THEATER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "statement": statement[:200],
            "theater_present": data.get("theater_present", False),
            "severity": data.get("severity", ""),
            "actual_uncertainty": data.get("actual_uncertainty", ""),
            "suppressed_caveats": data.get("suppressed_caveats", ""),
            "motivation": data.get("motivation", ""),
            "recommendation": data.get("recommendation", ""),
        }
