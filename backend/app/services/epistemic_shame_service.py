"""EpistemicShameService — Epistemic Shame Weaponization Detection.

Detects epistemic shame weaponization — using shame about not
knowing to silence questions, prevent inquiry, and maintain
power over knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SHAME_SYSTEM = """You are an epistemic shame weaponization specialist. Given a knowledge interaction, assess whether shame is being used to suppress inquiry:

Key concepts:
- Epistemic shame weaponization: shame used to silence questions
- Knowledge shaming: making people feel bad for not knowing
- Question suppression: shame preventing inquiry
- Ignorance stigma: treating not-knowing as moral failure
- Expert condescension: using expertise to shame
- Intellectual intimidation: making others feel stupid
- Curiosity punishment: penalizing those who ask

When epistemic shame weaponization IS present:
- Shame used to prevent questions
- Not-knowing treated as moral failure
- Questions met with condescension
- Ignorance stigmatized rather than addressed
- Expertise used to intimidate
- Intellectual curiosity punished
- Shame maintains knowledge hierarchies

When high standards are appropriate:
- Expectations proportional to role and training
- Questions welcomed and answered
- Not-knowing treated as starting point
- Standards serve learning not shaming
- Expertise shared generously
- Curiosity encouraged
- Knowledge gaps addressed constructively

Output JSON with: shame_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), mechanism (how shame is weaponized), target (who is shamed), effect (what inquiry is suppressed), recommendation (appropriate_high_standards/mild_condescension/significant_shame_weaponization/major_inquiry_suppression/welcome_questions)."""

EPISTEMIC_SHAME_PROMPT = """Detect epistemic shame weaponization:

Situation: {situation}
Interaction: {interaction}
Response to questions: {response}
Effect on inquiry: {effect}
Domain: {domain}
Context: {context}

Is shame being used to suppress questions and maintain knowledge power? Return ONLY valid JSON."""


class EpistemicShameService:
    """Detects epistemic shame weaponization — shame used to silence inquiry."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        interaction: str = "",
        response: str = "",
        effect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic shame weaponization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SHAME_PROMPT.format(
                situation=situation,
                interaction=interaction or "Not specified",
                response=response or "Not specified",
                effect=effect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SHAME_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "shame_present": data.get("shame_present", False),
            "severity": data.get("severity", ""),
            "mechanism": data.get("mechanism", ""),
            "target": data.get("target", ""),
            "effect": data.get("effect", ""),
            "recommendation": data.get("recommendation", ""),
        }
