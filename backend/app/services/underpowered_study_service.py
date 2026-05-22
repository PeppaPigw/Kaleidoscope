"""UnderpoweredStudyService — Underpowered Study Detection.

Detects underpowered study conclusions — drawing strong conclusions
from studies with insufficient sample size to detect the effect
of interest. Low statistical power means high false negative rates
and inflated effect sizes among significant results.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

UNDERPOWERED_STUDY_SYSTEM = """You are an underpowered study specialist. Given a research claim, assess whether the study had sufficient statistical power:

Key concepts:
- Statistical power: probability of detecting a true effect
- Sample size: larger samples detect smaller effects
- Effect size: how large the real effect is
- Type II error: failing to detect a real effect (false negative)
- Winner's curse: significant results from underpowered studies overestimate effects
- Power analysis: calculating needed sample size before study
- Minimum detectable effect: smallest effect the study could find

When underpowered study IS likely:
- Small sample size relative to expected effect size
- No power analysis reported
- Non-significant results interpreted as "no effect"
- Wide confidence intervals suggesting imprecision
- Effect sizes much larger than meta-analytic estimates
- Subgroup analyses with tiny cell sizes
- "Trending toward significance" (p = 0.06-0.10)

When underpowered study is NOT likely:
- Power analysis conducted and sample size justified
- Large sample relative to effect size
- Narrow confidence intervals
- Effect sizes consistent with meta-analyses
- Pre-registered sample size achieved
- Non-significance acknowledged as inconclusive, not negative
- Bayesian analysis provides evidence for null

Output JSON with: underpowered_likely (bool), severity (none/mild/moderate/severe), sample_size (reported sample), expected_effect (what effect size is plausible), power_analysis (was power calculated), confidence_intervals (how wide are they), recommendation (no_power_concern/mild_underpowering/significant_underpowering/major_power_failure/increase_sample_size)."""

UNDERPOWERED_STUDY_PROMPT = """Detect underpowered study:

Claim: {claim}
Sample size: {sample_size}
Effect reported: {effect}
Power analysis: {power_analysis}
Domain: {domain}
Context: {context}

Does this draw strong conclusions from an insufficiently powered study? Return ONLY valid JSON."""


class UnderpoweredStudyService:
    """Detects underpowered study — conclusions from insufficient sample sizes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        sample_size: str = "",
        effect: str = "",
        power_analysis: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect underpowered study."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=UNDERPOWERED_STUDY_PROMPT.format(
                claim=claim,
                sample_size=sample_size or "Not specified",
                effect=effect or "Not specified",
                power_analysis=power_analysis or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=UNDERPOWERED_STUDY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "underpowered_likely": data.get("underpowered_likely", False),
            "severity": data.get("severity", ""),
            "sample_size": data.get("sample_size", ""),
            "expected_effect": data.get("expected_effect", ""),
            "power_analysis": data.get("power_analysis", ""),
            "recommendation": data.get("recommendation", ""),
        }
