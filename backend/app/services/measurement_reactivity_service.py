"""MeasurementReactivityService — Measurement Reactivity Detection.

Detects measurement reactivity — when the act of measuring
changes what is being measured, invalidating the measurement
as a representation of the unmeasured state.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MEASUREMENT_REACTIVITY_SYSTEM = """You are a measurement reactivity specialist. Given a measurement situation, assess whether the act of measuring is changing what is measured:

Key concepts:
- Hawthorne effect: behavior changes when people know they're observed
- Observer effect: measurement instrument affecting the measured system
- Demand characteristics: subjects guessing what's expected and conforming
- Social desirability: reporting what seems acceptable rather than true
- Heisenberg analogy: measurement disturbing the measured state
- Reflexivity: measurement feeding back into the measured system
- Unobtrusive measures: measurement that doesn't disturb the system

When measurement reactivity IS present:
- Subjects aware of being measured and changing behavior
- Measurement instrument affecting the system
- Results reflect measured state, not natural state
- Social desirability distorting responses
- Observation changing the phenomenon observed
- Feedback from measurement altering future measurements
- Measured values differ from unmeasured reality

When measurement is non-reactive:
- Subjects unaware of measurement or unaffected
- Measurement instrument doesn't disturb system
- Results represent natural state
- Multiple measurement methods converge
- Unobtrusive measures used where possible
- Reactivity effects estimated and corrected
- Measurement validated against non-reactive alternatives

Output JSON with: reactivity_present (bool), severity (none/mild/moderate/severe), measurement (what is being measured), mechanism (how measurement changes the measured), distortion (how results are distorted), natural_state (what unmeasured state would be), recommendation (non_reactive/mild_reactivity/significant_distortion/major_measurement_artifact/use_unobtrusive_measures)."""

MEASUREMENT_REACTIVITY_PROMPT = """Detect measurement reactivity:

Measurement: {measurement}
Method: {method}
Subjects: {subjects}
Awareness: {awareness}
Domain: {domain}
Context: {context}

Is the act of measuring changing what is being measured? Return ONLY valid JSON."""


class MeasurementReactivityService:
    """Detects measurement reactivity — measuring changes what is measured."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        measurement: str,
        *,
        method: str = "",
        subjects: str = "",
        awareness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect measurement reactivity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MEASUREMENT_REACTIVITY_PROMPT.format(
                measurement=measurement,
                method=method or "Not specified",
                subjects=subjects or "Not specified",
                awareness=awareness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MEASUREMENT_REACTIVITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "measurement": measurement[:200],
            "reactivity_present": data.get("reactivity_present", False),
            "severity": data.get("severity", ""),
            "mechanism": data.get("mechanism", ""),
            "distortion": data.get("distortion", ""),
            "natural_state": data.get("natural_state", ""),
            "recommendation": data.get("recommendation", ""),
        }
