"""MotivatedNumeracyService — Motivated Numeracy Detection.

Detects motivated numeracy — using quantitative skills
selectively to support preferred conclusions while failing
to apply them to unwelcome data. Kahan et al. (2017).
Numerate people are BETTER at finding flaws in data that
contradicts their beliefs and WORSE at finding flaws in
data that supports them. Intelligence weaponized for bias.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MOTIVATED_NUMERACY_SYSTEM = """You are a motivated numeracy specialist. Given a quantitative analysis or data interpretation, assess whether numerical skills are being applied selectively based on whether conclusions are welcome:

Key concepts (Kahan et al., 2017):
- Motivated numeracy: selective application of quantitative skills
- Identity-protective cognition: using intelligence to defend beliefs
- Asymmetric scrutiny: more critical of unwelcome data
- Sophistication effect: smarter people are better at motivated reasoning
- Selective skepticism: questioning methodology only when results are unwelcome
- Confirmation bias amplified: numeracy makes confirmation bias more effective
- Myside bias: applying different standards to own-side vs other-side evidence

When motivated numeracy IS present:
- Finding methodological flaws only in studies with unwelcome results
- Accepting favorable statistics uncritically while scrutinizing unfavorable ones
- Using quantitative sophistication to dismiss inconvenient data
- "The sample size is too small" only for studies one disagrees with
- Sophisticated arguments for why unwelcome data doesn't apply
- Applying different statistical standards based on conclusion
- "Correlation isn't causation" selectively

When the analysis IS even-handed:
- Same standards applied regardless of conclusion
- Methodological criticism is consistent across studies
- The person acknowledges strong evidence even when unwelcome
- Statistical reasoning is applied uniformly
- The person can articulate what evidence would change their mind

Output JSON with: motivated_numeracy_present (bool), severity (none/mild/moderate/severe), analysis (what analysis is being performed), welcome_data (how is welcome data being treated), unwelcome_data (how is unwelcome data being treated), asymmetry (what asymmetry in scrutiny exists), sophistication_level (how numerate is the person), identity_stake (what identity is being protected), recommendation (analysis_even_handed/mild_asymmetry/significant_selective_scrutiny/major_motivated_numeracy/apply_uniform_standards)."""

MOTIVATED_NUMERACY_PROMPT = """Detect motivated numeracy:

Analysis: {analysis}
Data treatment: {treatment}
Standards applied: {standards}
Stakes: {stakes}
Domain: {domain}
Context: {context}

Are quantitative skills being applied selectively based on whether conclusions are welcome? Return ONLY valid JSON."""


class MotivatedNumeracyService:
    """Detects motivated numeracy — selective application of quantitative skills."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        analysis: str,
        *,
        treatment: str = "",
        standards: str = "",
        stakes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect motivated numeracy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MOTIVATED_NUMERACY_PROMPT.format(
                analysis=analysis,
                treatment=treatment or "Not specified",
                standards=standards or "Not specified",
                stakes=stakes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MOTIVATED_NUMERACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analysis": analysis[:200],
            "motivated_numeracy_present": data.get("motivated_numeracy_present", False),
            "severity": data.get("severity", ""),
            "welcome_data": data.get("welcome_data", ""),
            "unwelcome_data": data.get("unwelcome_data", ""),
            "asymmetry": data.get("asymmetry", ""),
            "sophistication_level": data.get("sophistication_level", ""),
            "identity_stake": data.get("identity_stake", ""),
            "recommendation": data.get("recommendation", ""),
        }
