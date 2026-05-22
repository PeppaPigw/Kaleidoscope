"""CurseOfExpertiseService — Curse of Expertise Detection.

Detects the curse of expertise — when deep knowledge makes it
impossible to remember what it's like to not know something.
Hinds (1999). Experts systematically underestimate how difficult
tasks are for novices, create incomprehensible documentation,
and design unusable interfaces. Related to curse of knowledge
but specifically about skill/expertise rather than information.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXPERTISE_CURSE_SYSTEM = """You are a curse of expertise specialist. Given a communication or design from an expert, assess whether expertise is creating barriers for non-experts:

Key concepts (Hinds, 1999):
- Curse of expertise: inability to remember what it's like to not know
- Expert blind spot overlap: but curse of expertise is about skill, not just knowledge
- Chunking: experts see patterns that novices must process element-by-element
- Tacit knowledge: experts rely on knowledge they can't articulate
- Difficulty estimation: experts systematically underestimate task difficulty for novices
- Jargon blindness: using technical terms without realizing they're opaque

When the curse of expertise IS present:
- Documentation that only makes sense if you already understand the topic
- "It's obvious" or "it's simple" for things that aren't to novices
- Skipping steps in explanations because they're "obvious"
- Interfaces designed for expert mental models
- Training that moves too fast for the audience
- Underestimating onboarding time for new team members

When expert-level communication IS appropriate:
- The audience is genuinely at the same expertise level
- The context is peer-to-peer expert communication
- Simplification would lose critical nuance
- The audience has explicitly requested expert-level detail
- Prerequisites have been verified

Output JSON with: expertise_curse_present (bool), severity (none/mild/moderate/severe), communication (what is being communicated), expert_level (how expert is the communicator), audience_level (how expert is the audience), gap (expertise gap between communicator and audience), assumed_knowledge (what knowledge is being assumed?), skipped_steps (what steps or context is being omitted?), jargon_used (technical terms used without explanation), difficulty_underestimation (how much is difficulty being underestimated?), tacit_knowledge (what implicit knowledge is required?), audience_feedback (has the audience indicated confusion?), recommendation (communication_appropriate/mild_expertise_curse/significant_gap/major_expertise_barrier/simplify_for_audience)."""

EXPERTISE_CURSE_PROMPT = """Detect curse of expertise:

Communication: {communication}
Expert's level: {expert_level}
Audience: {audience}
Feedback: {feedback}
Domain: {domain}
Context: {context}

Is expertise creating barriers for the intended audience? Return ONLY valid JSON."""


class CurseOfExpertiseService:
    """Detects curse of expertise — expert knowledge creating communication barriers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        communication: str,
        *,
        expert_level: str = "",
        audience: str = "",
        feedback: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect curse of expertise."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXPERTISE_CURSE_PROMPT.format(
                communication=communication,
                expert_level=expert_level or "Not specified",
                audience=audience or "Not specified",
                feedback=feedback or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EXPERTISE_CURSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "communication": communication[:200],
            "expertise_curse_present": data.get("expertise_curse_present", False),
            "severity": data.get("severity", ""),
            "expert_level": data.get("expert_level", ""),
            "audience_level": data.get("audience_level", ""),
            "gap": data.get("gap", ""),
            "assumed_knowledge": data.get("assumed_knowledge", ""),
            "skipped_steps": data.get("skipped_steps", ""),
            "jargon_used": data.get("jargon_used", ""),
            "difficulty_underestimation": data.get("difficulty_underestimation", ""),
            "tacit_knowledge": data.get("tacit_knowledge", ""),
            "audience_feedback": data.get("audience_feedback", ""),
            "recommendation": data.get("recommendation", ""),
        }
