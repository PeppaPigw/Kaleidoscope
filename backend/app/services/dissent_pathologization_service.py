"""DissentPathologizationService — Dissent Pathologization Detection.

Detects dissent pathologization — treating disagreement as a
psychological defect, moral failing, or character flaw rather than
engaging with the substance of the dissenting position.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DISSENT_PATHOLOGIZATION_SYSTEM = """You are a dissent pathologization specialist. Given a response to disagreement, assess whether dissent is being pathologized:

Key concepts:
- Dissent pathologization: disagreement treated as defect
- Psychological dismissal: dissent attributed to psychology
- Moral framing of disagreement: dissent as moral failing
- Character attack on dissenters: questioning character not argument
- Diagnosis as dismissal: diagnosing rather than engaging
- Motivation questioning: why they disagree vs what they argue
- Dissent as symptom: disagreement as sign of problem

When dissent pathologization IS present:
- Disagreement attributed to psychological problems
- Dissent treated as moral failing
- Character of dissenter attacked instead of argument
- Disagreement diagnosed rather than engaged
- Motivation questioned instead of substance addressed
- Dissent treated as symptom of defect
- Dissenters characterized as damaged or deficient

When criticism of dissent is appropriate:
- Substance of disagreement engaged directly
- Reasoning errors identified specifically
- Evidence against position presented
- Logical problems in dissent identified
- Factual errors in dissent corrected
- Quality of dissenting argument assessed
- Disagreement treated as intellectual matter

Output JSON with: pathologization_present (bool), severity (none/mild/moderate/severe), dissent (what disagreement is expressed), response (how dissent is treated), pathology_attributed (what defect is attributed), substance_ignored (what substance is not engaged), recommendation (appropriate_engagement_with_dissent/mild_motivation_questioning/significant_dissent_pathologization/major_psychological_dismissal/engage_substance_of_disagreement)."""

DISSENT_PATHOLOGIZATION_PROMPT = """Detect dissent pathologization:

Dissent: {dissent}
Response to dissent: {response}
Engagement with substance: {engagement}
Attribution made: {attribution}
Domain: {domain}
Context: {context}

Is disagreement being treated as a psychological defect rather than engaged substantively? Return ONLY valid JSON."""


class DissentPathologizationService:
    """Detects dissent pathologization — disagreement treated as defect."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        dissent: str,
        *,
        response: str = "",
        engagement: str = "",
        attribution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect dissent pathologization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DISSENT_PATHOLOGIZATION_PROMPT.format(
                dissent=dissent,
                response=response or "Not specified",
                engagement=engagement or "Not specified",
                attribution=attribution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DISSENT_PATHOLOGIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "dissent": dissent[:200],
            "pathologization_present": data.get("pathologization_present", False),
            "severity": data.get("severity", ""),
            "response": data.get("response", ""),
            "pathology_attributed": data.get("pathology_attributed", ""),
            "substance_ignored": data.get("substance_ignored", ""),
            "recommendation": data.get("recommendation", ""),
        }
