"""GoogleEffectService — Google Effect (Digital Amnesia) Detection.

Detects the Google effect — tendency to forget information that
is easily accessible online. Sparrow, Liu & Wegner (2011).
People remember WHERE to find information rather than the
information itself. This extends to any external memory system
(notes, bookmarks, AI assistants). Not inherently bad, but
problematic when it creates false confidence or dependency.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GOOGLE_EFFECT_SYSTEM = """You are a Google effect specialist. Given a knowledge or memory situation, assess whether reliance on external memory systems is creating problematic gaps:

Key concepts (Sparrow, Liu & Wegner, 2011):
- Google effect: forgetting information that's easily searchable
- Transactive memory: remembering where to find info rather than the info itself
- Cognitive offloading: delegating memory to external systems
- Digital amnesia: losing information when devices/systems fail
- False confidence: believing you "know" something you can only look up
- Dependency risk: inability to function without the external system

When the Google effect IS problematic:
- Critical knowledge not retained that's needed in time-sensitive situations
- False confidence in knowledge that's actually just accessibility
- Single point of failure in external memory (what if the system is down?)
- Inability to synthesize or connect ideas because details aren't in memory
- "I'll just look it up" for knowledge needed for real-time decisions
- Expertise degradation from never internalizing foundational knowledge

When external memory IS appropriate:
- The information changes frequently (prices, schedules, versions)
- The volume exceeds what any human could memorize
- The information is rarely needed and low-stakes when needed
- The external system is highly reliable and always accessible
- The person retains the conceptual framework and only offloads details
- Cognitive resources are better spent on synthesis than memorization

Output JSON with: google_effect_present (bool), severity (none/mild/moderate/severe), knowledge_type (what information is being externalized), access_reliability (how reliable is the external source?), time_sensitivity (is the knowledge needed in real-time?), false_confidence (bool — does the person think they "know" it?), synthesis_impact (does externalization prevent connecting ideas?), dependency_risk (what happens if the external system fails?), foundational_vs_detail (is this foundational knowledge or details?), cognitive_offloading_appropriate (bool — is this a good use of external memory?), expertise_impact (does this affect professional competence?), recommendation (offloading_appropriate/mild_dependency/significant_google_effect/major_knowledge_gap/internalize_critical_knowledge)."""

GOOGLE_EFFECT_PROMPT = """Detect Google effect:

Situation: {situation}
Knowledge externalized: {knowledge}
External system: {system}
Access conditions: {access}
Domain: {domain}
Context: {context}

Is reliance on external memory creating problematic knowledge gaps? Return ONLY valid JSON."""


class GoogleEffectService:
    """Detects Google effect — problematic reliance on external memory systems."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        knowledge: str = "",
        system: str = "",
        access: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Google effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GOOGLE_EFFECT_PROMPT.format(
                situation=situation,
                knowledge=knowledge or "Not specified",
                system=system or "Not specified",
                access=access or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GOOGLE_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "google_effect_present": data.get("google_effect_present", False),
            "severity": data.get("severity", ""),
            "knowledge_type": data.get("knowledge_type", ""),
            "access_reliability": data.get("access_reliability", ""),
            "time_sensitivity": data.get("time_sensitivity", ""),
            "false_confidence": data.get("false_confidence", False),
            "synthesis_impact": data.get("synthesis_impact", ""),
            "dependency_risk": data.get("dependency_risk", ""),
            "foundational_vs_detail": data.get("foundational_vs_detail", ""),
            "cognitive_offloading_appropriate": data.get("cognitive_offloading_appropriate", False),
            "expertise_impact": data.get("expertise_impact", ""),
            "recommendation": data.get("recommendation", ""),
        }
