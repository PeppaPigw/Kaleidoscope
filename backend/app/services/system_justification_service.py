"""SystemJustificationService — System Justification Detection.

Detects system justification — the tendency to defend and
rationalize the status quo as fair, natural, and legitimate,
even when it disadvantages you. Jost & Banaji (1994). People
prefer to believe the world is just and systems are fair,
leading them to rationalize inequality and resist change.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SYSTEM_JUST_SYSTEM = """You are a system justification specialist. Given a defense of the status quo, assess whether system justification bias is rationalizing unfairness:

Key concepts (Jost & Banaji, 1994):
- System justification: motivated defense of existing social arrangements
- Just-world belief: the world is fair, people get what they deserve
- Legitimizing myths: ideologies that justify inequality (meritocracy, natural order)
- Complementary stereotypes: "the poor are happy," "the rich are stressed"
- False consciousness: disadvantaged groups defending systems that harm them
- Status quo bias overlap: preferring current state, but with moral justification

When system justification IS present:
- Inequality is explained as natural, deserved, or inevitable
- Victims are blamed for their circumstances
- Alternatives are dismissed as utopian or dangerous
- The system is defended by those it disadvantages
- Complementary stereotypes compensate for inequality
- "That's just how things are" reasoning

When defense of the system IS appropriate:
- The system genuinely works well based on evidence
- Proposed alternatives have been tried and failed
- The defense acknowledges flaws while arguing net benefit
- Criticism is specific and evidence-based, not ideological
- Trade-offs are honestly weighed

Output JSON with: system_justification_present (bool), severity (none/mild/moderate/severe), status_quo_defended (what system/arrangement is being defended), justification_given (how it's being rationalized), who_benefits (who gains from the current arrangement), who_is_harmed (who is disadvantaged), just_world_belief (bool — assuming outcomes reflect desert?), legitimizing_myth (what ideology justifies the arrangement), complementary_stereotypes (bool — compensating narratives?), victim_blaming (bool — attributing disadvantage to personal failing?), alternatives_dismissed (how alternatives are being rejected), false_consciousness (bool — disadvantaged defending what harms them?), evidence_for_system (what genuine evidence supports the status quo), evidence_against_system (what evidence challenges it), naturalization (bool — treating social arrangements as natural/inevitable?), change_resistance_motive (what psychological need does defense serve), recommendation (defense_warranted/mild_rationalization/significant_system_justification/major_inequality_rationalization/examine_alternatives)."""

SYSTEM_JUST_PROMPT = """Detect system justification:

Defense/Argument: {defense}
System defended: {system}
Who benefits: {beneficiaries}
Who is harmed: {harmed}
Domain: {domain}
Context: {context}

Is system justification bias rationalizing unfairness? Return ONLY valid JSON."""


class SystemJustificationService:
    """Detects system justification — rationalizing the status quo as fair/natural."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        defense: str,
        *,
        system: str = "",
        beneficiaries: str = "",
        harmed: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect system justification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SYSTEM_JUST_PROMPT.format(
                defense=defense,
                system=system or "Not specified",
                beneficiaries=beneficiaries or "Not specified",
                harmed=harmed or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SYSTEM_JUST_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "defense": defense[:200],
            "system_justification_present": data.get("system_justification_present", False),
            "severity": data.get("severity", ""),
            "status_quo_defended": data.get("status_quo_defended", ""),
            "justification_given": data.get("justification_given", ""),
            "who_benefits": data.get("who_benefits", ""),
            "who_is_harmed": data.get("who_is_harmed", ""),
            "just_world_belief": data.get("just_world_belief", False),
            "legitimizing_myth": data.get("legitimizing_myth", ""),
            "complementary_stereotypes": data.get("complementary_stereotypes", False),
            "victim_blaming": data.get("victim_blaming", False),
            "alternatives_dismissed": data.get("alternatives_dismissed", ""),
            "false_consciousness": data.get("false_consciousness", False),
            "evidence_for_system": data.get("evidence_for_system", ""),
            "evidence_against_system": data.get("evidence_against_system", ""),
            "naturalization": data.get("naturalization", False),
            "change_resistance_motive": data.get("change_resistance_motive", ""),
            "recommendation": data.get("recommendation", ""),
        }
