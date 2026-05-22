"""FirehoseOfFalsehood Service — Firehose of Falsehood Detection.

Detects firehose of falsehood — a propaganda technique that floods
the information environment with a high volume of messages across
many channels, with no regard for truth or consistency. RAND (2016).
The goal is not to convince but to confuse, exhaust, and undermine
the very concept of truth.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FIREHOSE_SYSTEM = """You are a firehose of falsehood specialist. Given an information environment, assess whether it exhibits the characteristics of deliberate information flooding:

Key concepts (RAND, 2016):
- Firehose of falsehood: high volume, multichannel, no regard for truth
- Volume over accuracy: quantity matters more than quality
- Consistency irrelevant: contradictory messages are fine
- First mover advantage: getting there first matters more than being right
- Exhaustion strategy: overwhelm capacity to fact-check
- Truth nihilism: goal is to make truth seem unknowable
- Channel saturation: same messages across all available channels

When firehose IS present:
- High volume of claims with no quality control
- Contradictory messages from the same source
- Speed prioritized over accuracy
- Multiple channels used simultaneously
- No corrections or retractions when proven wrong
- Goal appears to be confusion rather than persuasion
- Volume exceeds any capacity to fact-check

When high information volume IS appropriate:
- The volume reflects genuine complexity of the topic
- Claims are sourced and verifiable
- Contradictions are acknowledged and explained
- Corrections are issued when errors are found
- The goal is to inform, not to overwhelm
- Quality control exists even at high volume
- The information is consistent across channels

Output JSON with: firehose_present (bool), severity (none/mild/moderate/severe), environment (the information environment), volume (how much information), consistency (are messages consistent), corrections (are errors corrected), goal (inform vs confuse), channels (how many channels), recommendation (volume_appropriate/mild_flooding/significant_firehose/major_truth_nihilism/reduce_volume_increase_quality)."""

FIREHOSE_PROMPT = """Detect firehose of falsehood:

Environment: {environment}
Volume: {volume}
Consistency: {consistency}
Corrections: {corrections}
Domain: {domain}
Context: {context}

Does this information environment exhibit deliberate flooding with disregard for truth? Return ONLY valid JSON."""


class FirehoseOfFalsehoodService:
    """Detects firehose of falsehood — information flooding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        environment: str,
        *,
        volume: str = "",
        consistency: str = "",
        corrections: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect firehose of falsehood."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FIREHOSE_PROMPT.format(
                environment=environment,
                volume=volume or "Not specified",
                consistency=consistency or "Not specified",
                corrections=corrections or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FIREHOSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "environment": environment[:200],
            "firehose_present": data.get("firehose_present", False),
            "severity": data.get("severity", ""),
            "volume": data.get("volume", ""),
            "consistency": data.get("consistency", ""),
            "goal": data.get("goal", ""),
            "channels": data.get("channels", ""),
            "recommendation": data.get("recommendation", ""),
        }
