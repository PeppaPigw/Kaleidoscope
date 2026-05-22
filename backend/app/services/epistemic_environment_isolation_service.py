"""EpistemicEnvironmentIsolationService — Epistemic Environment Isolation Detection.

Detects epistemic environment isolation — environmental isolation limiting
epistemic input diversity and creating echo chambers.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ENVIRONMENT_ISOLATION_SYSTEM = """You are an epistemic environment isolation specialist. Given environmental isolation limiting input diversity, assess environment isolation:

Key concepts:
- Epistemic environment isolation: environmental isolation limiting input diversity
- Source homogeneity: all sources coming from same perspective
- Perspective poverty: poverty of diverse perspectives
- Echo chamber formation: environment forming echo chamber
- Input narrowing: inputs narrowed to single stream
- Diversity deficit: deficit of diverse epistemic inputs
- Intellectual monoculture: monoculture of ideas in environment

When epistemic environment isolation IS present:
- Environment isolating from diversity
- Sources homogeneous
- Perspectives impoverished
- Echo chamber forming
- Inputs narrowed
- Diversity deficit
- Intellectual monoculture

When no environment isolation:
- Environment supporting diversity
- Sources diverse
- Perspectives rich
- No echo chamber
- Inputs broad
- Diversity adequate
- Intellectual diversity

Output JSON with: environment_isolation_detected (bool), severity (none/mild/moderate/severe), source_homogeneity (what sources homogeneous), perspective_poverty (what perspectives impoverished), echo_chamber_formation (what echo chamber forming about), diversity_deficit (what diversity lacking), recommendation (no_environment_isolation/mild_diversity_seeking/significant_perspective_expansion/major_intensive_isolation_breaking/emergency_complete_environment_isolation)."""

EPISTEMIC_ENVIRONMENT_ISOLATION_PROMPT = """Detect epistemic environment isolation:

Source homogeneity: {source_homogeneity}
Perspective poverty: {perspective_poverty}
Echo chamber formation: {echo_chamber_formation}
Diversity deficit: {diversity_deficit}
Domain: {domain}
Context: {context}

Is environmental isolation limiting epistemic input diversity? Return ONLY valid JSON."""


class EpistemicEnvironmentIsolationService:
    """Detects epistemic environment isolation — isolation limiting diversity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        source_homogeneity: str,
        *,
        perspective_poverty: str = "",
        echo_chamber_formation: str = "",
        diversity_deficit: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic environment isolation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ENVIRONMENT_ISOLATION_PROMPT.format(
                source_homogeneity=source_homogeneity,
                perspective_poverty=perspective_poverty or "Not specified",
                echo_chamber_formation=echo_chamber_formation or "Not specified",
                diversity_deficit=diversity_deficit or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ENVIRONMENT_ISOLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "source_homogeneity": source_homogeneity[:200],
            "environment_isolation_detected": data.get("environment_isolation_detected", False),
            "severity": data.get("severity", ""),
            "perspective_poverty": data.get("perspective_poverty", ""),
            "echo_chamber_formation": data.get("echo_chamber_formation", ""),
            "diversity_deficit": data.get("diversity_deficit", ""),
            "recommendation": data.get("recommendation", ""),
        }
