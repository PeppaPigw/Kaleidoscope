"""EpistemicPeristalsisService — Epistemic Peristalsis Detection.

Detects epistemic peristalsis — ideas being moved through intellectual
channels by rhythmic contractions rather than their own momentum.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PERISTALSIS_SYSTEM = """You are an epistemic peristalsis specialist. Given an idea movement pattern, assess whether ideas are moved by rhythmic contractions rather than their own momentum:

Key concepts:
- Epistemic peristalsis: rhythmic contractions moving ideas through channels
- Contraction: force applied to move ideas along
- Channel: intellectual pathway ideas travel through
- Rhythm: regular pattern of contractions
- Bolus: package of ideas being moved
- Retrograde: ideas moving backward against normal flow
- Obstruction: blockage preventing normal peristaltic movement

When epistemic peristalsis IS present:
- Ideas moved by rhythmic external forces not their own momentum
- Regular contractions pushing ideas through channels
- Ideas packaged into boluses for transport
- Rhythmic pattern of intellectual movement
- Ideas unable to move without external contractions
- Backward movement when contractions reverse
- Blockages preventing normal idea flow

When self-propelled movement is present:
- Ideas moving under their own momentum
- No external forces needed for movement
- Ideas flowing freely without packaging
- No rhythmic pattern to movement
- Ideas capable of independent movement
- No backward movement from reversed forces
- No blockages in free-flowing movement

Output JSON with: peristalsis_present (bool), severity (none/mild/moderate/severe), contractions (what forces move ideas), channel (what pathway), rhythm (what pattern), obstruction (what blockages exist), recommendation (self_propelled/mild_assisted/significant_peristalsis/major_dependency/restore_idea_momentum)."""

EPISTEMIC_PERISTALSIS_PROMPT = """Detect epistemic peristalsis:

Contractions: {contractions}
Channel: {channel}
Rhythm: {rhythm}
Obstruction: {obstruction}
Domain: {domain}
Context: {context}

Are ideas being moved through intellectual channels by rhythmic contractions rather than their own momentum? Return ONLY valid JSON."""


class EpistemicPeristalsisService:
    """Detects epistemic peristalsis — rhythmic contractions moving ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        contractions: str,
        *,
        channel: str = "",
        rhythm: str = "",
        obstruction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic peristalsis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PERISTALSIS_PROMPT.format(
                contractions=contractions,
                channel=channel or "Not specified",
                rhythm=rhythm or "Not specified",
                obstruction=obstruction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PERISTALSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "contractions": contractions[:200],
            "peristalsis_present": data.get("peristalsis_present", False),
            "severity": data.get("severity", ""),
            "channel": data.get("channel", ""),
            "rhythm": data.get("rhythm", ""),
            "obstruction": data.get("obstruction", ""),
            "recommendation": data.get("recommendation", ""),
        }
