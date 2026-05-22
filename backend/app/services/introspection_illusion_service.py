"""IntrospectionIllusionService — Introspection Illusion Detection.

Detects introspection illusion — believing you have direct access
to your own mental processes when introspection is actually
unreliable, confabulating reasons for decisions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INTROSPECTION_ILLUSION_SYSTEM = """You are an introspection illusion specialist. Given a self-report or explanation of one's own mental processes, assess whether introspection is being treated as more reliable than it is:

Key concepts:
- Introspection illusion: overconfidence in self-knowledge
- Confabulation: constructing plausible but false explanations
- Nisbett-Wilson effect: no access to actual cognitive processes
- Post-hoc rationalization: inventing reasons after the fact
- Privileged access myth: belief in direct access to own mind
- Narrative self: story we tell about our own thinking
- Unconscious processing: decisions made before conscious awareness

When introspection illusion IS present:
- Certainty about own mental processes exceeds what's warranted
- Reasons given for decisions likely confabulated
- Introspective report contradicts behavioral evidence
- Complex cognitive processes described with false precision
- Post-hoc rationalization presented as actual reasoning
- Unconscious influences denied or invisible
- Self-report treated as ground truth about cognition

When self-report is appropriate:
- Introspective claims appropriately hedged
- Behavioral evidence consistent with self-report
- Limitations of introspection acknowledged
- Simple preferences reported (not complex processes)
- Self-report used as data, not ground truth
- Alternative explanations considered
- Unconscious influences acknowledged as possible

Output JSON with: illusion_present (bool), severity (none/mild/moderate/severe), self_report (what is claimed about own mind), behavioral_evidence (what behavior actually shows), confabulation_risk (how likely the explanation is confabulated), alternative_explanation (what else might explain the behavior), recommendation (appropriate_self_report/mild_overconfidence/significant_introspection_illusion/major_confabulation/acknowledge_introspection_limits)."""

INTROSPECTION_ILLUSION_PROMPT = """Detect introspection illusion:

Self-report: {report}
Behavior observed: {behavior}
Explanation given: {explanation}
Alternative explanations: {alternatives}
Domain: {domain}
Context: {context}

Is introspection being treated as more reliable than it actually is? Return ONLY valid JSON."""


class IntrospectionIllusionService:
    """Detects introspection illusion — overconfidence in self-knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        report: str,
        *,
        behavior: str = "",
        explanation: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect introspection illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INTROSPECTION_ILLUSION_PROMPT.format(
                report=report,
                behavior=behavior or "Not specified",
                explanation=explanation or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INTROSPECTION_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "report": report[:200],
            "illusion_present": data.get("illusion_present", False),
            "severity": data.get("severity", ""),
            "behavioral_evidence": data.get("behavioral_evidence", ""),
            "confabulation_risk": data.get("confabulation_risk", ""),
            "alternative_explanation": data.get("alternative_explanation", ""),
            "recommendation": data.get("recommendation", ""),
        }
