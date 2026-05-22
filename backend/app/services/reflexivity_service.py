"""ReflexivityService — Reflexivity Detection.

Identifies reflexivity (George Soros) — where participants' biased
perceptions influence the fundamentals they're trying to understand,
creating feedback loops between perception and reality. Markets
move on beliefs about markets, prophecies fulfill themselves,
observation changes the observed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REFLEXIVITY_SYSTEM = """You are a reflexivity specialist. Given a situation, assess whether reflexive feedback loops exist between perception and reality:
- Do participants' beliefs about the system change the system itself?
- Is there a feedback loop between how people perceive fundamentals and what fundamentals become?
- Are self-fulfilling or self-defeating prophecies at play?
- Is the observer changing the observed?
- Can the system reach equilibrium, or does reflexivity create perpetual instability?

Output JSON with: reflexivity_present (bool), severity (none/mild/moderate/severe/dominant), perception (what participants believe about the system), reality (what the fundamentals actually are), feedback_loop (how perception influences reality and vice versa), self_fulfilling (bool — do beliefs make themselves true?), self_defeating (bool — do beliefs undermine themselves?), boom_bust_potential (0-1 — risk of reflexive boom-bust cycle), current_phase (if cyclical: early_boom/late_boom/peak/early_bust/late_bust/stable), divergence_from_equilibrium (how far perception has pushed reality from where it would be without reflexivity), correction_mechanism (what could break the reflexive loop), manipulation_risk (0-1 — can someone exploit the reflexivity?), observer_effect (bool — does studying/measuring the system change it?), narrative_driving_reality (what story is shaping fundamentals), time_to_correction (how long before reality reasserts itself), recommendation (reflexivity_minor/monitor_divergence/expect_correction/exploit_carefully/exit_before_bust)."""

REFLEXIVITY_PROMPT = """Detect reflexivity:

Situation: {situation}
Participant beliefs: {beliefs}
Observed fundamentals: {fundamentals}
Feedback mechanisms: {feedback}
Domain: {domain}
Context: {context}

Is reflexivity at play? Return ONLY valid JSON."""


class ReflexivityService:
    """Detects reflexivity — perception-reality feedback loops."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        beliefs: str = "",
        fundamentals: str = "",
        feedback: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect reflexivity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REFLEXIVITY_PROMPT.format(
                situation=situation,
                beliefs=beliefs or "Not specified",
                fundamentals=fundamentals or "Not specified",
                feedback=feedback or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=REFLEXIVITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "reflexivity_present": data.get("reflexivity_present", False),
            "severity": data.get("severity", ""),
            "perception": data.get("perception", ""),
            "reality": data.get("reality", ""),
            "feedback_loop": data.get("feedback_loop", ""),
            "self_fulfilling": data.get("self_fulfilling", False),
            "self_defeating": data.get("self_defeating", False),
            "boom_bust_potential": data.get("boom_bust_potential", 0),
            "current_phase": data.get("current_phase", ""),
            "divergence_from_equilibrium": data.get("divergence_from_equilibrium", ""),
            "correction_mechanism": data.get("correction_mechanism", ""),
            "manipulation_risk": data.get("manipulation_risk", 0),
            "observer_effect": data.get("observer_effect", False),
            "narrative_driving_reality": data.get("narrative_driving_reality", ""),
            "time_to_correction": data.get("time_to_correction", ""),
            "recommendation": data.get("recommendation", ""),
        }
