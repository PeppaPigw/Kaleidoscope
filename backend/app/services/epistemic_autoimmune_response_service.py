"""EpistemicAutoimmunResponseService — Epistemic Autoimmune Response Detection.

Detects epistemic autoimmune response — intellectual defense system
attacking its own ideas, mistaking self for threat.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AUTOIMMUNE_RESPONSE_SYSTEM = """You are an epistemic autoimmune response specialist. Given an intellectual defense system, assess whether it attacks its own ideas:

Key concepts:
- Epistemic autoimmune response: defense system attacking own ideas
- Self-antigen: own ideas being targeted
- Molecular mimicry: external threat resembling self
- Regulatory failure: loss of self-tolerance
- Tissue damage: destruction of healthy intellectual tissue
- Flare: periodic intensification of self-attack
- Immunosuppression: dampening the overactive response

When epistemic autoimmune response IS present:
- Intellectual defense system attacking its own ideas
- Own ideas being targeted as threats
- External threats resembling internal ideas causing confusion
- Loss of ability to distinguish self from non-self
- Destruction of healthy intellectual content
- Periodic intensification of self-attack
- Need to dampen the overactive response

When healthy immunity is present:
- Defense system only attacking external threats
- Own ideas recognized and protected
- Clear distinction between self and non-self
- Self-tolerance maintained
- Healthy content preserved
- Stable defense response
- No suppression needed

Output JSON with: autoimmune_response_present (bool), severity (none/mild/moderate/severe), self_antigen (what own ideas targeted), molecular_mimicry (what resemblance confusion), regulatory_failure (what tolerance loss), tissue_damage (what healthy destruction), recommendation (healthy_immunity/mild_autoimmune/significant_autoimmune_response/major_self_attack/restore_self_tolerance)."""

EPISTEMIC_AUTOIMMUNE_RESPONSE_PROMPT = """Detect epistemic autoimmune response:

Self-antigen: {self_antigen}
Molecular mimicry: {molecular_mimicry}
Regulatory failure: {regulatory_failure}
Tissue damage: {tissue_damage}
Domain: {domain}
Context: {context}

Is the intellectual defense system attacking its own ideas, mistaking self for threat? Return ONLY valid JSON."""


class EpistemicAutoimmunResponseService:
    """Detects epistemic autoimmune response — defense attacking own ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        self_antigen: str,
        *,
        molecular_mimicry: str = "",
        regulatory_failure: str = "",
        tissue_damage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic autoimmune response."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AUTOIMMUNE_RESPONSE_PROMPT.format(
                self_antigen=self_antigen,
                molecular_mimicry=molecular_mimicry or "Not specified",
                regulatory_failure=regulatory_failure or "Not specified",
                tissue_damage=tissue_damage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AUTOIMMUNE_RESPONSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "self_antigen": self_antigen[:200],
            "autoimmune_response_present": data.get("autoimmune_response_present", False),
            "severity": data.get("severity", ""),
            "molecular_mimicry": data.get("molecular_mimicry", ""),
            "regulatory_failure": data.get("regulatory_failure", ""),
            "tissue_damage": data.get("tissue_damage", ""),
            "recommendation": data.get("recommendation", ""),
        }
