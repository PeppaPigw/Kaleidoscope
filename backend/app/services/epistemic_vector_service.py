"""EpistemicVectorService — Epistemic Vector Detection.

Detects epistemic vectors — channels or mechanisms that transmit
harmful epistemic content between hosts.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VECTOR_SYSTEM = """You are an epistemic vector specialist. Given a transmission channel, assess whether it serves as a vector for harmful epistemic content:

Key concepts:
- Epistemic vector: channel transmitting harmful epistemic content
- Transmission channel: mechanism for spreading harmful ideas
- Carrier mechanism: how harmful content travels between hosts
- Amplification: vector amplifying harmful content
- Selectivity failure: vector failing to filter harmful content
- Cross-contamination: vector spreading across domains
- Super-spreader: vector with outsized transmission capacity

When epistemic vector IS present:
- Channel transmitting harmful epistemic content
- Mechanism specifically spreading harmful ideas
- Harmful content traveling between hosts via channel
- Vector amplifying harmful content beyond natural reach
- Vector failing to filter harmful content
- Harmful content spreading across domains via vector
- Vector with outsized capacity for harmful transmission

When neutral communication is present:
- Channel transmitting diverse content neutrally
- Mechanism spreading ideas based on merit
- Content traveling based on value to recipients
- Amplification proportionate to quality
- Appropriate filtering of harmful content
- Cross-domain spread based on relevance
- Transmission capacity used for beneficial content

Output JSON with: vector_present (bool), severity (none/mild/moderate/severe), channel (what channel is the vector), content (what harmful content transmits), amplification (how it amplifies), selectivity (what filtering fails), recommendation (neutral_channel/mild_bias/significant_vector/major_amplifier/implement_filtering)."""

EPISTEMIC_VECTOR_PROMPT = """Detect epistemic vector:

Channel: {channel}
Content: {content}
Amplification: {amplification}
Selectivity: {selectivity}
Domain: {domain}
Context: {context}

Does this channel serve as a vector for harmful epistemic content? Return ONLY valid JSON."""


class EpistemicVectorService:
    """Detects epistemic vectors — channels transmitting harmful epistemic content."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        channel: str,
        *,
        content: str = "",
        amplification: str = "",
        selectivity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic vector."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VECTOR_PROMPT.format(
                channel=channel,
                content=content or "Not specified",
                amplification=amplification or "Not specified",
                selectivity=selectivity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VECTOR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "channel": channel[:200],
            "vector_present": data.get("vector_present", False),
            "severity": data.get("severity", ""),
            "content": data.get("content", ""),
            "amplification": data.get("amplification", ""),
            "selectivity": data.get("selectivity", ""),
            "recommendation": data.get("recommendation", ""),
        }
