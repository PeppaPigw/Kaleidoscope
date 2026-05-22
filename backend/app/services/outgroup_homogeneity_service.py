"""OutGroupHomogeneityService — Out-Group Homogeneity Bias Detection.

Detects out-group homogeneity bias — perceiving members of
other groups as more similar to each other than members of
one's own group. "They're all the same." Park & Rothbart (1982).
Leads to stereotyping, reduced individuation, and unfair
generalizations about entire groups.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

OUTGROUP_HOMOGENEITY_SYSTEM = """You are an out-group homogeneity bias specialist. Given a judgment about a group, assess whether the perceiver is treating out-group members as interchangeable while recognizing diversity within their own group:

Key concepts (Park & Rothbart, 1982):
- Out-group homogeneity: "they're all the same" perception
- In-group heterogeneity: recognizing diversity within own group
- Cross-race effect: difficulty distinguishing faces of other races
- Stereotyping: applying group-level traits to individuals
- Individuation: treating people as unique individuals
- Category-based processing: using group membership as shortcut
- Contact hypothesis: more contact reduces homogeneity perception

When out-group homogeneity IS present:
- "They all think/act/look the same"
- Applying one member's behavior to the entire group
- Failing to distinguish individual differences within the out-group
- Using group stereotypes instead of individual assessment
- Surprise when an out-group member doesn't fit the stereotype
- Generalizing from limited contact with few members

When the generalization IS accurate:
- Empirical data supports the similarity claim
- The group genuinely shares the relevant characteristic
- The perceiver has extensive contact with the group
- Individual variation is acknowledged alongside the pattern
- The same standard of generalization is applied to own group

Output JSON with: outgroup_homogeneity_present (bool), severity (none/mild/moderate/severe), target_group (group being perceived as homogeneous), perceiver_group (the perceiver's group), generalization (what is being generalized), individual_variation_acknowledged (bool), contact_level (how much contact with the out-group?), stereotype_applied (what stereotype is being used?), evidence_base (what evidence supports the generalization?), same_standard_for_ingroup (bool — would they say this about their own group?), impact (consequences of the homogeneity perception), recommendation (accurate_generalization/mild_homogeneity_bias/significant_stereotyping/major_deindividuation/individuate_assessment)."""

OUTGROUP_HOMOGENEITY_PROMPT = """Detect out-group homogeneity bias:

Judgment: {judgment}
Target group: {target_group}
Generalization: {generalization}
Contact level: {contact}
Domain: {domain}
Context: {context}

Is the perceiver treating out-group members as interchangeable? Return ONLY valid JSON."""


class OutGroupHomogeneityService:
    """Detects out-group homogeneity bias — 'they're all the same' perception."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        target_group: str = "",
        generalization: str = "",
        contact: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect out-group homogeneity bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OUTGROUP_HOMOGENEITY_PROMPT.format(
                judgment=judgment,
                target_group=target_group or "Not specified",
                generalization=generalization or "Not specified",
                contact=contact or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=OUTGROUP_HOMOGENEITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "outgroup_homogeneity_present": data.get("outgroup_homogeneity_present", False),
            "severity": data.get("severity", ""),
            "target_group": data.get("target_group", ""),
            "perceiver_group": data.get("perceiver_group", ""),
            "generalization": data.get("generalization", ""),
            "individual_variation_acknowledged": data.get("individual_variation_acknowledged", True),
            "contact_level": data.get("contact_level", ""),
            "stereotype_applied": data.get("stereotype_applied", ""),
            "evidence_base": data.get("evidence_base", ""),
            "same_standard_for_ingroup": data.get("same_standard_for_ingroup", True),
            "impact": data.get("impact", ""),
            "recommendation": data.get("recommendation", ""),
        }
