"""ReplicationPredictorService — Replication Crisis Early Warning.

Predicts whether a research finding will replicate based on known risk
factors from the replication crisis literature: sample size, effect size,
p-value distribution, methodology flexibility, publication bias signals,
and domain-specific base rates.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REPLICATION_SYSTEM = """You are a replication crisis expert. Given a research finding, predict its replication probability based on known risk factors.

Key risk factors (from Ioannidis 2005, Open Science Collaboration 2015, etc.):
- Small sample size (underpowered studies)
- Small effect size (harder to detect reliably)
- P-value just below 0.05 (p-hacking signal)
- High researcher degrees of freedom (flexible analysis)
- Hot field with many competing teams (publication bias)
- No pre-registration
- Single study (no internal replication)
- Surprising/counterintuitive finding (prior probability low)
- Complex methodology (more things to go wrong)
- Domain base rate (psychology ~50%, cancer biology ~60%, economics ~60%)

Output JSON with: replication_assessment.finding, replication_assessment.predicted_replication_probability (0-1), replication_assessment.risk_factors (list of factor/severity critical|high|medium|low/contribution_to_risk 0-1/evidence), replication_assessment.protective_factors (list of factor/strength 0-1), replication_assessment.red_flags (list), replication_assessment.domain_base_rate (0-1), replication_assessment.confidence_in_prediction (0-1), replication_assessment.recommendations (list of action to improve replicability), replication_assessment.verdict (highly_likely|likely|uncertain|unlikely|very_unlikely)."""

REPLICATION_PROMPT = """Assess replication probability:

Finding: {finding}
Domain: {domain}

Methodology details:
{methodology_text}

Statistical details:
{stats_text}

Study characteristics:
{characteristics_text}

Predict replication probability. Return ONLY valid JSON."""

METHODOLOGY_AUDIT_SYSTEM = """You are a methodology auditor assessing research design quality. Identify specific methodological weaknesses that threaten validity and replicability.

Output JSON with: methodology_audit.design_quality (0-1), methodology_audit.internal_validity_threats (list of threat/severity/how_it_could_bias), methodology_audit.external_validity_threats (list), methodology_audit.statistical_concerns (list of concern/severity/recommendation), methodology_audit.researcher_degrees_of_freedom (list of decision_point/alternatives_available/impact), methodology_audit.missing_controls (list), methodology_audit.overall_rigor (exemplary|strong|adequate|weak|critically_flawed), methodology_audit.improvement_priority (ordered list of what to fix first)."""

METHODOLOGY_AUDIT_PROMPT = """Audit this methodology:

Research question: {question}
Method: {method}
Sample: {sample}
Analysis: {analysis}
Controls: {controls}

Identify methodological weaknesses. Return ONLY valid JSON."""


class ReplicationPredictorService:
    """Predicts replication probability and methodology quality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def predict_replication(
        self,
        finding: str,
        *,
        domain: str = "",
        methodology: str = "",
        sample_size: str = "",
        effect_size: str = "",
        p_value: str = "",
        pre_registered: bool | None = None,
        characteristics: list[str] | None = None,
    ) -> dict:
        """Predict whether a finding will replicate."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        methodology_text = methodology or "Not specified"
        stats_parts = []
        if sample_size:
            stats_parts.append(f"Sample size: {sample_size}")
        if effect_size:
            stats_parts.append(f"Effect size: {effect_size}")
        if p_value:
            stats_parts.append(f"P-value: {p_value}")
        if pre_registered is not None:
            stats_parts.append(f"Pre-registered: {'Yes' if pre_registered else 'No'}")
        stats_text = "\n".join(stats_parts) or "Not provided"

        chars = characteristics or []
        characteristics_text = "\n".join(f"- {c}" for c in chars) or "Not specified"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REPLICATION_PROMPT.format(
                finding=finding,
                domain=domain or "unspecified",
                methodology_text=methodology_text,
                stats_text=stats_text,
                characteristics_text=characteristics_text,
            ),
            system=REPLICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        assessment = data.get("replication_assessment", data)

        return {
            "finding": finding,
            "replication_probability": assessment.get("predicted_replication_probability", 0),
            "verdict": assessment.get("verdict", "uncertain"),
            "risk_factors": assessment.get("risk_factors", []),
            "protective_factors": assessment.get("protective_factors", []),
            "red_flags": assessment.get("red_flags", []),
            "domain_base_rate": assessment.get("domain_base_rate", 0),
            "confidence": assessment.get("confidence_in_prediction", 0),
            "recommendations": assessment.get("recommendations", []),
        }

    async def audit_methodology(
        self,
        question: str,
        method: str,
        *,
        sample: str = "",
        analysis: str = "",
        controls: str = "",
    ) -> dict:
        """Audit research methodology for validity threats."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=METHODOLOGY_AUDIT_PROMPT.format(
                question=question,
                method=method,
                sample=sample or "Not specified",
                analysis=analysis or "Not specified",
                controls=controls or "Not specified",
            ),
            system=METHODOLOGY_AUDIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        audit = data.get("methodology_audit", data)

        return {
            "design_quality": audit.get("design_quality", 0),
            "overall_rigor": audit.get("overall_rigor", "unknown"),
            "internal_validity_threats": audit.get("internal_validity_threats", []),
            "external_validity_threats": audit.get("external_validity_threats", []),
            "statistical_concerns": audit.get("statistical_concerns", []),
            "researcher_degrees_of_freedom": audit.get("researcher_degrees_of_freedom", []),
            "missing_controls": audit.get("missing_controls", []),
            "improvement_priority": audit.get("improvement_priority", []),
        }
