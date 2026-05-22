"""ProcessOverOutcomeService — Process Over Outcome Detection.

Detects process over outcome bias — when following process becomes
more important than achieving results, and procedural compliance
substitutes for actual effectiveness.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PROCESS_OVER_OUTCOME_SYSTEM = """You are a process over outcome specialist. Given an organizational situation, assess whether process compliance has become more important than results:

Key concepts:
- Process fetishism: following procedure regardless of outcome
- Bureaucratic displacement: means becoming ends
- Compliance theater: appearing to follow process without substance
- Goal displacement: original goals replaced by procedural goals
- Red tape: process requirements that impede actual work
- Ritualization: process becoming ritual rather than functional
- Outcome blindness: not checking whether process achieves goals

When process over outcome IS present:
- Following procedure valued over achieving results
- Process compliance checked but outcomes not measured
- Exceptions denied even when process clearly fails
- Process requirements growing without outcome improvement
- People punished for good outcomes achieved outside process
- Process becomes ritualistic rather than functional
- Original purpose of process forgotten

When process serves outcomes:
- Process designed to achieve specific outcomes
- Process effectiveness regularly evaluated
- Exceptions allowed when process clearly fails
- Process requirements proportional to risk
- Good outcomes valued regardless of path
- Process updated when it stops serving goals
- Purpose of each process step understood

Output JSON with: bias_present (bool), severity (none/mild/moderate/severe), situation (what situation), process (what process dominates), outcome_neglected (what outcomes are ignored), displacement (how means became ends), recommendation (process_serves_outcomes/mild_proceduralism/significant_displacement/major_process_fetishism/refocus_on_outcomes)."""

PROCESS_OVER_OUTCOME_PROMPT = """Detect process over outcome bias:

Situation: {situation}
Process: {process}
Outcomes: {outcomes}
Compliance focus: {compliance}
Domain: {domain}
Context: {context}

Has following process become more important than achieving results? Return ONLY valid JSON."""


class ProcessOverOutcomeService:
    """Detects process over outcome bias — procedure over results."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        process: str = "",
        outcomes: str = "",
        compliance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect process over outcome bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PROCESS_OVER_OUTCOME_PROMPT.format(
                situation=situation,
                process=process or "Not specified",
                outcomes=outcomes or "Not specified",
                compliance=compliance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PROCESS_OVER_OUTCOME_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "bias_present": data.get("bias_present", False),
            "severity": data.get("severity", ""),
            "process": data.get("process", ""),
            "outcome_neglected": data.get("outcome_neglected", ""),
            "displacement": data.get("displacement", ""),
            "recommendation": data.get("recommendation", ""),
        }
