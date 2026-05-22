"""SemmelweisReflexService — Semmelweis Reflex Detection.

Detects the Semmelweis reflex — the reflexive rejection of new
evidence or knowledge because it contradicts established norms,
beliefs, or paradigms. Named after Ignaz Semmelweis, whose
evidence that handwashing prevented childbed fever was rejected
by the medical establishment because it contradicted the
prevailing theory. The establishment attacked the messenger
rather than examining the evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SEMMELWEIS_SYSTEM = """You are a Semmelweis reflex specialist. Given a rejection of new evidence, assess whether the Semmelweis reflex is causing reflexive dismissal:

Key concepts:
- Semmelweis reflex: automatic rejection of evidence that challenges the paradigm
- Paradigm protection: defending existing theory against anomalous data
- Messenger attack: discrediting the source rather than addressing the evidence
- Status quo defense: institutional resistance to findings that require change
- Cognitive dissonance: rejecting evidence to avoid uncomfortable implications
- Normal science resistance: Kuhn's observation that paradigms resist anomalies

When the Semmelweis reflex IS present:
- Evidence is dismissed without serious examination
- The messenger is attacked rather than the message
- Rejection is based on "that can't be right" rather than specific flaws
- The evidence would require uncomfortable changes if accepted
- Institutional/professional identity is threatened by the findings
- Ad hominem or credential attacks substitute for methodological critique

When skepticism IS appropriate:
- The evidence has genuine methodological flaws
- The claim is extraordinary and requires extraordinary evidence
- The source has a track record of unreliable claims
- The evidence contradicts well-established, multiply-confirmed findings
- Specific, substantive critiques are offered

Output JSON with: semmelweis_reflex_present (bool), severity (none/mild/moderate/severe), evidence_rejected (what evidence is being dismissed), rejection_basis (stated reason for rejection), actual_evidence_quality (how strong the evidence actually is), paradigm_threatened (what established belief is challenged), messenger_attacked (bool — is the source being discredited instead of the evidence?), institutional_resistance (bool — does acceptance require institutional change?), cognitive_dissonance (bool — is the rejection motivated by discomfort?), specific_critique (bool — are there substantive methodological objections?), what_would_change (what would need to change if evidence is accepted), historical_parallels (similar cases of initially-rejected evidence), cost_of_rejection (what is lost by dismissing the evidence), cost_of_acceptance (what changes would acceptance require), recommendation (skepticism_warranted/mild_reflexive_dismissal/significant_semmelweis_reflex/major_paradigm_protection/examine_evidence_fairly)."""

SEMMELWEIS_PROMPT = """Detect Semmelweis reflex:

Evidence rejected: {evidence}
Rejection reasoning: {rejection}
Who is rejecting: {rejector}
What's at stake: {stakes}
Domain: {domain}
Context: {context}

Is the Semmelweis reflex causing reflexive dismissal? Return ONLY valid JSON."""


class SemmelweisReflexService:
    """Detects Semmelweis reflex — reflexive rejection of paradigm-challenging evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evidence: str,
        *,
        rejection: str = "",
        rejector: str = "",
        stakes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Semmelweis reflex."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SEMMELWEIS_PROMPT.format(
                evidence=evidence,
                rejection=rejection or "Not specified",
                rejector=rejector or "Not specified",
                stakes=stakes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SEMMELWEIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evidence": evidence[:200],
            "semmelweis_reflex_present": data.get("semmelweis_reflex_present", False),
            "severity": data.get("severity", ""),
            "evidence_rejected": data.get("evidence_rejected", ""),
            "rejection_basis": data.get("rejection_basis", ""),
            "actual_evidence_quality": data.get("actual_evidence_quality", ""),
            "paradigm_threatened": data.get("paradigm_threatened", ""),
            "messenger_attacked": data.get("messenger_attacked", False),
            "institutional_resistance": data.get("institutional_resistance", False),
            "cognitive_dissonance": data.get("cognitive_dissonance", False),
            "specific_critique": data.get("specific_critique", False),
            "what_would_change": data.get("what_would_change", ""),
            "historical_parallels": data.get("historical_parallels", ""),
            "cost_of_rejection": data.get("cost_of_rejection", ""),
            "cost_of_acceptance": data.get("cost_of_acceptance", ""),
            "recommendation": data.get("recommendation", ""),
        }
