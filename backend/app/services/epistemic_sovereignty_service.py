"""EpistemicSovereigntyService — Epistemic Sovereignty Detection.

Detects epistemic sovereignty — full self-governance over one's intellectual
life, the capacity to determine one's own beliefs and knowledge practices.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SOVEREIGNTY_SYSTEM = """You are an epistemic sovereignty specialist. Given intellectual self-governance, assess sovereignty:

Key concepts:
- Epistemic sovereignty: full self-governance over intellectual life
- Self-determination: choosing own beliefs and methods
- Intellectual independence: not dependent on external validation
- Knowledge authority: being the authority on own experience
- Boundary maintenance: protecting intellectual autonomy
- Selective engagement: choosing what to engage with
- Authentic inquiry: pursuing questions that genuinely matter

When epistemic sovereignty IS present:
- Full self-governance
- Choosing own beliefs
- Not dependent on validation
- Authority on own experience
- Protecting autonomy
- Choosing engagement
- Pursuing genuine questions

When sovereignty compromised:
- External governance
- Beliefs imposed
- Dependent on validation
- Others define experience
- Autonomy violated
- Forced engagement
- Pursuing others' questions

Output JSON with: sovereignty_detected (bool), severity (none/mild/moderate/severe), self_determination (what choosing), independence_level (what not dependent), boundary_maintenance (what protecting), authentic_inquiry (what pursuing), recommendation (sovereignty_intact/mild_sovereignty_strengthening/significant_sovereignty_building/major_intensive_sovereignty_recovery/emergency_sovereignty_crisis)."""

EPISTEMIC_SOVEREIGNTY_PROMPT = """Detect epistemic sovereignty:

Self determination: {self_determination}
Independence level: {independence_level}
Boundary maintenance: {boundary_maintenance}
Authentic inquiry: {authentic_inquiry}
Domain: {domain}
Context: {context}

Is there full self-governance over intellectual life and knowledge practices? Return ONLY valid JSON."""


class EpistemicSovereigntyService:
    """Detects epistemic sovereignty — intellectual self-governance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        self_determination: str,
        *,
        independence_level: str = "",
        boundary_maintenance: str = "",
        authentic_inquiry: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic sovereignty."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SOVEREIGNTY_PROMPT.format(
                self_determination=self_determination,
                independence_level=independence_level or "Not specified",
                boundary_maintenance=boundary_maintenance or "Not specified",
                authentic_inquiry=authentic_inquiry or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SOVEREIGNTY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "self_determination": self_determination[:200],
            "sovereignty_detected": data.get("sovereignty_detected", False),
            "severity": data.get("severity", ""),
            "independence_level": data.get("independence_level", ""),
            "boundary_maintenance": data.get("boundary_maintenance", ""),
            "authentic_inquiry": data.get("authentic_inquiry", ""),
            "recommendation": data.get("recommendation", ""),
        }
