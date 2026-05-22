"""GroupthinkAmplificationService — Groupthink Amplification Detection.

Detects groupthink amplification — group dynamics that amplify rather
than correct errors, where the group makes individuals more wrong
rather than leveraging collective intelligence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GROUPTHINK_AMPLIFICATION_SYSTEM = """You are a groupthink amplification specialist. Given a group process, assess whether group dynamics are amplifying errors:

Key concepts:
- Groupthink amplification: group makes errors worse
- Error amplification: group dynamics magnify mistakes
- Collective overconfidence: group more confident than warranted
- Dissent suppression: error-correcting voices silenced
- Polarization: group moves to extremes
- Shared information bias: only shared info discussed
- Collective blind spots: group blind spots larger than individual

When groupthink amplification IS present:
- Group dynamics amplify rather than correct errors
- Collective confidence exceeds individual confidence without basis
- Dissenting voices that could correct errors suppressed
- Group polarizes toward more extreme positions
- Only shared information discussed, unique info lost
- Group blind spots larger than any individual's
- Collective intelligence fails, collective stupidity emerges

When group process is healthy:
- Diverse perspectives genuinely integrated
- Dissent welcomed and considered
- Group corrects individual errors
- Unique information surfaced and valued
- Collective intelligence exceeds individual
- Confidence calibrated to actual group knowledge
- Error correction mechanisms functioning

Output JSON with: amplification_present (bool), severity (none/mild/moderate/severe), group (what group is analyzed), error_amplified (what error is amplified), mechanism (how amplification occurs), correction_suppressed (what correction is suppressed), recommendation (healthy_group_process/mild_conformity_pressure/significant_groupthink_amplification/major_collective_error_amplification/enable_dissent_and_correction)."""

GROUPTHINK_AMPLIFICATION_PROMPT = """Detect groupthink amplification:

Group process: {process}
Decision or belief: {decision}
Dissent present: {dissent}
Error correction: {correction}
Domain: {domain}
Context: {context}

Are group dynamics amplifying rather than correcting errors? Return ONLY valid JSON."""


class GroupthinkAmplificationService:
    """Detects groupthink amplification — group dynamics amplifying errors."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        process: str,
        *,
        decision: str = "",
        dissent: str = "",
        correction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect groupthink amplification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GROUPTHINK_AMPLIFICATION_PROMPT.format(
                process=process,
                decision=decision or "Not specified",
                dissent=dissent or "Not specified",
                correction=correction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GROUPTHINK_AMPLIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "process": process[:200],
            "amplification_present": data.get("amplification_present", False),
            "severity": data.get("severity", ""),
            "error_amplified": data.get("error_amplified", ""),
            "mechanism": data.get("mechanism", ""),
            "correction_suppressed": data.get("correction_suppressed", ""),
            "recommendation": data.get("recommendation", ""),
        }
