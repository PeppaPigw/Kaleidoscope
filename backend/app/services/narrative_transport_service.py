"""NarrativeTransportService — Narrative Transport Detection.

Detects narrative transport — being so absorbed in a story that
critical evaluation is suspended. Green & Brock (2000). When
transported into a narrative, people's beliefs shift to align
with the story regardless of argument quality. The story bypasses
analytical defenses that would catch logical flaws in non-narrative form.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NARRATIVE_TRANSPORT_SYSTEM = """You are a narrative transport specialist. Given a persuasion situation, assess whether narrative absorption is bypassing critical evaluation:

Key concepts (Green & Brock, 2000):
- Narrative transport: absorption into a story world
- Reduced counterarguing: transported readers don't argue back
- Belief change: attitudes shift to match narrative
- Emotional engagement: feelings override analysis
- Identification: merging with characters reduces critical distance
- Verisimilitude: story-like framing makes claims feel true
- Sleeper effect: narrative influence persists after source forgotten

When narrative transport IS distorting:
- Anecdotes overriding statistical evidence
- Single compelling story changing policy views
- Emotional narrative preventing logical analysis
- "But this person's story shows..." trumping data
- Advertising using stories to bypass product evaluation
- Political narratives preventing policy analysis
- Case studies treated as proof rather than illustration

When narrative IS appropriate:
- Stories illustrate validated statistical patterns
- Narrative is acknowledged as one data point
- Critical evaluation occurs alongside emotional engagement
- The story is used to generate hypotheses, not prove them
- Audience maintains awareness of narrative persuasion
- Both narrative and analytical evidence are considered

Output JSON with: narrative_transport_present (bool), severity (none/mild/moderate/severe), narrative (what story is being told), persuasive_goal (what belief change is intended), critical_evaluation (is analytical thinking engaged), counterarguing (are counterarguments being generated), evidence_type (narrative vs statistical), belief_shift (what beliefs are changing), recommendation (narrative_appropriate/mild_transport_effect/significant_narrative_bypass/major_critical_suspension/engage_analytical_evaluation)."""

NARRATIVE_TRANSPORT_PROMPT = """Detect narrative transport:

Situation: {situation}
Narrative: {narrative}
Evidence type: {evidence_type}
Critical response: {critical_response}
Domain: {domain}
Context: {context}

Is narrative absorption bypassing critical evaluation of claims? Return ONLY valid JSON."""


class NarrativeTransportService:
    """Detects narrative transport — story absorption bypassing critical thinking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        narrative: str = "",
        evidence_type: str = "",
        critical_response: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect narrative transport."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NARRATIVE_TRANSPORT_PROMPT.format(
                situation=situation,
                narrative=narrative or "Not specified",
                evidence_type=evidence_type or "Not specified",
                critical_response=critical_response or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NARRATIVE_TRANSPORT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "narrative_transport_present": data.get("narrative_transport_present", False),
            "severity": data.get("severity", ""),
            "narrative": data.get("narrative", ""),
            "persuasive_goal": data.get("persuasive_goal", ""),
            "critical_evaluation": data.get("critical_evaluation", ""),
            "counterarguing": data.get("counterarguing", ""),
            "evidence_type": data.get("evidence_type", ""),
            "belief_shift": data.get("belief_shift", ""),
            "recommendation": data.get("recommendation", ""),
        }
