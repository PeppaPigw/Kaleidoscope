"""InGroupBiasService — In-Group Bias Detection.

Detects in-group bias — favoring members of one's own group
over outsiders. Tajfel (1970). Minimal group paradigm shows
even arbitrary group membership triggers favoritism. Leads to
unfair hiring, biased evaluations, echo chambers, and
discrimination disguised as "cultural fit."
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INGROUP_SYSTEM = """You are an in-group bias specialist. Given a judgment or decision involving group membership, assess whether in-group favoritism is distorting the evaluation:

Key concepts (Tajfel, 1970; Tajfel & Turner, 1979):
- In-group bias: systematic preference for members of one's own group
- Minimal group paradigm: even trivial group distinctions trigger favoritism
- Social identity theory: self-esteem tied to group membership
- In-group favoritism: attributing positive traits to in-group members
- Out-group derogation: attributing negative traits to out-group members
- "Cultural fit": often a proxy for in-group preference
- Similarity attraction: preferring those who are like us

When in-group bias IS present:
- Evaluating in-group members more favorably with same evidence
- "Cultural fit" used without objective criteria
- Benefit of the doubt given to in-group but not out-group
- Different standards applied based on group membership
- Networking and opportunities flowing along group lines
- Dismissing out-group contributions while praising similar in-group work

When the preference IS justified:
- Objective criteria applied equally regardless of group
- Legitimate skill or experience differences explain the preference
- The evaluation is blind to group membership
- Multiple evaluators from different groups reach the same conclusion
- The criteria were established before knowing group membership

Output JSON with: ingroup_bias_present (bool), severity (none/mild/moderate/severe), decision (what is being decided), ingroup (the favored group), outgroup (the disfavored group), differential_treatment (how treatment differs), objective_criteria (what objective standards exist?), criteria_applied_equally (bool), cultural_fit_proxy (bool — is "fit" masking bias?), evidence_asymmetry (bool — different evidence standards?), structural_factors (systemic factors enabling the bias), impact (who is harmed and how?), recommendation (fair_evaluation/mild_ingroup_preference/significant_favoritism/major_discrimination/blind_evaluation_needed)."""

INGROUP_PROMPT = """Detect in-group bias:

Decision: {decision}
Groups involved: {groups}
Criteria used: {criteria}
Evidence: {evidence}
Domain: {domain}
Context: {context}

Is in-group favoritism distorting this evaluation? Return ONLY valid JSON."""


class InGroupBiasService:
    """Detects in-group bias — favoring own group members over outsiders."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        groups: str = "",
        criteria: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect in-group bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INGROUP_PROMPT.format(
                decision=decision,
                groups=groups or "Not specified",
                criteria=criteria or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INGROUP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "ingroup_bias_present": data.get("ingroup_bias_present", False),
            "severity": data.get("severity", ""),
            "ingroup": data.get("ingroup", ""),
            "outgroup": data.get("outgroup", ""),
            "differential_treatment": data.get("differential_treatment", ""),
            "objective_criteria": data.get("objective_criteria", ""),
            "criteria_applied_equally": data.get("criteria_applied_equally", True),
            "cultural_fit_proxy": data.get("cultural_fit_proxy", False),
            "evidence_asymmetry": data.get("evidence_asymmetry", False),
            "structural_factors": data.get("structural_factors", ""),
            "impact": data.get("impact", ""),
            "recommendation": data.get("recommendation", ""),
        }
