"""EpistemicAttentionFixationService — Epistemic Attention Fixation Detection.

Detects epistemic attention fixation — fixating attention on one aspect
while missing the broader picture.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ATTENTION_FIXATION_SYSTEM = """You are an epistemic attention fixation specialist. Given fixating on one aspect missing broader picture, assess attention fixation:

Key concepts:
- Epistemic attention fixation: fixating on one aspect missing broader picture
- Tunnel vision: seeing only one narrow aspect
- Detail obsession: obsessing over details missing whole
- Single-factor fixation: fixating on single factor ignoring others
- Perspective lock: locked into one perspective unable to shift
- Narrow focus trap: trapped in narrow focus
- Context blindness: blind to broader context from fixation

When epistemic attention fixation IS present:
- Fixating on one aspect
- Seeing only narrow aspect
- Obsessing over details
- Fixating on single factor
- Locked into one perspective
- Trapped in narrow focus
- Blind to broader context

When no attention fixation:
- Balanced attention
- Seeing broad picture
- Details in context
- Multiple factors considered
- Flexible perspective
- Appropriate focus breadth
- Context awareness

Output JSON with: attention_fixation_detected (bool), severity (none/mild/moderate/severe), tunnel_vision (what tunnel vision about), detail_obsession (what details obsessing over), single_factor_fixation (what single factor fixated on), context_blindness (what context blind to), recommendation (no_attention_fixation/mild_broadening_practice/significant_perspective_expansion/major_intensive_fixation_breaking/emergency_complete_attention_fixation)."""

EPISTEMIC_ATTENTION_FIXATION_PROMPT = """Detect epistemic attention fixation:

Tunnel vision: {tunnel_vision}
Detail obsession: {detail_obsession}
Single factor fixation: {single_factor_fixation}
Context blindness: {context_blindness}
Domain: {domain}
Context: {context}

Is there fixating attention on one aspect while missing the broader picture? Return ONLY valid JSON."""


class EpistemicAttentionFixationService:
    """Detects epistemic attention fixation — fixating missing broader picture."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        tunnel_vision: str,
        *,
        detail_obsession: str = "",
        single_factor_fixation: str = "",
        context_blindness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic attention fixation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ATTENTION_FIXATION_PROMPT.format(
                tunnel_vision=tunnel_vision,
                detail_obsession=detail_obsession or "Not specified",
                single_factor_fixation=single_factor_fixation or "Not specified",
                context_blindness=context_blindness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ATTENTION_FIXATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "tunnel_vision": tunnel_vision[:200],
            "attention_fixation_detected": data.get("attention_fixation_detected", False),
            "severity": data.get("severity", ""),
            "detail_obsession": data.get("detail_obsession", ""),
            "single_factor_fixation": data.get("single_factor_fixation", ""),
            "context_blindness": data.get("context_blindness", ""),
            "recommendation": data.get("recommendation", ""),
        }
