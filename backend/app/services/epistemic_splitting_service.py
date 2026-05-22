"""EpistemicSplittingService — Epistemic Splitting Detection.

Detects epistemic splitting — inability to integrate positive and negative
aspects of intellectual positions into coherent wholes, seeing only all-good or all-bad.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SPLITTING_SYSTEM = """You are an epistemic splitting specialist. Given inability to integrate aspects, assess splitting:

Key concepts:
- Epistemic splitting: seeing only all-good or all-bad
- Black-and-white: no middle ground or nuance
- Idealization: seeing framework as perfect
- Devaluation: seeing framework as worthless
- Rapid oscillation: flipping between ideal and worthless
- Integration failure: cannot hold both good and bad
- Primitive defense: earliest form of intellectual protection

When epistemic splitting IS present:
- Seeing only all-good or all-bad
- No middle ground
- Framework seen as perfect
- Framework seen as worthless
- Flipping between extremes
- Cannot hold both aspects
- Primitive protection

When no splitting:
- Integrated view
- Nuanced middle ground
- Realistic assessment
- Balanced evaluation
- Stable perspective
- Holding complexity
- Mature engagement

Output JSON with: splitting_detected (bool), severity (none/mild/moderate/severe), idealization_pattern (what perfect), devaluation_pattern (what worthless), oscillation_speed (what flipping), integration_failure (what cannot hold), recommendation (no_splitting/mild_integration_practice/significant_object_relations_therapy/major_intensive_integration/emergency_rapid_oscillation)."""

EPISTEMIC_SPLITTING_PROMPT = """Detect epistemic splitting:

Idealization pattern: {idealization_pattern}
Devaluation pattern: {devaluation_pattern}
Oscillation speed: {oscillation_speed}
Integration failure: {integration_failure}
Domain: {domain}
Context: {context}

Is there inability to integrate positive and negative aspects seeing only all-good or all-bad? Return ONLY valid JSON."""


class EpistemicSplittingService:
    """Detects epistemic splitting — seeing only all-good or all-bad."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        idealization_pattern: str,
        *,
        devaluation_pattern: str = "",
        oscillation_speed: str = "",
        integration_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic splitting."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SPLITTING_PROMPT.format(
                idealization_pattern=idealization_pattern,
                devaluation_pattern=devaluation_pattern or "Not specified",
                oscillation_speed=oscillation_speed or "Not specified",
                integration_failure=integration_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SPLITTING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "idealization_pattern": idealization_pattern[:200],
            "splitting_detected": data.get("splitting_detected", False),
            "severity": data.get("severity", ""),
            "devaluation_pattern": data.get("devaluation_pattern", ""),
            "oscillation_speed": data.get("oscillation_speed", ""),
            "integration_failure": data.get("integration_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
