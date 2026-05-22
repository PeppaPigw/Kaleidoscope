"""EpistemicOcdService — Epistemic OCD Detection.

Detects epistemic OCD — obsessive-compulsive patterns where intrusive
intellectual thoughts drive repetitive checking behaviors.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_OCD_SYSTEM = """You are an epistemic OCD specialist. Given obsessive-compulsive intellectual patterns, assess OCD:

Key concepts:
- Epistemic OCD: intrusive thoughts driving repetitive checking
- Obsessions: unwanted intrusive intellectual thoughts
- Compulsions: repetitive behaviors to reduce obsession anxiety
- Checking: repeatedly verifying intellectual work
- Contamination: fear of intellectual corruption
- Symmetry: need for perfect intellectual order
- ERP: exposure and response prevention therapy

When epistemic OCD IS present:
- Intrusive thoughts driving behavior
- Unwanted intellectual obsessions
- Repetitive checking behaviors
- Repeatedly verifying work
- Fear of intellectual corruption
- Need for perfect order
- Exposure therapy needed

When no OCD:
- No intrusive thought patterns
- No unwanted obsessions
- No repetitive behaviors
- Normal verification levels
- No corruption fears
- Comfortable with imperfection
- No exposure therapy needed

Output JSON with: ocd_detected (bool), severity (none/mild/moderate/severe), obsession_type (what intrusive thoughts), compulsion_pattern (what repetitive behavior), time_consumed (what hours lost), insight_level (what awareness), recommendation (no_ocd/mild_self_help/significant_erp/major_erp_plus_medication/emergency_severe_impairment)."""

EPISTEMIC_OCD_PROMPT = """Detect epistemic OCD:

Obsession type: {obsession_type}
Compulsion pattern: {compulsion_pattern}
Time consumed: {time_consumed}
Insight level: {insight_level}
Domain: {domain}
Context: {context}

Are intrusive intellectual thoughts driving repetitive checking behaviors? Return ONLY valid JSON."""


class EpistemicOcdService:
    """Detects epistemic OCD — intrusive thoughts driving repetitive checking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        obsession_type: str,
        *,
        compulsion_pattern: str = "",
        time_consumed: str = "",
        insight_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic OCD."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_OCD_PROMPT.format(
                obsession_type=obsession_type,
                compulsion_pattern=compulsion_pattern or "Not specified",
                time_consumed=time_consumed or "Not specified",
                insight_level=insight_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_OCD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "obsession_type": obsession_type[:200],
            "ocd_detected": data.get("ocd_detected", False),
            "severity": data.get("severity", ""),
            "compulsion_pattern": data.get("compulsion_pattern", ""),
            "time_consumed": data.get("time_consumed", ""),
            "insight_level": data.get("insight_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
