"""EpistemicLanguageInflationService — Epistemic Language Inflation Detection.

Detects epistemic language inflation — inflating language beyond what
evidence supports, overclaiming through word choice.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LANGUAGE_INFLATION_SYSTEM = """You are an epistemic language inflation specialist. Given inflating language beyond evidence, assess language inflation:

Key concepts:
- Epistemic language inflation: inflating language beyond what evidence supports
- Overclaiming: claiming more than evidence warrants
- Certainty inflation: using certain language for uncertain findings
- Scope inflation: using broad language for narrow findings
- Impact inflation: inflating impact through language
- Significance inflation: inflating significance through word choice
- Generalization inflation: generalizing beyond data through language

When epistemic language inflation IS present:
- Language inflated beyond evidence
- Overclaiming present
- Certainty inflated
- Scope inflated
- Impact inflated
- Significance inflated
- Generalization inflated

When no language inflation:
- Language matches evidence
- Claims proportional
- Certainty calibrated
- Scope appropriate
- Impact accurately stated
- Significance proportional
- Generalization bounded

Output JSON with: language_inflation_detected (bool), severity (none/mild/moderate/severe), overclaiming (what overclaimed), certainty_inflation (what certainty inflated), scope_inflation (what scope inflated), significance_inflation (what significance inflated), recommendation (no_language_inflation/mild_calibration_practice/significant_language_deflation/major_intensive_precision_recovery/emergency_complete_language_inflation)."""

EPISTEMIC_LANGUAGE_INFLATION_PROMPT = """Detect epistemic language inflation:

Overclaiming: {overclaiming}
Certainty inflation: {certainty_inflation}
Scope inflation: {scope_inflation}
Significance inflation: {significance_inflation}
Domain: {domain}
Context: {context}

Is language being inflated beyond what evidence supports? Return ONLY valid JSON."""


class EpistemicLanguageInflationService:
    """Detects epistemic language inflation — inflating language beyond evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        overclaiming: str,
        *,
        certainty_inflation: str = "",
        scope_inflation: str = "",
        significance_inflation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic language inflation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LANGUAGE_INFLATION_PROMPT.format(
                overclaiming=overclaiming,
                certainty_inflation=certainty_inflation or "Not specified",
                scope_inflation=scope_inflation or "Not specified",
                significance_inflation=significance_inflation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LANGUAGE_INFLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "overclaiming": overclaiming[:200],
            "language_inflation_detected": data.get("language_inflation_detected", False),
            "severity": data.get("severity", ""),
            "certainty_inflation": data.get("certainty_inflation", ""),
            "scope_inflation": data.get("scope_inflation", ""),
            "significance_inflation": data.get("significance_inflation", ""),
            "recommendation": data.get("recommendation", ""),
        }
