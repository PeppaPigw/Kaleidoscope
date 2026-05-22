"""TonePolicingService — Tone Policing Detection.

Detects tone policing — dismissing or undermining an argument based
on its emotional delivery rather than its content. The focus shifts
from whether the argument is correct to whether it was expressed
in an acceptable manner.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TONE_POLICING_SYSTEM = """You are a tone policing specialist. Given a response to an argument, assess whether the argument is being dismissed based on delivery rather than content:

Key concepts:
- Tone policing: dismissing arguments based on emotional delivery
- Respectability politics: requiring "proper" expression before engaging
- Content vs. delivery: separating what is said from how it's said
- Emotional invalidation: treating emotion as disqualifying
- Power dynamic: who gets to set the rules of acceptable expression
- Deflection: shifting from substance to style
- Civility requirement: demanding calm as precondition for engagement

When tone policing IS present:
- "I'd listen if you said it more calmly"
- Dismissing valid points because of emotional delivery
- Requiring victims to be polite about their victimization
- Focusing on how something was said rather than what was said
- Using tone as an excuse not to engage with substance
- "You'd be more persuasive if..." without addressing the argument
- Treating anger as evidence of irrationality

When tone feedback IS appropriate:
- The substance has been addressed AND delivery feedback is offered
- The tone genuinely obscures the content (incoherent, not just emotional)
- The feedback is about effectiveness, not about earning the right to speak
- Both parties have equal power to set communication norms
- The tone feedback is offered alongside substantive engagement
- The context genuinely requires measured communication (negotiation, diplomacy)
- The person asked for feedback on their communication

Output JSON with: tone_policing_present (bool), severity (none/mild/moderate/severe), argument (what argument was made), response (how it was responded to), substance_addressed (was the content engaged), tone_focus (how much focus is on delivery), power_dynamic (who sets acceptable expression), recommendation (tone_feedback_appropriate/mild_deflection/significant_tone_policing/major_substance_avoidance/address_content_first)."""

TONE_POLICING_PROMPT = """Detect tone policing:

Argument: {argument}
Response: {response}
Substance: {substance}
Tone focus: {tone_focus}
Domain: {domain}
Context: {context}

Is an argument being dismissed based on emotional delivery rather than content? Return ONLY valid JSON."""


class TonePolicingService:
    """Detects tone policing — dismissing arguments based on delivery."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        response: str = "",
        substance: str = "",
        tone_focus: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect tone policing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TONE_POLICING_PROMPT.format(
                argument=argument,
                response=response or "Not specified",
                substance=substance or "Not specified",
                tone_focus=tone_focus or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TONE_POLICING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "tone_policing_present": data.get("tone_policing_present", False),
            "severity": data.get("severity", ""),
            "substance_addressed": data.get("substance_addressed", ""),
            "tone_focus": data.get("tone_focus", ""),
            "power_dynamic": data.get("power_dynamic", ""),
            "recommendation": data.get("recommendation", ""),
        }
