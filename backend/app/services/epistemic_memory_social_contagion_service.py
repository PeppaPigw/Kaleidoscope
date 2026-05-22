"""EpistemicMemorySocialContagionService — Epistemic Memory Social Contagion Detection.

Detects epistemic memory social contagion — adopting others' memories as
one's own through social influence and suggestion.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MEMORY_SOCIAL_CONTAGION_SYSTEM = """You are an epistemic memory social contagion specialist. Given social memory contagion, assess memory adoption:

Key concepts:
- Epistemic memory social contagion: adopting others' memories as own
- Co-witness contamination: witnesses adopting each other's memories
- Suggestion-based adoption: adopting suggested memories as genuine
- Social pressure conformity: conforming memories to group consensus
- Authority-suggested memories: adopting memories suggested by authorities
- Media-implanted memories: media narratives becoming personal memories
- Repeated exposure adoption: repeated hearing becoming personal memory

When epistemic memory social contagion IS present:
- Others' memories adopted as own
- Co-witness contamination active
- Suggestions adopted as genuine
- Social pressure conforming memories
- Authority suggestions adopted
- Media narratives becoming memories
- Repeated exposure creating memories

When no social contagion:
- Own memories distinguished from others'
- Witness independence maintained
- Suggestions recognized as external
- Social pressure resisted
- Authority suggestions evaluated
- Media distinguished from experience
- Repetition not creating false memories

Output JSON with: social_contagion_detected (bool), severity (none/mild/moderate/severe), co_witness_contamination (what co-witness contamination), suggestion_adoption (what suggestions adopted), social_pressure_conformity (what social pressure), authority_suggested_memories (what authority suggestions), recommendation (no_social_contagion/mild_source_independence/significant_memory_isolation/major_intensive_contamination_audit/emergency_complete_social_contagion)."""

EPISTEMIC_MEMORY_SOCIAL_CONTAGION_PROMPT = """Detect epistemic memory social contagion:

Co witness contamination: {co_witness_contamination}
Suggestion adoption: {suggestion_adoption}
Social pressure conformity: {social_pressure_conformity}
Authority suggested memories: {authority_suggested_memories}
Domain: {domain}
Context: {context}

Are others' memories being adopted as one's own through social influence? Return ONLY valid JSON."""


class EpistemicMemorySocialContagionService:
    """Detects epistemic memory social contagion — memory adoption from others."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        co_witness_contamination: str,
        *,
        suggestion_adoption: str = "",
        social_pressure_conformity: str = "",
        authority_suggested_memories: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic memory social contagion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MEMORY_SOCIAL_CONTAGION_PROMPT.format(
                co_witness_contamination=co_witness_contamination,
                suggestion_adoption=suggestion_adoption or "Not specified",
                social_pressure_conformity=social_pressure_conformity or "Not specified",
                authority_suggested_memories=authority_suggested_memories or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MEMORY_SOCIAL_CONTAGION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "co_witness_contamination": co_witness_contamination[:200],
            "social_contagion_detected": data.get("social_contagion_detected", False),
            "severity": data.get("severity", ""),
            "suggestion_adoption": data.get("suggestion_adoption", ""),
            "social_pressure_conformity": data.get("social_pressure_conformity", ""),
            "authority_suggested_memories": data.get("authority_suggested_memories", ""),
            "recommendation": data.get("recommendation", ""),
        }
