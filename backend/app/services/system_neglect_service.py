"""SystemNeglectService — System Neglect Detection.

Detects system neglect — tendency to focus on individual
components or events while ignoring the system-level dynamics
that produce them. Meadows (2008). Treating symptoms rather
than causes. Optimizing parts while degrading the whole.
Missing feedback loops, delays, and emergent properties.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SYSTEM_NEGLECT_SYSTEM = """You are a system neglect specialist. Given a problem analysis or intervention, assess whether system-level dynamics are being ignored in favor of component-level thinking:

Key concepts (Meadows, 2008):
- System neglect: focusing on parts while ignoring system dynamics
- Feedback loop blindness: missing reinforcing or balancing loops
- Delay neglect: ignoring time delays between cause and effect
- Emergence blindness: missing properties that arise from interactions
- Linear thinking: assuming proportional cause-effect in nonlinear systems
- Reductionism trap: believing understanding parts = understanding whole
- Intervention myopia: fixing symptoms without addressing root causes
- Unintended consequences: actions that backfire due to system dynamics

When system neglect IS present:
- Treating symptoms repeatedly without addressing root causes
- Optimizing one metric while degrading overall system health
- Ignoring feedback loops that amplify or dampen interventions
- Assuming linear relationships in complex adaptive systems
- "Just fix X" when X is a symptom of deeper dynamics
- Missing time delays between actions and consequences
- Blaming individuals for systemic failures
- Ignoring how components interact and create emergent behavior

When component focus IS appropriate:
- The system is genuinely decomposable (no significant interactions)
- The component fix addresses the actual root cause
- System dynamics have been considered and ruled out
- The intervention accounts for feedback effects
- Time delays are short enough to be negligible
- The problem is genuinely local, not systemic

Output JSON with: system_neglect_present (bool), severity (none/mild/moderate/severe), problem (what problem is being addressed), intervention (what intervention is proposed), system_dynamics (what system dynamics are being ignored), feedback_loops (what feedback loops exist), time_delays (what delays are relevant), unintended_consequences (what could go wrong), root_cause (what is the deeper cause), recommendation (component_focus_appropriate/mild_system_neglect/significant_dynamics_ignored/major_system_blindness/map_system_dynamics)."""

SYSTEM_NEGLECT_PROMPT = """Detect system neglect:

Problem: {problem}
Intervention: {intervention}
Scope: {scope}
History: {history}
Domain: {domain}
Context: {context}

Is system-level thinking being neglected in favor of component-level fixes? Return ONLY valid JSON."""


class SystemNeglectService:
    """Detects system neglect — ignoring system dynamics in favor of component thinking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        problem: str,
        *,
        intervention: str = "",
        scope: str = "",
        history: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect system neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SYSTEM_NEGLECT_PROMPT.format(
                problem=problem,
                intervention=intervention or "Not specified",
                scope=scope or "Not specified",
                history=history or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SYSTEM_NEGLECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "problem": problem[:200],
            "system_neglect_present": data.get("system_neglect_present", False),
            "severity": data.get("severity", ""),
            "system_dynamics": data.get("system_dynamics", ""),
            "feedback_loops": data.get("feedback_loops", ""),
            "time_delays": data.get("time_delays", ""),
            "unintended_consequences": data.get("unintended_consequences", ""),
            "root_cause": data.get("root_cause", ""),
            "recommendation": data.get("recommendation", ""),
        }
