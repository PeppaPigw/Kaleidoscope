"""EpistemicSelectiveAttentionService — Epistemic Selective Attention Detection.

Detects epistemic selective attention — selectively attending only to
confirming information.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SELECTIVE_ATTENTION_SYSTEM = """You are an epistemic selective attention specialist. Given selectively attending to confirming information, assess selective attention:

Key concepts:
- Epistemic selective attention: attending only to confirming information
- Confirmation seeking: actively seeking only supporting evidence
- Disconfirmation avoidance: avoiding information that might disconfirm
- Attention filtering: filtering out challenging information
- Source selection: choosing only agreeable sources
- Signal boosting: amplifying confirming signals
- Noise classification: classifying disconfirming info as noise

When epistemic selective attention IS present:
- Attending only to confirming
- Seeking only supporting evidence
- Avoiding disconfirming information
- Filtering out challenges
- Choosing only agreeable sources
- Amplifying confirming signals
- Classifying disconfirming as noise

When no selective attention:
- Attending to all evidence
- Seeking diverse evidence
- Welcoming disconfirmation
- Open to challenges
- Diverse sources
- Equal signal treatment
- Fair classification

Output JSON with: selective_attention_detected (bool), severity (none/mild/moderate/severe), confirmation_seeking (what seeking only support for), disconfirmation_avoidance (what avoiding challenge to), attention_filtering (what filtering out), source_selection (what choosing only agreeable about), recommendation (no_selective_attention/mild_attention_broadening/significant_disconfirmation_seeking/major_intensive_attention_rebalancing/emergency_complete_confirmation_tunnel)."""

EPISTEMIC_SELECTIVE_ATTENTION_PROMPT = """Detect epistemic selective attention:

Confirmation seeking: {confirmation_seeking}
Disconfirmation avoidance: {disconfirmation_avoidance}
Attention filtering: {attention_filtering}
Source selection: {source_selection}
Domain: {domain}
Context: {context}

Is there selectively attending only to confirming information? Return ONLY valid JSON."""


class EpistemicSelectiveAttentionService:
    """Detects epistemic selective attention — attending only to confirming information."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        confirmation_seeking: str,
        *,
        disconfirmation_avoidance: str = "",
        attention_filtering: str = "",
        source_selection: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic selective attention."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SELECTIVE_ATTENTION_PROMPT.format(
                confirmation_seeking=confirmation_seeking,
                disconfirmation_avoidance=disconfirmation_avoidance or "Not specified",
                attention_filtering=attention_filtering or "Not specified",
                source_selection=source_selection or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SELECTIVE_ATTENTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "confirmation_seeking": confirmation_seeking[:200],
            "selective_attention_detected": data.get("selective_attention_detected", False),
            "severity": data.get("severity", ""),
            "disconfirmation_avoidance": data.get("disconfirmation_avoidance", ""),
            "attention_filtering": data.get("attention_filtering", ""),
            "source_selection": data.get("source_selection", ""),
            "recommendation": data.get("recommendation", ""),
        }
