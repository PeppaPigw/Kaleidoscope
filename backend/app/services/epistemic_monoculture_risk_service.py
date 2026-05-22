"""EpistemicMonocultureRiskService — Epistemic Monoculture Risk Detection.

Detects epistemic monoculture risk — single intellectual species
dominating, creating vulnerability to novel challenges.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MONOCULTURE_RISK_SYSTEM = """You are an epistemic monoculture risk specialist. Given an intellectual ecosystem, assess whether single-species dominance creates vulnerability:

Key concepts:
- Epistemic monoculture risk: single approach dominating creating vulnerability
- Diversity loss: loss of intellectual diversity
- Vulnerability: vulnerability to challenges the dominant approach cannot handle
- Resilience failure: lack of resilience from lack of alternatives
- Novel threat: novel challenges that monoculture cannot address
- Adaptation failure: inability to adapt due to lack of variety
- Systemic risk: risk affecting the entire system simultaneously

When monoculture risk IS present:
- Single intellectual approach dominating
- Loss of intellectual diversity
- Vulnerability to challenges the dominant approach cannot handle
- Lack of resilience from absence of alternatives
- Novel challenges that monoculture cannot address
- Inability to adapt due to lack of variety
- Risk of systemic failure affecting everything simultaneously

When healthy diversity is present:
- Multiple intellectual approaches coexisting
- Rich intellectual diversity maintained
- Resilience from multiple approaches available
- Alternatives available when one approach fails
- Ability to address novel challenges from diverse toolkit
- Adaptation possible through variety
- No systemic risk from single-point failure

Output JSON with: monoculture_risk (bool), severity (none/mild/moderate/severe), dominant (what dominates), diversity_lost (what diversity is lost), vulnerability (what vulnerability exists), novel_threat (what novel threats are unaddressable), recommendation (healthy_diversity/mild_dominance/significant_monoculture/major_systemic_risk/cultivate_diversity)."""

EPISTEMIC_MONOCULTURE_RISK_PROMPT = """Detect epistemic monoculture risk:

Dominant: {dominant}
Diversity lost: {diversity_lost}
Vulnerability: {vulnerability}
Novel threat: {novel_threat}
Domain: {domain}
Context: {context}

Is single-approach dominance creating vulnerability to novel challenges? Return ONLY valid JSON."""


class EpistemicMonocultureRiskService:
    """Detects epistemic monoculture risk — single-species vulnerability."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        dominant: str,
        *,
        diversity_lost: str = "",
        vulnerability: str = "",
        novel_threat: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic monoculture risk."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MONOCULTURE_RISK_PROMPT.format(
                dominant=dominant,
                diversity_lost=diversity_lost or "Not specified",
                vulnerability=vulnerability or "Not specified",
                novel_threat=novel_threat or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MONOCULTURE_RISK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "dominant": dominant[:200],
            "monoculture_risk": data.get("monoculture_risk", False),
            "severity": data.get("severity", ""),
            "diversity_lost": data.get("diversity_lost", ""),
            "vulnerability": data.get("vulnerability", ""),
            "novel_threat": data.get("novel_threat", ""),
            "recommendation": data.get("recommendation", ""),
        }
