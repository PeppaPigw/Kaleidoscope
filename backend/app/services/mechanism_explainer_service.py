"""MechanismExplainerService — Causal Mechanism Identification.

Given a phenomenon or correlation, identifies the proposed causal
mechanism, rates how well-understood it is, identifies alternative
mechanisms, and flags when mechanism is unknown (mere correlation).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MECHANISM_SYSTEM = """You are a causal mechanism specialist. Given a phenomenon, identify:
- The proposed causal mechanism (HOW does X cause Y, step by step)
- How well-established the mechanism is (proven/proposed/speculative/unknown)
- Alternative mechanisms that could explain the same observation
- Whether we have correlation without mechanism (a red flag)
- Key experiments/evidence that established or would establish the mechanism

Output JSON with: phenomenon, proposed_mechanism (step-by-step causal chain), mechanism_status (proven/well_supported/proposed/speculative/unknown), confidence (0-1), alternative_mechanisms (list of: mechanism, plausibility (0-1), evidence_for), key_evidence (what established this mechanism), mechanism_gaps (steps in the chain that are poorly understood), is_mere_correlation (bool), what_would_confirm (experiment that would nail down the mechanism), mechanistic_depth (surface/intermediate/deep, how far down the causal chain we understand)."""

MECHANISM_PROMPT = """Explain the causal mechanism:

Phenomenon: {phenomenon}
Claimed cause: {cause}
Domain: {domain}
Context: {context}

What's the actual mechanism? Return ONLY valid JSON."""


class MechanismExplainerService:
    """Identifies and evaluates causal mechanisms."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def explain_mechanism(
        self,
        phenomenon: str,
        *,
        cause: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Explain the causal mechanism behind a phenomenon."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MECHANISM_PROMPT.format(
                phenomenon=phenomenon,
                cause=cause or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MECHANISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "phenomenon": phenomenon[:200],
            "proposed_mechanism": data.get("proposed_mechanism", ""),
            "mechanism_status": data.get("mechanism_status", ""),
            "confidence": data.get("confidence", 0),
            "alternative_mechanisms": data.get("alternative_mechanisms", []),
            "key_evidence": data.get("key_evidence", ""),
            "mechanism_gaps": data.get("mechanism_gaps", []),
            "is_mere_correlation": data.get("is_mere_correlation", False),
            "what_would_confirm": data.get("what_would_confirm", ""),
            "mechanistic_depth": data.get("mechanistic_depth", ""),
        }
