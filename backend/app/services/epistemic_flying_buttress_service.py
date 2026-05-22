"""EpistemicFlyingButtressService — Epistemic Flying Buttress Detection.

Detects epistemic flying buttresses — external supports propping up
beliefs that cannot stand on their own evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FLYING_BUTTRESS_SYSTEM = """You are an epistemic flying buttress specialist. Given a belief system, assess whether external supports are propping up beliefs that can't stand alone:

Key concepts:
- Epistemic flying buttress: external supports propping up beliefs
- External dependency: beliefs depending on external support
- Self-support failure: beliefs unable to stand on own evidence
- Authority props: authority used to prop up weak beliefs
- Social support: social pressure supporting unsupported beliefs
- Emotional buttress: emotional investment propping up beliefs
- Removal vulnerability: vulnerability if external support removed

When epistemic flying buttress IS present:
- External supports propping up beliefs
- Beliefs depending on external support to survive
- Beliefs unable to stand on their own evidence
- Authority used to prop up evidentially weak beliefs
- Social pressure supporting otherwise unsupported beliefs
- Emotional investment propping up beliefs
- Beliefs would collapse if external support removed

When self-supporting belief is present:
- Beliefs standing on their own evidence
- No external support needed for survival
- Beliefs supported by their own evidential base
- Authority confirming but not required
- Social acceptance following from evidence
- Emotional investment following from conviction
- Beliefs robust to removal of external support

Output JSON with: flying_buttress_present (bool), severity (none/mild/moderate/severe), system (what belief system), belief (what belief is propped up), support (what external support exists), self_support (whether belief can stand alone), recommendation (self_supporting/mild_external_support/significant_flying_buttress/major_external_dependency/develop_internal_support)."""

EPISTEMIC_FLYING_BUTTRESS_PROMPT = """Detect epistemic flying buttress:

System: {system}
Belief: {belief}
Support: {support}
Self-support: {self_support}
Domain: {domain}
Context: {context}

Are external supports propping up beliefs that can't stand on their own? Return ONLY valid JSON."""


class EpistemicFlyingButtressService:
    """Detects epistemic flying buttresses — external supports propping up beliefs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        belief: str = "",
        support: str = "",
        self_support: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic flying buttress."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FLYING_BUTTRESS_PROMPT.format(
                system=system,
                belief=belief or "Not specified",
                support=support or "Not specified",
                self_support=self_support or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FLYING_BUTTRESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "flying_buttress_present": data.get("flying_buttress_present", False),
            "severity": data.get("severity", ""),
            "belief": data.get("belief", ""),
            "support": data.get("support", ""),
            "self_support": data.get("self_support", ""),
            "recommendation": data.get("recommendation", ""),
        }
