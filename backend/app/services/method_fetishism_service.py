"""MethodFetishismService — Method Fetishism Detection.

Detects method fetishism — privileging methodological form over
substance, rejecting valid findings because they used the "wrong"
method regardless of the quality of evidence produced.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

METHOD_FETISHISM_SYSTEM = """You are a method fetishism specialist. Given an evaluation, assess whether method is being privileged over substance:

Key concepts:
- Method fetishism: method valued over substance
- Methodological gatekeeping: rejecting findings for method alone
- Form over content: procedural correctness over insight
- Method-substance inversion: method becomes the goal
- Inappropriate method hierarchy: rigid ranking of methods
- Context-blind methodology: ignoring what methods suit the question
- Methodological monoculture: one method for all questions

When method fetishism IS present:
- Valid findings rejected solely for methodological form
- Method privileged regardless of question fit
- Procedural correctness valued over substantive insight
- Rigid method hierarchy applied without context
- One method demanded regardless of research question
- Methodological criticism ignores quality of evidence
- Form of inquiry valued over content of findings

When methodological rigor is appropriate:
- Method criticism addresses genuine validity threats
- Method requirements matched to research question
- Multiple methods valued for different questions
- Substance and method both considered
- Methodological standards contextually appropriate
- Quality of evidence assessed holistically
- Method serves the question, not vice versa

Output JSON with: fetishism_present (bool), severity (none/mild/moderate/severe), evaluation (what evaluation is made), method_demanded (what method is demanded), finding_rejected (what finding is rejected), substance_ignored (what substance is overlooked), recommendation (appropriate_methodological_rigor/mild_method_preference/significant_method_fetishism/major_substance_rejection/match_method_to_question)."""

METHOD_FETISHISM_PROMPT = """Detect method fetishism:

Evaluation: {evaluation}
Method demanded: {method}
Finding assessed: {finding}
Substance of finding: {substance}
Domain: {domain}
Context: {context}

Is method being privileged over substance inappropriately? Return ONLY valid JSON."""


class MethodFetishismService:
    """Detects method fetishism — privileging method over substance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        method: str = "",
        finding: str = "",
        substance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect method fetishism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=METHOD_FETISHISM_PROMPT.format(
                evaluation=evaluation,
                method=method or "Not specified",
                finding=finding or "Not specified",
                substance=substance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=METHOD_FETISHISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "fetishism_present": data.get("fetishism_present", False),
            "severity": data.get("severity", ""),
            "method_demanded": data.get("method_demanded", ""),
            "finding_rejected": data.get("finding_rejected", ""),
            "substance_ignored": data.get("substance_ignored", ""),
            "recommendation": data.get("recommendation", ""),
        }
