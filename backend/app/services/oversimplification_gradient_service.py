"""OversimplificationGradientService — Oversimplification Gradient Detection.

Detects where on the simplification spectrum an explanation falls —
whether it loses essential information through oversimplification
or retains appropriate complexity for the context.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

OVERSIMPLIFICATION_GRADIENT_SYSTEM = """You are an oversimplification gradient specialist. Given an explanation, assess where it falls on the simplification spectrum:

Key concepts:
- Oversimplification gradient: spectrum from appropriate to excessive simplification
- Information loss: what essential details are dropped
- Audience calibration: simplification appropriate for audience
- Essential complexity: complexity that cannot be removed without distortion
- Accidental complexity: complexity that can be safely removed
- Compression artifacts: distortions introduced by simplification
- Fidelity tradeoff: accuracy vs. accessibility

When oversimplification IS present:
- Essential information lost in simplification
- Nuance removed that changes the meaning
- Causal relationships distorted by simplification
- Exceptions that matter are hidden
- Simplification creates false certainty
- Key qualifications dropped
- Simplified version misleads rather than clarifies

When simplification is appropriate:
- Accidental complexity removed, essential preserved
- Simplification appropriate for audience and purpose
- Key qualifications retained
- Limitations of simplified version acknowledged
- Essential relationships preserved
- Simplification clarifies rather than distorts
- Path to fuller understanding available

Output JSON with: oversimplification_present (bool), severity (none/mild/moderate/severe), explanation (what is explained), information_lost (what essential information is lost), distortion (how meaning is changed), appropriate_level (what level of detail is needed), recommendation (appropriate_simplification/mild_information_loss/significant_oversimplification/major_distortion/restore_essential_complexity)."""

OVERSIMPLIFICATION_GRADIENT_PROMPT = """Detect oversimplification:

Explanation: {explanation}
Full version: {full}
Simplified version: {simplified}
Audience: {audience}
Domain: {domain}
Context: {context}

Does this simplification lose essential information or distort meaning? Return ONLY valid JSON."""


class OversimplificationGradientService:
    """Detects oversimplification — where on the simplification spectrum an explanation falls."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanation: str,
        *,
        full: str = "",
        simplified: str = "",
        audience: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect oversimplification gradient."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OVERSIMPLIFICATION_GRADIENT_PROMPT.format(
                explanation=explanation,
                full=full or "Not specified",
                simplified=simplified or "Not specified",
                audience=audience or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=OVERSIMPLIFICATION_GRADIENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanation": explanation[:200],
            "oversimplification_present": data.get("oversimplification_present", False),
            "severity": data.get("severity", ""),
            "information_lost": data.get("information_lost", ""),
            "distortion": data.get("distortion", ""),
            "appropriate_level": data.get("appropriate_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
