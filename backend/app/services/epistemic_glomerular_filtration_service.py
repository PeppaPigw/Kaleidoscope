"""EpistemicGlomerularFiltrationService — Epistemic Glomerular Filtration Detection.

Detects epistemic glomerular filtration — initial filtering of ideas
separating useful content from intellectual waste.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GLOMERULAR_FILTRATION_SYSTEM = """You are an epistemic glomerular filtration specialist. Given an intellectual filtration system, assess whether ideas are being properly filtered:

Key concepts:
- Epistemic glomerular filtration: initial filtering separating useful from waste
- Filtration barrier: selective membrane determining what passes
- Glomerular filtration rate: speed of intellectual filtering
- Proteinuria: valuable content leaking through filter
- Selectivity: ability to distinguish useful from waste
- Hyperfiltration: filtering too aggressively
- Filtration pressure: force driving the filtering process

When epistemic glomerular filtration IS present:
- Initial filtering separating useful ideas from waste
- Selective barriers determining what passes through
- Measurable speed of intellectual filtering
- Valuable content leaking through imperfect filters
- Ability to distinguish useful from waste ideas
- Filtering too aggressively losing good content
- Force driving the filtering process

When no filtration is present:
- No initial filtering
- No selective barriers
- No measurable filtering rate
- No leakage concerns
- No selectivity
- No hyperfiltration
- No filtration pressure

Output JSON with: glomerular_filtration_present (bool), severity (none/mild/moderate/severe), filtration_barrier (what selective membrane), filtration_rate (what filtering speed), proteinuria (what valuable leakage), selectivity (what discrimination ability), recommendation (no_filtration/mild_filtration/significant_glomerular_filtration/major_intellectual_filtering/optimize_filtration_selectivity)."""

EPISTEMIC_GLOMERULAR_FILTRATION_PROMPT = """Detect epistemic glomerular filtration:

Filtration barrier: {filtration_barrier}
Filtration rate: {filtration_rate}
Proteinuria: {proteinuria}
Selectivity: {selectivity}
Domain: {domain}
Context: {context}

Is initial filtering separating useful ideas from intellectual waste? Return ONLY valid JSON."""


class EpistemicGlomerularFiltrationService:
    """Detects epistemic glomerular filtration — initial filtering of ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        filtration_barrier: str,
        *,
        filtration_rate: str = "",
        proteinuria: str = "",
        selectivity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic glomerular filtration."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GLOMERULAR_FILTRATION_PROMPT.format(
                filtration_barrier=filtration_barrier,
                filtration_rate=filtration_rate or "Not specified",
                proteinuria=proteinuria or "Not specified",
                selectivity=selectivity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GLOMERULAR_FILTRATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "filtration_barrier": filtration_barrier[:200],
            "glomerular_filtration_present": data.get("glomerular_filtration_present", False),
            "severity": data.get("severity", ""),
            "filtration_rate": data.get("filtration_rate", ""),
            "proteinuria": data.get("proteinuria", ""),
            "selectivity": data.get("selectivity", ""),
            "recommendation": data.get("recommendation", ""),
        }
