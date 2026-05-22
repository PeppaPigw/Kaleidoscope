"""EpistemicTeethingService — Epistemic Teething Detection.

Detects epistemic teething — painful emergence of new intellectual
capabilities causing temporary distress and disruption.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEETHING_SYSTEM = """You are an epistemic teething specialist. Given painful emergence of new capabilities, assess teething:

Key concepts:
- Epistemic teething: painful emergence of new capabilities
- Eruption: new capability breaking through
- Drooling: excess output during emergence
- Irritability: distress from emergence process
- Fever: systemic response to emergence
- Biting: testing new capability aggressively
- Soothing: managing discomfort during emergence

When epistemic teething IS occurring:
- New capability painfully emerging
- Breaking through existing surface
- Excess output during process
- Distress from emergence
- Systemic response present
- Aggressive testing of new capability
- Need for discomfort management

When no teething:
- No new capabilities emerging
- Stable existing surface
- Normal output levels
- No emergence distress
- No systemic response
- Normal capability use
- No discomfort

Output JSON with: teething_detected (bool), severity (none/mild/moderate/severe), eruption_stage (what emergence phase), irritability_level (what distress), systemic_response (what body reaction), soothing_need (what comfort required), recommendation (no_teething/mild_discomfort/significant_emergence/major_difficult_eruption/complicated_impacted_emergence)."""

EPISTEMIC_TEETHING_PROMPT = """Detect epistemic teething:

Eruption stage: {eruption_stage}
Irritability level: {irritability_level}
Systemic response: {systemic_response}
Soothing need: {soothing_need}
Domain: {domain}
Context: {context}

Are new intellectual capabilities painfully emerging? Return ONLY valid JSON."""


class EpistemicTeethingService:
    """Detects epistemic teething — painful emergence of new capabilities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        eruption_stage: str,
        *,
        irritability_level: str = "",
        systemic_response: str = "",
        soothing_need: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic teething."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEETHING_PROMPT.format(
                eruption_stage=eruption_stage,
                irritability_level=irritability_level or "Not specified",
                systemic_response=systemic_response or "Not specified",
                soothing_need=soothing_need or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEETHING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "eruption_stage": eruption_stage[:200],
            "teething_detected": data.get("teething_detected", False),
            "severity": data.get("severity", ""),
            "irritability_level": data.get("irritability_level", ""),
            "systemic_response": data.get("systemic_response", ""),
            "soothing_need": data.get("soothing_need", ""),
            "recommendation": data.get("recommendation", ""),
        }
