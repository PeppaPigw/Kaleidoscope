"""SelectionEffectBlindnessService — Selection Effect Blindness Detection.

Detects selection effect blindness — ignoring how selection
processes create misleading patterns in observed data, making
non-representative samples appear representative.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SELECTION_EFFECT_BLINDNESS_SYSTEM = """You are a selection effect blindness specialist. Given a conclusion, assess whether selection effects are creating misleading patterns:

Key concepts:
- Selection bias: non-random selection creating misleading patterns
- Survivorship bias: only seeing what survived selection
- Berkson's paradox: selection creating spurious correlations
- Collider bias: conditioning on a common effect
- Truncation: only observing part of the distribution
- Self-selection: subjects choosing to participate
- Publication bias: only positive results published

When selection effect blindness IS present:
- Conclusions drawn from non-randomly selected sample
- Selection process not accounted for
- Survivorship creating misleading patterns
- Collider bias creating spurious correlations
- Truncated distribution treated as complete
- Self-selection not addressed
- Selection mechanism ignored in interpretation

When selection effects are recognized:
- Selection process explicitly modeled
- Survivorship bias accounted for
- Collider bias identified and avoided
- Full distribution considered, not just observed
- Self-selection effects estimated
- Selection mechanism incorporated into analysis
- Conclusions qualified by selection limitations

Output JSON with: blindness_present (bool), severity (none/mild/moderate/severe), conclusion (what conclusion is drawn), selection_mechanism (how data was selected), bias_direction (how selection distorts), missing_data (what is not observed due to selection), recommendation (selection_recognized/mild_blindness/significant_selection_bias/major_selection_artifact/model_selection_process)."""

SELECTION_EFFECT_BLINDNESS_PROMPT = """Detect selection effect blindness:

Conclusion: {conclusion}
Sample: {sample}
Selection process: {selection}
What's missing: {missing}
Domain: {domain}
Context: {context}

Are selection effects creating misleading patterns that are being ignored? Return ONLY valid JSON."""


class SelectionEffectBlindnessService:
    """Detects selection effect blindness — ignoring how selection creates misleading patterns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conclusion: str,
        *,
        sample: str = "",
        selection: str = "",
        missing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect selection effect blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SELECTION_EFFECT_BLINDNESS_PROMPT.format(
                conclusion=conclusion,
                sample=sample or "Not specified",
                selection=selection or "Not specified",
                missing=missing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SELECTION_EFFECT_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conclusion": conclusion[:200],
            "blindness_present": data.get("blindness_present", False),
            "severity": data.get("severity", ""),
            "selection_mechanism": data.get("selection_mechanism", ""),
            "bias_direction": data.get("bias_direction", ""),
            "missing_data": data.get("missing_data", ""),
            "recommendation": data.get("recommendation", ""),
        }
