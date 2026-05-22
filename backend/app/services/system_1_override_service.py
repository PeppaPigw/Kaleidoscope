"""System1OverrideService — System 1 Override Detection.

Detects situations where System 1 (fast, automatic, intuitive)
processing overrides System 2 (slow, deliberate, analytical)
when the situation demands careful analysis. Kahneman (2011).
The lazy controller — System 2 is supposed to monitor System 1
but often endorses intuitive answers without scrutiny, especially
under cognitive load, time pressure, or good mood.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SYSTEM_1_OVERRIDE_SYSTEM = """You are a dual-process cognition specialist. Given a decision or judgment, assess whether System 1 (fast/intuitive) is inappropriately overriding System 2 (slow/analytical):

Key concepts (Kahneman, 2011):
- System 1: fast, automatic, effortless, associative, emotional
- System 2: slow, deliberate, effortful, rule-based, logical
- Lazy controller: System 2 fails to monitor System 1 adequately
- Cognitive ease: fluent processing feels true
- WYSIATI: What You See Is All There Is
- Substitution: answering easier question instead of hard one
- Ego depletion: System 2 weakened by prior effort
- Cognitive load: System 2 occupied, System 1 takes over

When System 1 override IS problematic:
- Complex decisions made on gut feeling alone
- Statistical/logical problems answered intuitively
- Important judgments made under cognitive load
- "It just feels right" for consequential choices
- Pattern matching where base rates matter
- Emotional reactions driving analytical decisions
- Time pressure forcing heuristic answers on complex problems

When System 1 dominance IS appropriate:
- Expert intuition in domains with valid cues and practice
- Rapid decisions where speed matters more than precision
- Social interactions requiring fluid responses
- Well-learned skills operating automatically
- Low-stakes decisions not worth deliberative effort
- Emergency responses requiring immediate action

Output JSON with: system1_override_present (bool), severity (none/mild/moderate/severe), decision (what is being decided), system1_response (what intuition suggests), system2_needed (why deliberation is needed), override_mechanism (what allows System 1 to dominate), conditions (what conditions enable the override — load/pressure/ease/mood), stakes (how consequential is the decision), recommendation (intuition_appropriate/mild_system1_bias/significant_override/major_analytical_failure/engage_system2_processing)."""

SYSTEM_1_OVERRIDE_PROMPT = """Detect System 1 override:

Decision: {decision}
Process: {process}
Conditions: {conditions}
Stakes: {stakes}
Domain: {domain}
Context: {context}

Is System 1 (intuitive) inappropriately overriding System 2 (analytical) for a decision that requires deliberation? Return ONLY valid JSON."""


class System1OverrideService:
    """Detects System 1 override — intuition dominating where analysis is needed."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        process: str = "",
        conditions: str = "",
        stakes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect System 1 override."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SYSTEM_1_OVERRIDE_PROMPT.format(
                decision=decision,
                process=process or "Not specified",
                conditions=conditions or "Not specified",
                stakes=stakes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SYSTEM_1_OVERRIDE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "system1_override_present": data.get("system1_override_present", False),
            "severity": data.get("severity", ""),
            "system1_response": data.get("system1_response", ""),
            "system2_needed": data.get("system2_needed", ""),
            "override_mechanism": data.get("override_mechanism", ""),
            "conditions": data.get("conditions", ""),
            "stakes": data.get("stakes", ""),
            "recommendation": data.get("recommendation", ""),
        }
