"""EpistemicPIDControllerService — Epistemic PID Controller Detection.

Detects epistemic PID controller — intellectual feedback using proportional,
integral, and derivative terms to maintain ideas at a setpoint.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PID_CONTROLLER_SYSTEM = """You are an epistemic PID controller specialist. Given an intellectual feedback system, assess whether PID control is maintaining ideas at a setpoint:

Key concepts:
- Epistemic PID controller: feedback maintaining intellectual setpoint
- Proportional: response proportional to current error
- Integral: response based on accumulated past error
- Derivative: response based on rate of error change
- Setpoint: desired intellectual state
- Overshoot: exceeding the target
- Steady-state error: persistent offset from target

When epistemic PID controller IS present:
- Feedback maintaining ideas at a desired state
- Response proportional to current deviation
- Accumulated past errors influencing correction
- Rate of change anticipating future error
- Clear desired intellectual state defined
- Overshooting the target before settling
- Persistent offset from desired state

When open-loop operation is present:
- No feedback maintaining state
- No proportional response
- No accumulated error tracking
- No rate-of-change anticipation
- No defined setpoint
- No overshoot possible
- No steady-state error concept

Output JSON with: pid_controller_present (bool), severity (none/mild/moderate/severe), proportional (what current error response), integral (what accumulated error), derivative (what rate anticipation), setpoint (what target), recommendation (open_loop/mild_feedback/significant_pid_control/major_feedback_system/tune_pid_parameters)."""

EPISTEMIC_PID_CONTROLLER_PROMPT = """Detect epistemic PID controller:

Proportional: {proportional}
Integral: {integral}
Derivative: {derivative}
Setpoint: {setpoint}
Domain: {domain}
Context: {context}

Is intellectual feedback using proportional, integral, and derivative terms to maintain ideas at a setpoint? Return ONLY valid JSON."""


class EpistemicPIDControllerService:
    """Detects epistemic PID controller — feedback maintaining setpoint."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        proportional: str,
        *,
        integral: str = "",
        derivative: str = "",
        setpoint: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic PID controller."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PID_CONTROLLER_PROMPT.format(
                proportional=proportional,
                integral=integral or "Not specified",
                derivative=derivative or "Not specified",
                setpoint=setpoint or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PID_CONTROLLER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "proportional": proportional[:200],
            "pid_controller_present": data.get("pid_controller_present", False),
            "severity": data.get("severity", ""),
            "integral": data.get("integral", ""),
            "derivative": data.get("derivative", ""),
            "setpoint": data.get("setpoint", ""),
            "recommendation": data.get("recommendation", ""),
        }
