"""EpistemicMonocultureService — Epistemic Monoculture Detection.

Detects epistemic monoculture — dangerous homogeneity in knowledge
sources, methods, frameworks, or perspectives that creates
systemic vulnerability to shared blind spots.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MONOCULTURE_SYSTEM = """You are an epistemic monoculture specialist. Given a knowledge ecosystem, assess whether dangerous homogeneity exists:

Key concepts:
- Epistemic monoculture: single framework/method/source dominating
- Systemic vulnerability: shared blind spots across all participants
- Methodological diversity: multiple approaches to same question
- Source diversity: multiple independent information sources
- Framework diversity: multiple theoretical lenses
- Correlated failure: when monoculture fails, everything fails together
- Resilience through diversity: diverse approaches catch different errors

When epistemic monoculture IS present:
- Single methodology dominates without alternatives
- All participants trained in same framework
- One information source used by everyone
- No methodological diversity in approach
- Shared assumptions never questioned because universal
- Correlated failure risk high
- Alternative perspectives systematically excluded

When epistemic diversity is present:
- Multiple methodologies applied
- Diverse training and perspectives represented
- Multiple independent information sources
- Assumptions challenged from different frameworks
- Methodological pluralism practiced
- Failure modes uncorrelated
- Alternative perspectives actively sought

Output JSON with: monoculture_present (bool), severity (none/mild/moderate/severe), ecosystem (what knowledge ecosystem), dominant_framework (what dominates), missing_diversity (what perspectives are absent), vulnerability (what shared blind spot exists), recommendation (diverse_ecosystem/mild_homogeneity/significant_monoculture/major_systemic_vulnerability/diversify_approaches)."""

EPISTEMIC_MONOCULTURE_PROMPT = """Detect epistemic monoculture:

Ecosystem: {ecosystem}
Methods used: {methods}
Sources: {sources}
Perspectives: {perspectives}
Domain: {domain}
Context: {context}

Is there dangerous epistemic homogeneity in this knowledge ecosystem? Return ONLY valid JSON."""


class EpistemicMonocultureService:
    """Detects epistemic monoculture — dangerous knowledge homogeneity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ecosystem: str,
        *,
        methods: str = "",
        sources: str = "",
        perspectives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic monoculture."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MONOCULTURE_PROMPT.format(
                ecosystem=ecosystem,
                methods=methods or "Not specified",
                sources=sources or "Not specified",
                perspectives=perspectives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MONOCULTURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ecosystem": ecosystem[:200],
            "monoculture_present": data.get("monoculture_present", False),
            "severity": data.get("severity", ""),
            "dominant_framework": data.get("dominant_framework", ""),
            "missing_diversity": data.get("missing_diversity", ""),
            "vulnerability": data.get("vulnerability", ""),
            "recommendation": data.get("recommendation", ""),
        }
