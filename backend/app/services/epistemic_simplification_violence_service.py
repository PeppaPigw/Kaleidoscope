"""EpistemicSimplificationViolenceService — Epistemic Simplification Violence Detection.

Detects epistemic simplification violence — violent oversimplification
that destroys nuance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SIMPLIFICATION_VIOLENCE_SYSTEM = """You are an epistemic simplification violence specialist. Given violent oversimplification destroying nuance, assess simplification violence:

Key concepts:
- Epistemic simplification violence: oversimplification destroying nuance
- Nuance destruction: flattening complex realities into simple binaries
- Forced reduction: forcing complex issues into simple frameworks
- Complexity denial: denying legitimate complexity exists
- Binary imposition: imposing either/or on both/and situations
- Detail erasure: erasing important details for simplicity
- Reductionism violence: reducing in ways that harm understanding

When epistemic simplification violence IS present:
- Oversimplification destroying nuance
- Flattening into binaries
- Forcing into simple frameworks
- Denying legitimate complexity
- Imposing either/or on both/and
- Erasing important details
- Reducing harmfully

When no simplification violence:
- Appropriate simplification
- Preserving nuance
- Frameworks matching complexity
- Acknowledging complexity
- Both/and when appropriate
- Preserving important details
- Helpful reduction

Output JSON with: simplification_violence_detected (bool), severity (none/mild/moderate/severe), nuance_destruction (what flattening into binaries), forced_reduction (what forcing into simple frameworks), complexity_denial (what denying complexity of), binary_imposition (what imposing either/or on), recommendation (no_simplification_violence/mild_nuance_recovery/significant_complexity_honoring/major_intensive_nuance_rebuilding/emergency_complete_simplification_violence)."""

EPISTEMIC_SIMPLIFICATION_VIOLENCE_PROMPT = """Detect epistemic simplification violence:

Nuance destruction: {nuance_destruction}
Forced reduction: {forced_reduction}
Complexity denial: {complexity_denial}
Binary imposition: {binary_imposition}
Domain: {domain}
Context: {context}

Is there violent oversimplification that destroys nuance? Return ONLY valid JSON."""


class EpistemicSimplificationViolenceService:
    """Detects epistemic simplification violence — oversimplification destroying nuance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        nuance_destruction: str,
        *,
        forced_reduction: str = "",
        complexity_denial: str = "",
        binary_imposition: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic simplification violence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SIMPLIFICATION_VIOLENCE_PROMPT.format(
                nuance_destruction=nuance_destruction,
                forced_reduction=forced_reduction or "Not specified",
                complexity_denial=complexity_denial or "Not specified",
                binary_imposition=binary_imposition or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SIMPLIFICATION_VIOLENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "nuance_destruction": nuance_destruction[:200],
            "simplification_violence_detected": data.get("simplification_violence_detected", False),
            "severity": data.get("severity", ""),
            "forced_reduction": data.get("forced_reduction", ""),
            "complexity_denial": data.get("complexity_denial", ""),
            "binary_imposition": data.get("binary_imposition", ""),
            "recommendation": data.get("recommendation", ""),
        }
