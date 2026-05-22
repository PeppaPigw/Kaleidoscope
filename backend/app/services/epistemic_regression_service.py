"""EpistemicRegressionService — Epistemic Regression Detection.

Detects epistemic regression — reverting to earlier, less sophisticated
intellectual functioning under stress or threat.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_REGRESSION_SYSTEM = """You are an epistemic regression specialist. Given intellectual reversion, assess regression:

Key concepts:
- Epistemic regression: reverting to earlier intellectual functioning
- Simplification: complex thinking collapses to simple
- Black-and-white: nuance disappears under stress
- Authority seeking: wanting someone to tell you what to think
- Magical thinking: abandoning rational analysis
- Concrete operations: losing abstract capacity
- Defensive retreat: falling back to safe intellectual territory

When epistemic regression IS present:
- Reverting to earlier functioning
- Complex collapses to simple
- Nuance disappears
- Wanting to be told
- Abandoning rational analysis
- Losing abstract capacity
- Retreating to safe territory

When no regression:
- Maintaining sophistication
- Complexity preserved
- Nuance maintained
- Independent thinking
- Rational analysis intact
- Abstract capacity stable
- Engaging new territory

Output JSON with: regression_detected (bool), severity (none/mild/moderate/severe), simplification_level (what collapsing), authority_seeking (what wanting told), magical_thinking (what abandoning), defensive_retreat (what falling back), recommendation (no_regression/mild_stress_management/significant_developmental_support/major_intensive_recovery/emergency_complete_collapse)."""

EPISTEMIC_REGRESSION_PROMPT = """Detect epistemic regression:

Simplification level: {simplification_level}
Authority seeking: {authority_seeking}
Magical thinking: {magical_thinking}
Defensive retreat: {defensive_retreat}
Domain: {domain}
Context: {context}

Is there reversion to earlier less sophisticated intellectual functioning under stress? Return ONLY valid JSON."""


class EpistemicRegressionService:
    """Detects epistemic regression — reverting to earlier intellectual functioning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        simplification_level: str,
        *,
        authority_seeking: str = "",
        magical_thinking: str = "",
        defensive_retreat: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic regression."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_REGRESSION_PROMPT.format(
                simplification_level=simplification_level,
                authority_seeking=authority_seeking or "Not specified",
                magical_thinking=magical_thinking or "Not specified",
                defensive_retreat=defensive_retreat or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_REGRESSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "simplification_level": simplification_level[:200],
            "regression_detected": data.get("regression_detected", False),
            "severity": data.get("severity", ""),
            "authority_seeking": data.get("authority_seeking", ""),
            "magical_thinking": data.get("magical_thinking", ""),
            "defensive_retreat": data.get("defensive_retreat", ""),
            "recommendation": data.get("recommendation", ""),
        }
