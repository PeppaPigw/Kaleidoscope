"""MisinformationEffectService — Misinformation Effect Detection.

Detects misinformation effect — tendency for post-event
information to interfere with memory of the original event.
Loftus (1975). Misleading questions or subsequent information
alter what people remember. "Did you see THE broken headlight?"
vs "Did you see A broken headlight?" changes memory.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MISINFORMATION_SYSTEM = """You are a misinformation effect specialist. Given a memory or recollection, assess whether post-event information has contaminated the original memory:

Key concepts (Loftus, 1975):
- Misinformation effect: post-event info alters memory
- Memory conformity: adopting others' versions of events
- Source confusion: not distinguishing original from later info
- Leading questions: questions that suggest specific answers
- Retroactive interference: new info overwriting old memory
- Memory blending: combining original and post-event information
- Confidence inflation: misinformation increasing memory confidence

When misinformation effect IS present:
- Memories that incorporate details from later discussions
- "I remember seeing X" when X was only mentioned afterward
- Recollections that match media reports rather than original experience
- Details that were suggested by questions becoming "memories"
- Group discussions altering individual memories
- Confidence in memories that include post-event details
- "Everyone says it happened that way" replacing original memory

When the memory IS reliable:
- The recollection predates any post-event information
- The person distinguishes what they saw from what they heard later
- Multiple independent sources confirm the same details
- The memory was recorded before contaminating information
- The person acknowledges uncertainty about post-event details

Output JSON with: misinformation_present (bool), severity (none/mild/moderate/severe), memory (what is being remembered), original_event (what actually happened), post_event_info (what information came later), contamination (how has the memory been altered), source_confusion (is the person confusing sources), confidence_level (how confident in the contaminated memory), recommendation (memory_reliable/mild_contamination/significant_misinformation/major_memory_distortion/verify_against_original_records)."""

MISINFORMATION_PROMPT = """Detect misinformation effect:

Memory: {memory}
Original event: {original}
Later information: {later_info}
Sources: {sources}
Domain: {domain}
Context: {context}

Has post-event information contaminated the original memory? Return ONLY valid JSON."""


class MisinformationEffectService:
    """Detects misinformation effect — post-event info altering memories."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        memory: str,
        *,
        original: str = "",
        later_info: str = "",
        sources: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect misinformation effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MISINFORMATION_PROMPT.format(
                memory=memory,
                original=original or "Not specified",
                later_info=later_info or "Not specified",
                sources=sources or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MISINFORMATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "memory": memory[:200],
            "misinformation_present": data.get("misinformation_present", False),
            "severity": data.get("severity", ""),
            "original_event": data.get("original_event", ""),
            "post_event_info": data.get("post_event_info", ""),
            "contamination": data.get("contamination", ""),
            "source_confusion": data.get("source_confusion", ""),
            "confidence_level": data.get("confidence_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
