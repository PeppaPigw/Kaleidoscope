"""EpistemicBandwidthService — Epistemic Bandwidth Detection.

Detects epistemic bandwidth — the maximum rate at which intellectual
information can be reliably transmitted through a communication channel.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BANDWIDTH_SYSTEM = """You are an epistemic bandwidth specialist. Given an intellectual communication channel, assess its maximum reliable transmission rate:

Key concepts:
- Epistemic bandwidth: maximum reliable information rate
- Throughput: actual achieved transmission rate
- Latency: delay between sending and receiving
- Bottleneck: narrowest point limiting flow
- Congestion: too many ideas competing for channel
- Quality of service: prioritizing certain ideas
- Shannon limit: theoretical maximum for channel

When epistemic bandwidth IS present:
- Maximum rate of reliable idea transmission
- Actual throughput below theoretical maximum
- Delay between idea formation and reception
- Narrow points limiting intellectual flow
- Too many ideas competing for attention
- Some ideas prioritized over others
- Approaching theoretical channel limits

When unlimited channel is present:
- No rate limitation on transmission
- Throughput matching all demands
- Zero delay in transmission
- No bottlenecks anywhere
- No competition for channel
- All ideas equally served
- Far from any theoretical limit

Output JSON with: bandwidth_present (bool), severity (none/mild/moderate/severe), throughput (what actual rate), bottleneck (what narrows flow), congestion (what competition), shannon_limit (what theoretical max), recommendation (unlimited_channel/mild_bandwidth/significant_bandwidth_limit/major_channel_constraint/expand_bandwidth)."""

EPISTEMIC_BANDWIDTH_PROMPT = """Detect epistemic bandwidth:

Throughput: {throughput}
Bottleneck: {bottleneck}
Congestion: {congestion}
Shannon limit: {shannon_limit}
Domain: {domain}
Context: {context}

Is there a maximum rate at which intellectual information can be reliably transmitted through this communication channel? Return ONLY valid JSON."""


class EpistemicBandwidthService:
    """Detects epistemic bandwidth — maximum reliable transmission rate."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        throughput: str,
        *,
        bottleneck: str = "",
        congestion: str = "",
        shannon_limit: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic bandwidth."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BANDWIDTH_PROMPT.format(
                throughput=throughput,
                bottleneck=bottleneck or "Not specified",
                congestion=congestion or "Not specified",
                shannon_limit=shannon_limit or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BANDWIDTH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "throughput": throughput[:200],
            "bandwidth_present": data.get("bandwidth_present", False),
            "severity": data.get("severity", ""),
            "bottleneck": data.get("bottleneck", ""),
            "congestion": data.get("congestion", ""),
            "shannon_limit": data.get("shannon_limit", ""),
            "recommendation": data.get("recommendation", ""),
        }
