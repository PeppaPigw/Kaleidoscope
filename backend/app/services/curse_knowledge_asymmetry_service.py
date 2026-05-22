"""CurseOfKnowledgeAsymmetryService — Curse of Knowledge Asymmetry Detection.

Detects curse of knowledge asymmetry — the inability to remember
what it's like not to know something, specifically as it creates
communication failures. Camerer, Loewenstein & Weber (1989).
Once you know something, you can't un-know it, and you
systematically overestimate how obvious it is to others.
This is the communication-failure variant, distinct from the
general curse of knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CURSE_KNOWLEDGE_ASYMMETRY_SYSTEM = """You are a curse of knowledge asymmetry specialist. Given a communication or explanation situation, assess whether the communicator is failing to account for the audience's knowledge gap:

Key concepts (Camerer, Loewenstein & Weber, 1989):
- Curse of knowledge: can't un-know what you know
- Hindsight contamination: knowledge makes things seem obvious
- Expert blind spot: forgetting what it's like to be a novice
- Assumed shared context: believing others have your background
- Jargon blindness: using specialized terms without realizing
- Explanation gap: skipping steps that seem obvious to the knower
- Tapping study: knowing the song makes tapping seem clear

When the curse IS creating communication failure:
- Explanations that skip crucial background steps
- "It's obvious that..." when it's only obvious with expertise
- Using jargon without defining it for the audience
- Frustration that others "don't get" something "simple"
- Documentation that assumes reader knowledge they don't have
- Teaching that starts at too advanced a level
- "Everyone knows that..." when they demonstrably don't

When the communication level IS appropriate:
- The audience genuinely has the assumed background
- Technical communication between peers with shared expertise
- Progressive disclosure with appropriate scaffolding
- The communicator has verified audience knowledge level
- Simplification would be condescending given the actual audience

Output JSON with: curse_asymmetry_present (bool), severity (none/mild/moderate/severe), communication (what is being communicated), assumed_knowledge (what knowledge is assumed), actual_audience (what the audience actually knows), gap (the knowledge gap being overlooked), skipped_steps (what explanation steps are missing), frustration_signal (signs of frustration with audience), recommendation (communication_appropriate/mild_assumption_gap/significant_curse_of_knowledge/major_communication_failure/bridge_the_knowledge_gap)."""

CURSE_KNOWLEDGE_ASYMMETRY_PROMPT = """Detect curse of knowledge asymmetry:

Situation: {situation}
Communication: {communication}
Audience: {audience}
Assumed knowledge: {assumed}
Domain: {domain}
Context: {context}

Is the communicator failing to account for what the audience doesn't know? Return ONLY valid JSON."""


class CurseOfKnowledgeAsymmetryService:
    """Detects curse of knowledge asymmetry — communication failures from assumed shared knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        communication: str = "",
        audience: str = "",
        assumed: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect curse of knowledge asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CURSE_KNOWLEDGE_ASYMMETRY_PROMPT.format(
                situation=situation,
                communication=communication or "Not specified",
                audience=audience or "Not specified",
                assumed=assumed or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CURSE_KNOWLEDGE_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "curse_asymmetry_present": data.get("curse_asymmetry_present", False),
            "severity": data.get("severity", ""),
            "assumed_knowledge": data.get("assumed_knowledge", ""),
            "actual_audience": data.get("actual_audience", ""),
            "gap": data.get("gap", ""),
            "skipped_steps": data.get("skipped_steps", ""),
            "frustration_signal": data.get("frustration_signal", ""),
            "recommendation": data.get("recommendation", ""),
        }
