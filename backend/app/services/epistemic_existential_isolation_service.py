"""EpistemicExistentialIsolationService — Epistemic Existential Isolation Detection.

Detects epistemic existential isolation — fundamental aloneness in one's
intellectual experience that cannot be bridged by any relationship.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXISTENTIAL_ISOLATION_SYSTEM = """You are an epistemic existential isolation specialist. Given fundamental intellectual aloneness, assess existential isolation:

Key concepts:
- Epistemic existential isolation: fundamental aloneness in thinking
- Unbridgeable gap: no one can truly share your intellectual experience
- Subjective prison: trapped in own perspective
- Communication failure: cannot convey what you truly mean
- Unique burden: carrying insights no one else sees
- Loneliness of understanding: seeing what others cannot
- Radical separateness: fundamentally alone in thought

When epistemic existential isolation IS present:
- Fundamental aloneness
- No one can share experience
- Trapped in own perspective
- Cannot convey meaning
- Carrying unique insights
- Seeing what others cannot
- Fundamentally alone

When no existential isolation:
- Connected in thinking
- Shared experience
- Multiple perspectives
- Successful communication
- Shared understanding
- Others see similarly
- Intellectual community

Output JSON with: existential_isolation_detected (bool), severity (none/mild/moderate/severe), unbridgeable_gap (what cannot share), communication_failure (what cannot convey), unique_burden (what carrying alone), radical_separateness (what fundamentally alone), recommendation (no_existential_isolation/mild_connection_seeking/significant_existential_therapy/major_intensive_bridging/emergency_complete_isolation)."""

EPISTEMIC_EXISTENTIAL_ISOLATION_PROMPT = """Detect epistemic existential isolation:

Unbridgeable gap: {unbridgeable_gap}
Communication failure: {communication_failure}
Unique burden: {unique_burden}
Radical separateness: {radical_separateness}
Domain: {domain}
Context: {context}

Is there fundamental aloneness in intellectual experience that cannot be bridged? Return ONLY valid JSON."""


class EpistemicExistentialIsolationService:
    """Detects epistemic existential isolation — fundamental intellectual aloneness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        unbridgeable_gap: str,
        *,
        communication_failure: str = "",
        unique_burden: str = "",
        radical_separateness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic existential isolation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXISTENTIAL_ISOLATION_PROMPT.format(
                unbridgeable_gap=unbridgeable_gap,
                communication_failure=communication_failure or "Not specified",
                unique_burden=unique_burden or "Not specified",
                radical_separateness=radical_separateness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXISTENTIAL_ISOLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "unbridgeable_gap": unbridgeable_gap[:200],
            "existential_isolation_detected": data.get("existential_isolation_detected", False),
            "severity": data.get("severity", ""),
            "communication_failure": data.get("communication_failure", ""),
            "unique_burden": data.get("unique_burden", ""),
            "radical_separateness": data.get("radical_separateness", ""),
            "recommendation": data.get("recommendation", ""),
        }
