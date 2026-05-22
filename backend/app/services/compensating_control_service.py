"""CompensatingControlService — Compensating Control Analysis.

Identifies when a system relies on compensating controls rather than
fixing root causes. A compensating control is a workaround that
mitigates a vulnerability without eliminating it — like putting a
guard rail on a cliff instead of moving the road. They accumulate
technical/organizational debt and create fragile safety layers.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COMPENSATING_SYSTEM = """You are a compensating control specialist. Given a system or process, assess whether it relies on compensating controls rather than root fixes:
- Are there workarounds that mitigate problems without eliminating them?
- How many layers of compensating controls have accumulated?
- What happens if one compensating control fails?
- Is the system getting more complex over time as controls are added?
- Would it be cheaper/safer to fix the root cause than maintain all the controls?

Output JSON with: compensating_controls_present (bool), severity (none/mild/moderate/severe/critical), root_problem (the underlying issue not being fixed), controls_in_place (list of: control, what_it_compensates_for, failure_mode, maintenance_cost), layers_of_compensation (how many workarounds are stacked), single_point_of_failure (bool — does one control failure expose the root problem?), complexity_cost (how much complexity the controls add), maintenance_burden (low/moderate/high/unsustainable), why_root_not_fixed (why the underlying problem persists: cost/politics/legacy/unknown), root_fix_cost (estimated cost to actually fix the root cause), control_failure_cascade (what happens when controls fail in sequence), false_sense_of_security (bool — do controls make people think the problem is solved?), debt_accumulation_rate (how fast new compensating controls are being added), normalization_of_deviance (bool — has the workaround become accepted as normal?), recommendation (controls_adequate/fix_root_cause/simplify_controls/accept_risk/emergency_fix_needed)."""

COMPENSATING_PROMPT = """Analyze compensating controls:

System/Process: {system}
Known problems: {problems}
Current controls: {controls}
Failure history: {failure_history}
Domain: {domain}
Context: {context}

Are compensating controls masking root problems? Return ONLY valid JSON."""


class CompensatingControlService:
    """Analyzes compensating controls and root cause avoidance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self,
        system: str,
        *,
        problems: str = "",
        controls: str = "",
        failure_history: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Analyze compensating controls."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COMPENSATING_PROMPT.format(
                system=system,
                problems=problems or "Not specified",
                controls=controls or "Not specified",
                failure_history=failure_history or "None noted",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COMPENSATING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "compensating_controls_present": data.get("compensating_controls_present", False),
            "severity": data.get("severity", ""),
            "root_problem": data.get("root_problem", ""),
            "controls_in_place": data.get("controls_in_place", []),
            "layers_of_compensation": data.get("layers_of_compensation", 0),
            "single_point_of_failure": data.get("single_point_of_failure", False),
            "complexity_cost": data.get("complexity_cost", ""),
            "maintenance_burden": data.get("maintenance_burden", ""),
            "why_root_not_fixed": data.get("why_root_not_fixed", ""),
            "root_fix_cost": data.get("root_fix_cost", ""),
            "control_failure_cascade": data.get("control_failure_cascade", ""),
            "false_sense_of_security": data.get("false_sense_of_security", False),
            "debt_accumulation_rate": data.get("debt_accumulation_rate", ""),
            "normalization_of_deviance": data.get("normalization_of_deviance", False),
            "recommendation": data.get("recommendation", ""),
        }
