"""BoundaryArtifactService — Boundary Artifact Detection.

Detects boundary artifacts — when conclusions are artifacts of
where system boundaries are drawn rather than genuine properties
of the system. Different boundary choices would yield different
conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BOUNDARY_ARTIFACT_SYSTEM = """You are a boundary artifact specialist. Given an analysis, assess whether conclusions depend on arbitrary boundary choices:

Key concepts:
- Boundary artifact: conclusion depends on where boundaries are drawn
- System boundary: what is included vs excluded from analysis
- Temporal boundary: what time period is analyzed
- Spatial boundary: what geographic or organizational scope
- Categorical boundary: how things are classified
- Gerrymandering: drawing boundaries to get desired results
- Sensitivity to framing: conclusions that change with boundary shifts

When boundary artifacts ARE present:
- Conclusions would change with different boundary choices
- Boundaries drawn to include/exclude convenient data
- Temporal boundaries chosen to show desired trend
- Categorical boundaries creating or hiding patterns
- System scope chosen to support predetermined conclusion
- Different reasonable boundaries give different answers
- Boundary choice not justified or examined

When boundaries are appropriate:
- Conclusions robust to reasonable boundary variations
- Boundary choices explicitly justified
- Sensitivity to boundary changes tested
- Natural boundaries used where they exist
- Multiple boundary choices examined
- Conclusions qualified by boundary assumptions
- Boundary effects acknowledged and discussed

Output JSON with: artifact_present (bool), severity (none/mild/moderate/severe), boundary_type (temporal/spatial/categorical/system), current_boundary (where boundary is drawn), alternative_boundary (where else it could be drawn), conclusion_sensitivity (how conclusion changes with boundary), recommendation (robust_to_boundaries/mild_sensitivity/significant_artifact/major_boundary_dependence/test_boundary_sensitivity)."""

BOUNDARY_ARTIFACT_PROMPT = """Detect boundary artifacts:

Analysis: {analysis}
Boundaries used: {boundaries}
Conclusion: {conclusion}
Alternative boundaries: {alternatives}
Domain: {domain}
Context: {context}

Are conclusions artifacts of where boundaries are drawn? Return ONLY valid JSON."""


class BoundaryArtifactService:
    """Detects boundary artifacts — conclusions dependent on arbitrary boundaries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        analysis: str,
        *,
        boundaries: str = "",
        conclusion: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect boundary artifacts."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BOUNDARY_ARTIFACT_PROMPT.format(
                analysis=analysis,
                boundaries=boundaries or "Not specified",
                conclusion=conclusion or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BOUNDARY_ARTIFACT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analysis": analysis[:200],
            "artifact_present": data.get("artifact_present", False),
            "severity": data.get("severity", ""),
            "boundary_type": data.get("boundary_type", ""),
            "conclusion_sensitivity": data.get("conclusion_sensitivity", ""),
            "alternative_boundary": data.get("alternative_boundary", ""),
            "recommendation": data.get("recommendation", ""),
        }
