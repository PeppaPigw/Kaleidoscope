"""NirvanaFallacyAsymmetryService — Nirvana Fallacy Asymmetry Detection.

Detects nirvana fallacy asymmetry — comparing a real-world proposal
to an idealized alternative that doesn't exist, while ignoring the
flaws of the actual alternative. Demsetz (1969). The "grass is
greener" error applied to policy and decision-making: comparing
imperfect reality to perfect theory.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NIRVANA_FALLACY_SYSTEM = """You are a nirvana fallacy asymmetry specialist. Given a comparison between options, assess whether a real option is being unfairly compared to an idealized alternative:

Key concepts (Demsetz, 1969):
- Nirvana fallacy: comparing real to ideal rather than real to real
- Demsetz critique: comparing imperfect markets to perfect government (or vice versa)
- Comparative institution analysis: compare real institutions to real institutions
- Grass is greener: the unchosen option appears flawless because untested
- Utopian benchmark: measuring against a standard nothing could achieve
- Implementation gap: ignoring that the ideal would degrade in practice
- Asymmetric realism: one option analyzed realistically, other idealistically

When nirvana fallacy IS present:
- Comparing a real system's flaws to a theoretical system's design
- "The market fails here, so government should do it" (without analyzing government failure)
- "Government fails here, so the market should do it" (without analyzing market failure)
- Comparing actual implementation to theoretical specification
- Ignoring implementation costs and degradation of the alternative
- One option judged by its worst cases, other by its best-case theory
- "If only we had X" where X has never been tested at scale

When idealized comparison IS appropriate:
- The ideal is achievable and has been demonstrated elsewhere
- The comparison explicitly acknowledges implementation challenges
- Both options are analyzed with equal realism
- The ideal serves as a direction, not a benchmark for rejection
- Transaction costs and implementation are factored in
- The comparison is between two real implementations

Output JSON with: nirvana_fallacy_present (bool), severity (none/mild/moderate/severe), comparison (what is being compared), real_option (the option analyzed realistically), ideal_option (the option analyzed idealistically), asymmetry (how realism differs between options), implementation_gap (what would degrade in practice), recommendation (comparison_appropriate/mild_idealization/significant_nirvana_fallacy/major_utopian_benchmark/compare_real_to_real)."""

NIRVANA_FALLACY_PROMPT = """Detect nirvana fallacy asymmetry:

Comparison: {comparison}
Real option: {real_option}
Ideal option: {ideal_option}
Analysis: {analysis}
Domain: {domain}
Context: {context}

Is a real option being unfairly compared to an idealized alternative? Return ONLY valid JSON."""


class NirvanaFallacyAsymmetryService:
    """Detects nirvana fallacy — comparing real to ideal unfairly."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        comparison: str,
        *,
        real_option: str = "",
        ideal_option: str = "",
        analysis: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect nirvana fallacy asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NIRVANA_FALLACY_PROMPT.format(
                comparison=comparison,
                real_option=real_option or "Not specified",
                ideal_option=ideal_option or "Not specified",
                analysis=analysis or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NIRVANA_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "comparison": comparison[:200],
            "nirvana_fallacy_present": data.get("nirvana_fallacy_present", False),
            "severity": data.get("severity", ""),
            "real_option": data.get("real_option", ""),
            "ideal_option": data.get("ideal_option", ""),
            "asymmetry": data.get("asymmetry", ""),
            "implementation_gap": data.get("implementation_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
