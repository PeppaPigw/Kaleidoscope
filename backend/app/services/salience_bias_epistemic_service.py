"""SalienceBiasEpistemicService — Epistemic Salience Bias Detection.

Detects epistemic salience bias — vivid, dramatic, or emotionally
salient information dominating assessment over more diagnostic but
less attention-grabbing evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SALIENCE_BIAS_EPISTEMIC_SYSTEM = """You are an epistemic salience bias specialist. Given an assessment, determine whether salient information is dominating over more diagnostic evidence:

Key concepts:
- Salience bias: vivid info dominating over diagnostic info
- Vividness effect: dramatic examples outweighing statistics
- Emotional salience: emotionally charged info given excess weight
- Attention capture: attention-grabbing info displacing important
- Diagnostic neglect: more diagnostic but less vivid info ignored
- Narrative dominance: stories outweighing data
- Availability by salience: salient examples treated as representative

When salience bias IS present:
- Vivid information dominates over more diagnostic evidence
- Dramatic examples outweigh systematic data
- Emotionally charged information given excess weight
- Attention-grabbing info displaces more important info
- More diagnostic but less vivid evidence ignored
- Stories dominate over statistics
- Salient examples treated as representative

When salience is appropriate:
- Vivid information genuinely diagnostic
- Emotional salience reflects actual importance
- Attention proportionate to diagnostic value
- Both vivid and systematic evidence considered
- Salience not confused with representativeness
- Stories and data integrated appropriately
- Attention allocated by importance not vividness

Output JSON with: salience_bias_present (bool), severity (none/mild/moderate/severe), assessment (what assessment is made), salient_info (what salient info dominates), diagnostic_info (what diagnostic info is neglected), distortion (how assessment is distorted), recommendation (appropriate_attention/mild_salience_effect/significant_salience_bias/major_diagnostic_neglect/weight_by_diagnosticity_not_salience)."""

SALIENCE_BIAS_EPISTEMIC_PROMPT = """Detect epistemic salience bias:

Assessment: {assessment}
Salient information: {salient}
Diagnostic information: {diagnostic}
Weighting: {weighting}
Domain: {domain}
Context: {context}

Is vivid information dominating over more diagnostic evidence? Return ONLY valid JSON."""


class SalienceBiasEpistemicService:
    """Detects epistemic salience bias — vivid info dominating over diagnostic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        assessment: str,
        *,
        salient: str = "",
        diagnostic: str = "",
        weighting: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic salience bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SALIENCE_BIAS_EPISTEMIC_PROMPT.format(
                assessment=assessment,
                salient=salient or "Not specified",
                diagnostic=diagnostic or "Not specified",
                weighting=weighting or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SALIENCE_BIAS_EPISTEMIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "assessment": assessment[:200],
            "salience_bias_present": data.get("salience_bias_present", False),
            "severity": data.get("severity", ""),
            "salient_info": data.get("salient_info", ""),
            "diagnostic_info": data.get("diagnostic_info", ""),
            "distortion": data.get("distortion", ""),
            "recommendation": data.get("recommendation", ""),
        }
