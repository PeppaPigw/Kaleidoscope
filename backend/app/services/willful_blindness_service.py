"""WillfulBlindnessService — Willful Blindness Detection.

Detects willful blindness — choosing not to know something
that one could and should know. Heffernan (2011). Unlike
strategic ignorance (avoiding future info), willful blindness
is about refusing to see what's already visible. "I didn't
want to see it." Turning a blind eye to problems, risks,
or ethical violations that are plainly evident.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WILLFUL_BLINDNESS_SYSTEM = """You are a willful blindness specialist. Given a situation where obvious information is being ignored, assess whether someone is deliberately not seeing what's plainly visible:

Key concepts (Heffernan, 2011):
- Willful blindness: refusing to see what's visible
- Motivated not-seeing: psychological incentives to ignore
- Organizational blindness: systemic refusal to acknowledge problems
- Complicity through ignorance: enabling by not seeing
- Red flags ignored: warning signs deliberately overlooked
- Comfortable ignorance: preferring not to confront reality
- Legal concept: "should have known" standard

When willful blindness IS present:
- Obvious problems that everyone can see but no one acknowledges
- "I had no idea" when the signs were clearly visible
- Ignoring red flags because acknowledging them requires action
- Organizational culture of not asking uncomfortable questions
- "Don't ask, don't tell" about known problems
- Refusing to look at data that would reveal issues
- "Everything is fine" when evidence clearly says otherwise

When not seeing IS understandable:
- The information genuinely wasn't available or visible
- Cognitive load made the signal genuinely hard to detect
- The person lacked the expertise to interpret the signs
- The signs were genuinely ambiguous
- Reasonable people could disagree about what the evidence shows

Output JSON with: willful_blindness_present (bool), severity (none/mild/moderate/severe), situation (what is being ignored), visible_evidence (what evidence is plainly visible), motivation_to_ignore (why is it being ignored), consequences (what are the consequences of not seeing), should_have_known (would a reasonable person have seen it), organizational_factor (is this systemic), recommendation (genuinely_not_visible/mild_avoidance/significant_willful_blindness/major_deliberate_ignorance/confront_the_evidence)."""

WILLFUL_BLINDNESS_PROMPT = """Detect willful blindness:

Situation: {situation}
Evidence: {evidence}
Response: {response}
Incentives: {incentives}
Domain: {domain}
Context: {context}

Is someone deliberately not seeing what's plainly visible? Return ONLY valid JSON."""


class WillfulBlindnessService:
    """Detects willful blindness — refusing to see plainly visible information."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        evidence: str = "",
        response: str = "",
        incentives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect willful blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WILLFUL_BLINDNESS_PROMPT.format(
                situation=situation,
                evidence=evidence or "Not specified",
                response=response or "Not specified",
                incentives=incentives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=WILLFUL_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "willful_blindness_present": data.get("willful_blindness_present", False),
            "severity": data.get("severity", ""),
            "visible_evidence": data.get("visible_evidence", ""),
            "motivation_to_ignore": data.get("motivation_to_ignore", ""),
            "consequences": data.get("consequences", ""),
            "should_have_known": data.get("should_have_known", ""),
            "organizational_factor": data.get("organizational_factor", ""),
            "recommendation": data.get("recommendation", ""),
        }
