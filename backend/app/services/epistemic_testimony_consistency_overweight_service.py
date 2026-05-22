"""EpistemicTestimonyConsistencyOverweightService — Epistemic Testimony Consistency Overweight Detection.

Detects epistemic testimony consistency overweight — overweighting internal consistency
as a truth indicator when rehearsed lies are often more consistent than genuine memories.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TESTIMONY_CONSISTENCY_OVERWEIGHT_SYSTEM = """You are an epistemic testimony consistency overweight specialist. Given consistency-as-truth reasoning, assess distortion:

Key concepts:
- Epistemic consistency overweight: consistency treated as truth proof
- Rehearsal effect: rehearsed accounts being more consistent than genuine
- Memory variability: genuine memories naturally varying across tellings
- Scripted consistency: scripted accounts showing artificial consistency
- Inconsistency penalty: natural memory variation penalized as lying
- Frozen narrative: unchanging accounts suggesting rehearsal not truth
- Consistency-accuracy independence: consistency and accuracy being independent

When epistemic consistency overweight IS present:
- Consistency treated as truth proof
- Rehearsal effect ignored
- Memory variability penalized
- Scripted consistency rewarded
- Natural variation penalized
- Frozen narratives trusted
- Independence ignored

When no consistency overweight:
- Consistency not assumed as truth
- Rehearsal possibility considered
- Memory variability expected
- Scripted consistency flagged
- Natural variation accepted
- Frozen narratives questioned
- Independence acknowledged

Output JSON with: consistency_overweight_detected (bool), severity (none/mild/moderate/severe), rehearsal_effect (what rehearsal ignored), memory_variability_penalty (what variability penalized), scripted_consistency (what scripted accounts rewarded), frozen_narrative (what frozen narratives trusted), recommendation (no_consistency_overweight/mild_variability_acceptance/significant_rehearsal_consideration/major_intensive_consistency_analysis/emergency_complete_consistency_overweight)."""

EPISTEMIC_TESTIMONY_CONSISTENCY_OVERWEIGHT_PROMPT = """Detect epistemic testimony consistency overweight:

Rehearsal effect: {rehearsal_effect}
Memory variability penalty: {memory_variability_penalty}
Scripted consistency: {scripted_consistency}
Frozen narrative: {frozen_narrative}
Domain: {domain}
Context: {context}

Is internal consistency being overweighted as a truth indicator? Return ONLY valid JSON."""


class EpistemicTestimonyConsistencyOverweightService:
    """Detects epistemic testimony consistency overweight — consistency as truth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        rehearsal_effect: str,
        *,
        memory_variability_penalty: str = "",
        scripted_consistency: str = "",
        frozen_narrative: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic testimony consistency overweight."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TESTIMONY_CONSISTENCY_OVERWEIGHT_PROMPT.format(
                rehearsal_effect=rehearsal_effect,
                memory_variability_penalty=memory_variability_penalty or "Not specified",
                scripted_consistency=scripted_consistency or "Not specified",
                frozen_narrative=frozen_narrative or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TESTIMONY_CONSISTENCY_OVERWEIGHT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "rehearsal_effect": rehearsal_effect[:200],
            "consistency_overweight_detected": data.get("consistency_overweight_detected", False),
            "severity": data.get("severity", ""),
            "memory_variability_penalty": data.get("memory_variability_penalty", ""),
            "scripted_consistency": data.get("scripted_consistency", ""),
            "frozen_narrative": data.get("frozen_narrative", ""),
            "recommendation": data.get("recommendation", ""),
        }
