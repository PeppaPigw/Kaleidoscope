"""MethodologyAuditorService — Research Methodology Validity Audit.

Audits research methodology for internal validity, external validity,
construct validity, and statistical conclusion validity threats. Identifies
specific weaknesses and suggests improvements.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AUDIT_SYSTEM = """You are a methodology auditor. Given a research methodology description, audit it for validity threats across four dimensions:
1. Internal validity: can we trust the causal claims? (confounds, selection bias, maturation, history, instrumentation)
2. External validity: do findings generalize? (population, setting, time, treatment variation)
3. Construct validity: are we measuring what we think? (operationalization, mono-method bias, hypothesis guessing)
4. Statistical conclusion validity: are statistical inferences sound? (power, effect size, multiple comparisons, assumptions)

Output JSON with: audit.internal_validity (score 0-1, threats list with severity), audit.external_validity (score 0-1, threats list with severity), audit.construct_validity (score 0-1, threats list with severity), audit.statistical_validity (score 0-1, threats list with severity), audit.overall_score (0-1), audit.grade (A+/A/B/C/D/F), audit.critical_flaws (list of deal-breakers), audit.improvements (list of actionable fixes ranked by impact), audit.strengths (what the methodology does well)."""

AUDIT_PROMPT = """Audit this research methodology:

Study description: {description}
Methodology: {methodology}
Domain: {domain}
Sample/data: {sample}

Identify all validity threats. Return ONLY valid JSON."""


class MethodologyAuditorService:
    """Audits research methodology for validity threats."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def audit(
        self,
        description: str,
        *,
        methodology: str = "",
        domain: str = "",
        sample: str = "",
    ) -> dict:
        """Audit a research methodology for validity threats."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AUDIT_PROMPT.format(
                description=description,
                methodology=methodology or "Not specified",
                domain=domain or "research",
                sample=sample or "Not specified",
            ),
            system=AUDIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        audit = data.get("audit", data)

        return {
            "description": description[:200],
            "internal_validity": audit.get("internal_validity", {}),
            "external_validity": audit.get("external_validity", {}),
            "construct_validity": audit.get("construct_validity", {}),
            "statistical_validity": audit.get("statistical_validity", {}),
            "overall_score": audit.get("overall_score", 0),
            "grade": audit.get("grade", ""),
            "critical_flaws": audit.get("critical_flaws", []),
            "improvements": audit.get("improvements", []),
            "strengths": audit.get("strengths", []),
        }
