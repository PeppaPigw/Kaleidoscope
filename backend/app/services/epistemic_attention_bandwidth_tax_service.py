"""EpistemicAttentionBandwidthTaxService — Epistemic Attention Bandwidth Tax Detection.

Detects epistemic attention bandwidth tax where scarcity or stress reduces
cognitive capacity for accurate inquiry and belief updating.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ATTENTION_BANDWIDTH_TAX_SYSTEM = """You are an epistemic attention bandwidth tax specialist. Given cognitive load conditions, assess bandwidth-driven epistemic impairment:

Key concepts:
- Cognitive bandwidth tax: scarcity or stress reduces epistemic capacity
- Cognitive load: active burden limits attention, memory, and reasoning
- Scarcity mindset: scarce resources narrow attention and planning
- Tunneling effect: urgent demands crowd out broader evidence
- Executive function depletion: self-control and integration capacity are reduced

When bandwidth tax IS present:
- Cognitive load degrades inquiry
- Scarcity narrows the evidential field
- Urgency creates tunnel vision
- Executive function is depleted
- Simplified judgments replace careful updating

When no bandwidth tax:
- Adequate cognitive capacity remains
- Scarcity pressure is accounted for
- Attention stays broad enough
- Executive function supports evaluation
- Updating remains proportionate

Output JSON with: bandwidth_tax_detected (bool), severity (none/mild/moderate/severe), scarcity_mindset (what scarcity narrows), tunneling_effect (what evidence is crowded out), executive_function_depletion (what reasoning capacity is reduced), recommendation (no_bandwidth_tax/mild_load_reduction/significant_attention_support/major_capacity_restoration/emergency_complete_bandwidth_recovery)."""

EPISTEMIC_ATTENTION_BANDWIDTH_TAX_PROMPT = """Detect epistemic attention bandwidth tax:

Cognitive load: {cognitive_load}
Scarcity mindset: {scarcity_mindset}
Tunneling effect: {tunneling_effect}
Executive function depletion: {executive_function_depletion}
Domain: {domain}
Context: {context}

Is scarcity or stress reducing epistemic capacity? Return ONLY valid JSON."""


class EpistemicAttentionBandwidthTaxService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        cognitive_load: str,
        *,
        scarcity_mindset: str = "",
        tunneling_effect: str = "",
        executive_function_depletion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ATTENTION_BANDWIDTH_TAX_PROMPT.format(
                cognitive_load=cognitive_load,
                scarcity_mindset=scarcity_mindset or "Not specified",
                tunneling_effect=tunneling_effect or "Not specified",
                executive_function_depletion=executive_function_depletion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ATTENTION_BANDWIDTH_TAX_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "cognitive_load": cognitive_load[:200],
            "bandwidth_tax_detected": data.get("bandwidth_tax_detected", False),
            "severity": data.get("severity", ""),
            "scarcity_mindset": data.get("scarcity_mindset", ""),
            "tunneling_effect": data.get("tunneling_effect", ""),
            "executive_function_depletion": data.get("executive_function_depletion", ""),
            "recommendation": data.get("recommendation", ""),
        }
