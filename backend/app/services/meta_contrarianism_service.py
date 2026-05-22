"""MetaContrarianismService — Meta-Contrarianism Detection.

Detects meta-contrarianism — being contrarian about contrarianism
itself, a form of third-level signaling where one opposes the
contrarian position to signal even higher sophistication. The
meta-contrarian agrees with the naive position but for "deeper"
reasons, creating a spiral of signaling.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

META_CONTRARIANISM_SYSTEM = """You are a meta-contrarianism specialist. Given a position in a debate, assess whether it represents meta-contrarianism — opposing contrarians to signal higher sophistication:

Key concepts:
- Meta-contrarianism: contrarianism about contrarianism
- Signaling spiral: naive → contrarian → meta-contrarian → ...
- Third-level position: agreeing with naive view for "sophisticated" reasons
- Status signaling: positions chosen for social positioning, not truth
- Sophistication performance: complexity as social signal
- Recursive contrarianism: each level opposes the previous
- Position as identity: what you believe signals who you are

When meta-contrarianism IS present:
- Agreeing with the naive position but claiming deeper reasons
- "Actually, the contrarians are wrong and the simple view is right, but..."
- Position chosen to signal sophistication rather than track truth
- The reasoning is more about positioning than evidence
- Each level of the debate is about status rather than substance
- "I've gone through the contrarian phase and come out the other side"
- The position would change if the social dynamics changed

When sophisticated agreement IS genuine:
- The position is held for substantive reasons independent of signaling
- Evidence supports the conclusion regardless of who else holds it
- The person can articulate reasons that don't reference the debate levels
- The position would be held even without an audience
- The reasoning is about the object level, not the meta level
- Genuine expertise informs the return to the "naive" position
- The person acknowledges uncertainty rather than performing certainty

Output JSON with: meta_contrarianism_present (bool), severity (none/mild/moderate/severe), position (what position is held), level (what level of the debate), signaling (what is being signaled), substance (is there substantive reasoning), audience_dependence (would position change without audience), recommendation (position_substantive/mild_signaling/significant_meta_contrarianism/major_status_performance/evaluate_on_merits)."""

META_CONTRARIANISM_PROMPT = """Detect meta-contrarianism:

Position: {position}
Debate context: {debate}
Signaling: {signaling}
Substance: {substance}
Domain: {domain}
Context: {context}

Is this position meta-contrarian — opposing contrarians to signal sophistication rather than tracking truth? Return ONLY valid JSON."""


class MetaContrarianismService:
    """Detects meta-contrarianism — contrarianism about contrarianism."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        position: str,
        *,
        debate: str = "",
        signaling: str = "",
        substance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect meta-contrarianism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=META_CONTRARIANISM_PROMPT.format(
                position=position,
                debate=debate or "Not specified",
                signaling=signaling or "Not specified",
                substance=substance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=META_CONTRARIANISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "position": position[:200],
            "meta_contrarianism_present": data.get("meta_contrarianism_present", False),
            "severity": data.get("severity", ""),
            "level": data.get("level", ""),
            "signaling": data.get("signaling", ""),
            "substance": data.get("substance", ""),
            "audience_dependence": data.get("audience_dependence", ""),
            "recommendation": data.get("recommendation", ""),
        }
