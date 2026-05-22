"""KnowledgeDecayBlindnessService — Knowledge Decay Blindness Detection.

Detects knowledge decay blindness — failing to notice that knowledge
is becoming outdated or no longer applies.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

KNOWLEDGE_DECAY_BLINDNESS_SYSTEM = """You are a knowledge decay blindness specialist. Given a knowledge application, assess whether outdated knowledge is being applied without recognizing its decay:

Key concepts:
- Knowledge decay blindness: failing to notice knowledge becoming outdated
- Stale knowledge application: applying knowledge past its expiry
- Update neglect: neglecting to update knowledge
- Temporal validity ignorance: ignoring that knowledge has temporal limits
- Obsolescence blindness: blind to knowledge becoming obsolete
- Freshness assumption: assuming knowledge remains fresh indefinitely
- Decay rate ignorance: ignoring how fast knowledge decays

When knowledge decay blindness IS present:
- Outdated knowledge applied without recognizing decay
- Knowledge used past its temporal validity
- Updates neglected despite changing conditions
- Temporal limits of knowledge ignored
- Obsolescence not recognized
- Knowledge assumed fresh without verification
- Decay rate of knowledge ignored

When appropriate knowledge management is present:
- Knowledge freshness regularly assessed
- Updates applied as conditions change
- Temporal validity acknowledged
- Obsolescence recognized and addressed
- Knowledge verified before application
- Decay rates considered in application
- Outdated knowledge retired appropriately

Output JSON with: decay_blindness_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge is affected), decay_indicators (what indicates decay), freshness (how fresh knowledge actually is), application (how outdated knowledge is applied), recommendation (appropriate_management/mild_staleness/significant_decay_blindness/major_obsolescence_blindness/verify_knowledge_freshness)."""

KNOWLEDGE_DECAY_BLINDNESS_PROMPT = """Detect knowledge decay blindness:

Knowledge: {knowledge}
Decay indicators: {indicators}
Last updated: {last_updated}
Application: {application}
Domain: {domain}
Context: {context}

Is outdated knowledge being applied without recognizing its decay? Return ONLY valid JSON."""


class KnowledgeDecayBlindnessService:
    """Detects knowledge decay blindness — failing to notice outdated knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        indicators: str = "",
        last_updated: str = "",
        application: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect knowledge decay blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=KNOWLEDGE_DECAY_BLINDNESS_PROMPT.format(
                knowledge=knowledge,
                indicators=indicators or "Not specified",
                last_updated=last_updated or "Not specified",
                application=application or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=KNOWLEDGE_DECAY_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "decay_blindness_present": data.get("decay_blindness_present", False),
            "severity": data.get("severity", ""),
            "decay_indicators": data.get("decay_indicators", ""),
            "freshness": data.get("freshness", ""),
            "application": data.get("application", ""),
            "recommendation": data.get("recommendation", ""),
        }
