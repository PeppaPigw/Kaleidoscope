"""JustWorldService — Just-World Hypothesis Detection.

Detects the just-world hypothesis — the belief that people get
what they deserve and deserve what they get. Lerner (1980).
Leads to victim-blaming, defensive attribution, and the belief
that success always reflects merit. A cognitive bias that serves
to maintain the illusion of a fair and predictable world.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

JUST_WORLD_SYSTEM = """You are a just-world hypothesis specialist. Given a judgment about outcomes, assess whether the just-world belief is distorting attribution:

Key concepts (Lerner, 1980):
- Just-world hypothesis: belief that people get what they deserve
- Victim blaming: attributing misfortune to victim's character or actions
- Defensive attribution: "it won't happen to me because I'm different"
- Meritocracy illusion: believing all success is earned and all failure is deserved
- System justification overlap: defending the status quo as fair
- Fundamental attribution error overlap: overweighting character vs. circumstance

When just-world thinking IS distorting:
- Blaming victims for their misfortune ("they must have done something")
- Assuming successful people always earned it through merit alone
- Ignoring structural/systemic factors in outcomes
- Believing bad things only happen to bad people
- Defensive distancing from victims ("I would never...")
- Rationalizing inequality as deserved

When merit-based reasoning IS appropriate:
- Clear causal link between actions and outcomes
- Structural factors have been accounted for
- Individual agency genuinely played the primary role
- The judgment acknowledges luck and circumstance alongside merit
- No victim-blaming or defensive attribution present

Output JSON with: just_world_present (bool), severity (none/mild/moderate/severe), outcome_judged (what outcome is being evaluated), attribution (how the outcome is being explained), victim_blaming (bool — is the victim being blamed?), meritocracy_assumption (bool — is success assumed to be purely earned?), structural_factors_ignored (what systemic factors are being overlooked), defensive_attribution (bool — distancing self from victim?), character_vs_circumstance (is character overweighted vs. circumstance?), evidence_for_merit (what evidence supports merit-based explanation), evidence_for_luck (what evidence supports luck/structural explanation), emotional_function (what psychological need does the belief serve?), consequences (what harm does this attribution cause?), recommendation (attribution_appropriate/mild_just_world/significant_just_world/major_victim_blaming/consider_structural_factors)."""

JUST_WORLD_PROMPT = """Detect just-world hypothesis:

Outcome being judged: {outcome}
Attribution given: {attribution}
Structural factors: {structural}
Subject: {subject}
Domain: {domain}
Context: {context}

Is just-world thinking distorting the attribution of this outcome? Return ONLY valid JSON."""


class JustWorldService:
    """Detects just-world hypothesis — belief that people get what they deserve."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        outcome: str,
        *,
        attribution: str = "",
        structural: str = "",
        subject: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect just-world hypothesis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=JUST_WORLD_PROMPT.format(
                outcome=outcome,
                attribution=attribution or "Not specified",
                structural=structural or "Not specified",
                subject=subject or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=JUST_WORLD_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "outcome": outcome[:200],
            "just_world_present": data.get("just_world_present", False),
            "severity": data.get("severity", ""),
            "attribution": data.get("attribution", ""),
            "victim_blaming": data.get("victim_blaming", False),
            "meritocracy_assumption": data.get("meritocracy_assumption", False),
            "structural_factors_ignored": data.get("structural_factors_ignored", ""),
            "defensive_attribution": data.get("defensive_attribution", False),
            "character_vs_circumstance": data.get("character_vs_circumstance", ""),
            "evidence_for_merit": data.get("evidence_for_merit", ""),
            "evidence_for_luck": data.get("evidence_for_luck", ""),
            "emotional_function": data.get("emotional_function", ""),
            "consequences": data.get("consequences", ""),
            "recommendation": data.get("recommendation", ""),
        }
