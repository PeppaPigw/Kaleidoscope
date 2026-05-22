"""JustProcessService — Belief in Just Process Detection.

Detects belief in a just process — assuming that fair procedures
necessarily produce fair outcomes regardless of structural bias,
unequal starting positions, or systemic factors. Procedural
justice is necessary but not sufficient for distributive justice.
"We followed the rules" doesn't mean the outcome is just.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

JUST_PROCESS_SYSTEM = """You are a just process belief specialist. Given a fairness judgment, assess whether procedural fairness is being confused with outcome fairness:

Key concepts:
- Procedural justice: fairness of the process
- Distributive justice: fairness of the outcome
- Process-outcome conflation: fair process = fair outcome (not always)
- Structural bias: systems that produce unequal outcomes despite fair rules
- Starting position inequality: equal rules on unequal playing fields
- Meritocracy myth: assuming outcomes reflect merit when process is "fair"
- Legitimation function: fair process legitimizes unfair outcomes

When just process belief IS distorting:
- "The process was fair, so the outcome must be fair"
- Ignoring structural advantages/disadvantages
- Equal rules applied to unequal situations
- Using procedural compliance to dismiss outcome concerns
- "Everyone had the same opportunity" ignoring different starting points
- Meritocratic framing that ignores systemic factors
- Process fairness used to avoid examining outcome patterns

When procedural fairness IS sufficient:
- Starting positions are genuinely equal
- The process accounts for structural differences
- Outcome patterns are monitored alongside process compliance
- Procedural fairness is one criterion among several
- Structural factors have been identified and addressed
- Both process and outcome fairness are evaluated

Output JSON with: just_process_belief_present (bool), severity (none/mild/moderate/severe), process (what process is being evaluated), outcome (what outcome resulted), structural_factors (what structural factors are ignored), starting_positions (are starting positions equal), process_fairness (is the process actually fair), outcome_fairness (is the outcome actually fair), recommendation (process_sufficient/mild_process_conflation/significant_just_process_belief/major_structural_blindness/evaluate_outcomes_independently)."""

JUST_PROCESS_PROMPT = """Detect belief in just process:

Situation: {situation}
Process: {process}
Outcome: {outcome}
Structural factors: {structural}
Domain: {domain}
Context: {context}

Is procedural fairness being confused with outcome fairness while ignoring structural factors? Return ONLY valid JSON."""


class JustProcessService:
    """Detects belief in just process — conflating fair procedures with fair outcomes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        process: str = "",
        outcome: str = "",
        structural: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect belief in just process."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=JUST_PROCESS_PROMPT.format(
                situation=situation,
                process=process or "Not specified",
                outcome=outcome or "Not specified",
                structural=structural or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=JUST_PROCESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "just_process_belief_present": data.get("just_process_belief_present", False),
            "severity": data.get("severity", ""),
            "process": data.get("process", ""),
            "outcome": data.get("outcome", ""),
            "structural_factors": data.get("structural_factors", ""),
            "starting_positions": data.get("starting_positions", ""),
            "process_fairness": data.get("process_fairness", ""),
            "outcome_fairness": data.get("outcome_fairness", ""),
            "recommendation": data.get("recommendation", ""),
        }
