"""PHackingService — P-Hacking Detection.

Detects p-hacking — manipulating data analysis (trying multiple
tests, excluding outliers, optional stopping) until a statistically
significant result appears, inflating false positive rates and
producing unreliable findings.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

P_HACKING_SYSTEM = """You are a p-hacking specialist. Given a research claim or analysis, assess whether statistical significance may have been achieved through questionable research practices:

Key concepts:
- P-hacking: manipulating analysis to achieve p < 0.05
- Multiple comparisons: testing many hypotheses increases false positives
- Optional stopping: stopping data collection when significance is reached
- Outlier exclusion: removing data points to change results
- Subgroup analysis: finding significance in post-hoc subgroups
- Garden of forking paths: many undisclosed analytical choices
- Pre-registration: declaring analysis plan before seeing data

When p-hacking IS likely:
- Many tests run but only significant ones reported
- Unusual sample sizes suggesting optional stopping
- Post-hoc subgroup analyses presented as primary findings
- Suspiciously many results at p = 0.04-0.05
- No pre-registration or deviation from pre-registered plan
- Multiple outcome measures with only some reported
- Flexible exclusion criteria that happen to produce significance

When p-hacking is NOT likely:
- Pre-registered analysis plan followed
- All tests reported (including non-significant)
- Correction for multiple comparisons applied
- Sample size determined a priori
- Replication confirms findings
- Effect sizes are large and robust to analytical choices
- Transparent reporting of all analytical decisions

Output JSON with: p_hacking_likely (bool), severity (none/mild/moderate/severe), indicators (what suggests p-hacking), multiple_tests (evidence of multiple testing), pre_registration (was analysis pre-registered), reporting (is reporting selective), recommendation (no_p_hacking_concern/mild_flexibility/significant_p_hacking_risk/major_analytical_manipulation/pre_register_and_correct)."""

P_HACKING_PROMPT = """Detect p-hacking:

Claim: {claim}
Analysis described: {analysis}
Sample details: {sample}
Reporting: {reporting}
Domain: {domain}
Context: {context}

Does this show signs of p-hacking or questionable research practices? Return ONLY valid JSON."""


class PHackingService:
    """Detects p-hacking — manipulating analysis for statistical significance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        analysis: str = "",
        sample: str = "",
        reporting: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect p-hacking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=P_HACKING_PROMPT.format(
                claim=claim,
                analysis=analysis or "Not specified",
                sample=sample or "Not specified",
                reporting=reporting or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=P_HACKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "p_hacking_likely": data.get("p_hacking_likely", False),
            "severity": data.get("severity", ""),
            "indicators": data.get("indicators", ""),
            "multiple_tests": data.get("multiple_tests", ""),
            "pre_registration": data.get("pre_registration", ""),
            "recommendation": data.get("recommendation", ""),
        }
