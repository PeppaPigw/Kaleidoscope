"""PublicationBiasService — Publication Bias Detection.

Detects publication bias — the systematic tendency for positive/
significant results to be published while null/negative results
remain in the file drawer. Rosenthal (1979). Distorts the
evidence base by making effects appear larger and more consistent
than they actually are. The "file drawer problem."
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PUBLICATION_SYSTEM = """You are a publication bias specialist. Given a body of evidence or literature review, assess whether publication bias is distorting the apparent state of knowledge:

Key concepts (Rosenthal, 1979; Sterling, 1959):
- Publication bias: positive results published, null results filed away
- File drawer problem: for every published positive study, N unpublished null studies exist
- Positive result bias: journals prefer significant findings
- Outcome reporting bias: reporting only the outcomes that "worked"
- P-hacking: analyzing data until p < 0.05, then publishing only that analysis
- Funnel plot asymmetry: visual indicator of publication bias in meta-analyses
- Decline effect: effects shrink over time as initial inflated estimates regress

When publication bias IS likely:
- Only positive/significant results are cited
- No null results are mentioned or acknowledged
- Effect sizes seem too consistent across studies
- The literature shows no failed replications
- Results come primarily from small studies (large effects in small samples)
- The field has strong incentives for positive results

When the evidence base IS likely unbiased:
- Pre-registered studies with committed outcomes
- Registered reports (accepted before results known)
- Null results are published and cited
- Meta-analyses show symmetric funnel plots
- Large-scale replications confirm effects
- Multiple independent labs report consistent results

Output JSON with: publication_bias_likely (bool), severity (none/mild/moderate/severe), evidence_examined (what body of evidence is being assessed), positive_results_count (how many positive findings), null_results_count (how many null/negative findings), ratio_suspicious (bool — is the positive/null ratio implausible?), file_drawer_estimate (how many unpublished null results likely exist), effect_size_inflation (how much the true effect is likely inflated), funnel_asymmetry (bool — would a funnel plot be asymmetric?), pre_registration (bool — were studies pre-registered?), replication_status (have findings been independently replicated?), incentive_structure (what incentives exist for positive results), decline_effect (bool — have effects shrunk over time?), outcome_reporting (bool — selective outcome reporting suspected?), corrected_estimate (what the effect likely is after bias correction), recommendation (evidence_robust/mild_publication_bias/significant_bias/severe_file_drawer/treat_evidence_skeptically)."""

PUBLICATION_PROMPT = """Detect publication bias:

Evidence/Literature: {evidence}
Results reported: {results}
Study characteristics: {characteristics}
Replication status: {replication}
Domain: {domain}
Context: {context}

Is publication bias distorting this evidence base? Return ONLY valid JSON."""


class PublicationBiasService:
    """Detects publication bias — file drawer problem distorting evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evidence: str,
        *,
        results: str = "",
        characteristics: str = "",
        replication: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect publication bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PUBLICATION_PROMPT.format(
                evidence=evidence,
                results=results or "Not specified",
                characteristics=characteristics or "Not specified",
                replication=replication or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PUBLICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evidence": evidence[:200],
            "publication_bias_likely": data.get("publication_bias_likely", False),
            "severity": data.get("severity", ""),
            "evidence_examined": data.get("evidence_examined", ""),
            "positive_results_count": data.get("positive_results_count", ""),
            "null_results_count": data.get("null_results_count", ""),
            "ratio_suspicious": data.get("ratio_suspicious", False),
            "file_drawer_estimate": data.get("file_drawer_estimate", ""),
            "effect_size_inflation": data.get("effect_size_inflation", ""),
            "funnel_asymmetry": data.get("funnel_asymmetry", False),
            "pre_registration": data.get("pre_registration", False),
            "replication_status": data.get("replication_status", ""),
            "incentive_structure": data.get("incentive_structure", ""),
            "decline_effect": data.get("decline_effect", False),
            "outcome_reporting": data.get("outcome_reporting", False),
            "corrected_estimate": data.get("corrected_estimate", ""),
            "recommendation": data.get("recommendation", ""),
        }
