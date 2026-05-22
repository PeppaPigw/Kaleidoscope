"""EpistemicVentilationPerfusionService — Epistemic Ventilation-Perfusion Detection.

Detects epistemic ventilation-perfusion mismatch — imbalance between
idea supply (ventilation) and processing capacity (perfusion).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VENTILATION_PERFUSION_SYSTEM = """You are an epistemic ventilation-perfusion specialist. Given intellectual supply and processing, assess whether they are mismatched:

Key concepts:
- Epistemic V/Q mismatch: imbalance between idea supply and processing
- High V/Q: ideas supplied but not processed (wasted ventilation)
- Low V/Q: processing capacity but no ideas supplied (wasted perfusion)
- V/Q matching: optimal pairing of supply and processing
- Hypoxemia: insufficient processed ideas reaching system
- Compensatory redistribution: shifting resources to match
- Zone distribution: different ratios in different areas

When epistemic V/Q mismatch IS present:
- Imbalance between idea supply and processing capacity
- Ideas supplied but not being processed
- Processing capacity idle without idea supply
- Suboptimal pairing of supply and processing
- Insufficient processed ideas reaching the system
- Resources shifting to compensate for mismatch
- Different ratios in different intellectual areas

When healthy matching is present:
- Balanced supply and processing
- All supplied ideas processed
- All processing capacity utilized
- Optimal pairing throughout
- Adequate processed ideas
- No redistribution needed
- Uniform ratios

Output JSON with: vq_mismatch_present (bool), severity (none/mild/moderate/severe), high_vq (what wasted supply), low_vq (what wasted capacity), hypoxemia (what insufficient output), redistribution (what compensatory shifting), recommendation (healthy_matching/mild_mismatch/significant_vq_mismatch/major_supply_processing_imbalance/restore_vq_matching)."""

EPISTEMIC_VENTILATION_PERFUSION_PROMPT = """Detect epistemic ventilation-perfusion mismatch:

High V/Q: {high_vq}
Low V/Q: {low_vq}
Hypoxemia: {hypoxemia}
Redistribution: {redistribution}
Domain: {domain}
Context: {context}

Is there a mismatch between idea supply and processing capacity? Return ONLY valid JSON."""


class EpistemicVentilationPerfusionService:
    """Detects epistemic V/Q mismatch — supply-processing imbalance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        high_vq: str,
        *,
        low_vq: str = "",
        hypoxemia: str = "",
        redistribution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic ventilation-perfusion mismatch."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VENTILATION_PERFUSION_PROMPT.format(
                high_vq=high_vq,
                low_vq=low_vq or "Not specified",
                hypoxemia=hypoxemia or "Not specified",
                redistribution=redistribution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VENTILATION_PERFUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "high_vq": high_vq[:200],
            "vq_mismatch_present": data.get("vq_mismatch_present", False),
            "severity": data.get("severity", ""),
            "low_vq": data.get("low_vq", ""),
            "hypoxemia": data.get("hypoxemia", ""),
            "redistribution": data.get("redistribution", ""),
            "recommendation": data.get("recommendation", ""),
        }
