"""LevelsOfProcessingService — Levels of Processing Effect Detection.

Detects levels of processing violations — relying on shallow
processing when deep processing is needed for adequate retention
and understanding. Craik & Lockhart (1972). Shallow (structural/
phonemic) processing produces weak memory traces. Deep (semantic)
processing produces durable understanding. Reading without
engaging is shallow; connecting to existing knowledge is deep.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

LEVELS_OF_PROCESSING_SYSTEM = """You are a levels of processing specialist. Given an information processing or learning situation, assess whether processing depth is insufficient for the task:

Key concepts (Craik & Lockhart, 1972):
- Levels of processing: deeper processing = better retention
- Structural processing: surface features only (shallowest)
- Phonemic processing: sound-based encoding (shallow)
- Semantic processing: meaning-based encoding (deep)
- Elaborative rehearsal: connecting to existing knowledge (deepest)
- Maintenance rehearsal: simple repetition (shallow)
- Transfer-appropriate processing: depth must match retrieval needs
- Self-reference effect: relating to self produces deepest encoding

When shallow processing IS problematic:
- Reading without comprehending or connecting to prior knowledge
- Memorizing without understanding underlying principles
- Copying information without processing its meaning
- Skimming critical documents that require deep understanding
- Surface-level engagement with complex material
- Relying on recognition rather than generating understanding
- "I read it" without being able to explain or apply it

When the processing level IS appropriate:
- The task genuinely only requires surface-level familiarity
- Time constraints make deep processing impractical
- The information is supplementary, not critical
- Deep processing has already occurred and review is maintenance
- The material is already well-integrated with existing knowledge

Output JSON with: shallow_processing_present (bool), severity (none/mild/moderate/severe), situation (what is being processed), current_depth (how deeply is information being processed), required_depth (how deeply should it be processed), depth_gap (mismatch between current and required depth), retention_risk (what understanding is at risk), deeper_strategy (what would constitute deeper processing), recommendation (processing_depth_appropriate/mild_shallow_tendency/significant_depth_deficit/major_surface_only_processing/engage_at_semantic_level)."""

LEVELS_OF_PROCESSING_PROMPT = """Detect levels of processing violations:

Situation: {situation}
Processing approach: {approach}
Depth required: {depth}
Engagement: {engagement}
Domain: {domain}
Context: {context}

Is information being processed too shallowly for the retention and understanding required? Return ONLY valid JSON."""


class LevelsOfProcessingService:
    """Detects levels of processing violations — insufficient processing depth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        approach: str = "",
        depth: str = "",
        engagement: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect levels of processing violations."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=LEVELS_OF_PROCESSING_PROMPT.format(
                situation=situation,
                approach=approach or "Not specified",
                depth=depth or "Not specified",
                engagement=engagement or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=LEVELS_OF_PROCESSING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "shallow_processing_present": data.get("shallow_processing_present", False),
            "severity": data.get("severity", ""),
            "current_depth": data.get("current_depth", ""),
            "required_depth": data.get("required_depth", ""),
            "depth_gap": data.get("depth_gap", ""),
            "retention_risk": data.get("retention_risk", ""),
            "deeper_strategy": data.get("deeper_strategy", ""),
            "recommendation": data.get("recommendation", ""),
        }
