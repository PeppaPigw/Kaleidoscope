"""EpistemicAttentionSalienceBiasService — Epistemic Attention Salience Bias Detection.

Detects epistemic attention salience bias where vivid or dramatic information
captures disproportionate attention over less salient base-rate evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ATTENTION_SALIENCE_BIAS_SYSTEM = """You are an epistemic attention salience bias specialist. Given attention capture patterns, assess salience-driven distortion:

Key concepts:
- Epistemic salience bias: vivid or dramatic information captures disproportionate attention
- Vividness capture: concrete, emotional, or sensory details dominate evaluation
- Base rate neglect: statistical background evidence is displaced by salient examples
- Availability cascade: repeated salient claims become easier to believe
- Drama premium: dramatic evidence receives more weight than probative evidence

When epistemic salience bias IS present:
- Vivid information drives attention
- Base rates are neglected
- Repeated salient examples amplify confidence
- Drama is treated as epistemic importance
- Boring but reliable evidence is discounted

When no salience bias:
- Attention tracks evidential value
- Base rates remain visible
- Repetition is separated from truth
- Dramatic content is calibrated
- Reliable low-salience evidence is included

Output JSON with: salience_bias_detected (bool), severity (none/mild/moderate/severe), base_rate_neglect (what base rates are neglected), availability_cascade (what salient repetition amplifies), drama_premium (what drama is overweighted), recommendation (no_salience_bias/mild_salience_calibration/significant_base_rate_restoration/major_attention_rebalancing/emergency_complete_salience_debiasing)."""

EPISTEMIC_ATTENTION_SALIENCE_BIAS_PROMPT = """Detect epistemic attention salience bias:

Vividness capture: {vividness_capture}
Base rate neglect: {base_rate_neglect}
Availability cascade: {availability_cascade}
Drama premium: {drama_premium}
Domain: {domain}
Context: {context}

Is vivid or dramatic information capturing disproportionate attention? Return ONLY valid JSON."""


class EpistemicAttentionSalienceBiasService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        vividness_capture: str,
        *,
        base_rate_neglect: str = "",
        availability_cascade: str = "",
        drama_premium: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ATTENTION_SALIENCE_BIAS_PROMPT.format(
                vividness_capture=vividness_capture,
                base_rate_neglect=base_rate_neglect or "Not specified",
                availability_cascade=availability_cascade or "Not specified",
                drama_premium=drama_premium or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ATTENTION_SALIENCE_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "vividness_capture": vividness_capture[:200],
            "salience_bias_detected": data.get("salience_bias_detected", False),
            "severity": data.get("severity", ""),
            "base_rate_neglect": data.get("base_rate_neglect", ""),
            "availability_cascade": data.get("availability_cascade", ""),
            "drama_premium": data.get("drama_premium", ""),
            "recommendation": data.get("recommendation", ""),
        }
