"""EpistemicLanguageDeflationService — Epistemic Language Deflation Detection.

Detects epistemic language deflation — deflating language to minimize
important findings and understate significance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LANGUAGE_DEFLATION_SYSTEM = """You are an epistemic language deflation specialist. Given deflating language to minimize findings, assess language deflation:

Key concepts:
- Epistemic language deflation: deflating language to minimize important findings
- Underclaiming: claiming less than evidence warrants
- Significance minimization: minimizing significance through language
- Hedging excess: excessive hedging beyond what uncertainty requires
- Impact understatement: understating impact through word choice
- Finding burial: burying findings in minimizing language
- Importance deflation: deflating importance through understatement

When epistemic language deflation IS present:
- Language deflated below evidence
- Underclaiming present
- Significance minimized
- Hedging excessive
- Impact understated
- Findings buried
- Importance deflated

When no language deflation:
- Language matches evidence
- Claims proportional
- Significance acknowledged
- Hedging appropriate
- Impact accurately stated
- Findings highlighted
- Importance recognized

Output JSON with: language_deflation_detected (bool), severity (none/mild/moderate/severe), underclaiming (what underclaimed), significance_minimization (what significance minimized), hedging_excess (what excessively hedged), impact_understatement (what impact understated), recommendation (no_language_deflation/mild_assertion_practice/significant_confidence_building/major_intensive_claim_calibration/emergency_complete_language_deflation)."""

EPISTEMIC_LANGUAGE_DEFLATION_PROMPT = """Detect epistemic language deflation:

Underclaiming: {underclaiming}
Significance minimization: {significance_minimization}
Hedging excess: {hedging_excess}
Impact understatement: {impact_understatement}
Domain: {domain}
Context: {context}

Is language being deflated to minimize important findings? Return ONLY valid JSON."""


class EpistemicLanguageDeflationService:
    """Detects epistemic language deflation — deflating language to minimize findings."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        underclaiming: str,
        *,
        significance_minimization: str = "",
        hedging_excess: str = "",
        impact_understatement: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic language deflation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LANGUAGE_DEFLATION_PROMPT.format(
                underclaiming=underclaiming,
                significance_minimization=significance_minimization or "Not specified",
                hedging_excess=hedging_excess or "Not specified",
                impact_understatement=impact_understatement or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LANGUAGE_DEFLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "underclaiming": underclaiming[:200],
            "language_deflation_detected": data.get("language_deflation_detected", False),
            "severity": data.get("severity", ""),
            "significance_minimization": data.get("significance_minimization", ""),
            "hedging_excess": data.get("hedging_excess", ""),
            "impact_understatement": data.get("impact_understatement", ""),
            "recommendation": data.get("recommendation", ""),
        }
