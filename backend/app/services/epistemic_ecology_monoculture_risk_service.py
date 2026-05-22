"""EpistemicEcologyMonocultureRiskService - Epistemic Monoculture Risk Detection.

Detects epistemic monoculture where lack of intellectual diversity creates systemic risk.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ECOLOGY_MONOCULTURE_RISK_SYSTEM = """You are an epistemic ecology monoculture risk specialist. Given viewpoint homogeneity, assess whether lack of intellectual diversity creates systemic risk:

Key concepts:
- Epistemic monoculture: intellectual ecosystem dominated by a narrow set of views or methods
- Viewpoint homogeneity: perspectives becoming too similar
- Methodological monoculture: one method crowding out alternatives
- Paradigm lock-in: a dominant paradigm blocking adaptation
- Dissent extinction: critical alternatives disappearing from the system

When epistemic monoculture risk IS present:
- Viewpoints become homogeneous
- Methods converge too narrowly
- A paradigm locks inquiry into one frame
- Dissent and alternatives disappear
- Systemic risk grows from lack of intellectual diversity

When no monoculture risk:
- Multiple viewpoints remain available
- Methods remain plural and complementary
- Paradigms can be challenged or revised
- Dissent remains viable
- Diversity provides resilience against systemic failure

Output JSON with: monoculture_detected (bool), severity (none/mild/moderate/severe), methodological_monoculture (how methods are homogenized), paradigm_lock_in (how a paradigm blocks adaptation), dissent_extinction (how dissent disappears), recommendation (no_monoculture/mild_diversity_support/significant_pluralism_repair/major_monoculture_reversal/emergency_diversity_restoration)."""

EPISTEMIC_ECOLOGY_MONOCULTURE_RISK_PROMPT = """Detect epistemic ecology monoculture risk:

Viewpoint homogeneity: {viewpoint_homogeneity}
Methodological monoculture: {methodological_monoculture}
Paradigm lock-in: {paradigm_lock_in}
Dissent extinction: {dissent_extinction}
Domain: {domain}
Context: {context}

Is lack of intellectual diversity creating systemic risk? Return ONLY valid JSON."""


class EpistemicEcologyMonocultureRiskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        viewpoint_homogeneity: str,
        *,
        methodological_monoculture: str = "",
        paradigm_lock_in: str = "",
        dissent_extinction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ECOLOGY_MONOCULTURE_RISK_PROMPT.format(
                viewpoint_homogeneity=viewpoint_homogeneity,
                methodological_monoculture=methodological_monoculture or "Not specified",
                paradigm_lock_in=paradigm_lock_in or "Not specified",
                dissent_extinction=dissent_extinction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ECOLOGY_MONOCULTURE_RISK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "viewpoint_homogeneity": viewpoint_homogeneity[:200],
            "monoculture_detected": data.get("monoculture_detected", False),
            "severity": data.get("severity", ""),
            "methodological_monoculture": data.get("methodological_monoculture", ""),
            "paradigm_lock_in": data.get("paradigm_lock_in", ""),
            "dissent_extinction": data.get("dissent_extinction", ""),
            "recommendation": data.get("recommendation", ""),
        }
