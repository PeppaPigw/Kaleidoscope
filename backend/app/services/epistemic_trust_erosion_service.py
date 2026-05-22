"""EpistemicTrustErosionService — Epistemic Trust Erosion Detection.

Detects epistemic trust erosion — the systematic degradation of
trust in knowledge institutions, experts, and evidence that
undermines society's capacity for collective knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TRUST_EROSION_SYSTEM = """You are an epistemic trust erosion specialist. Given a trust situation, assess whether epistemic trust is being systematically eroded:

Key concepts:
- Epistemic trust erosion: degradation of trust in knowledge sources
- Institutional credibility collapse: loss of faith in institutions
- Expert distrust: rejection of expertise as category
- Evidence nihilism: nothing counts as evidence anymore
- Trust weaponization: using distrust as political tool
- Credibility destruction: deliberately undermining sources
- Epistemic anomie: no shared basis for knowledge

When epistemic trust erosion IS present:
- Trust in knowledge institutions systematically degraded
- Expertise rejected as category not just specific experts
- Evidence itself treated as untrustworthy
- Distrust weaponized for political purposes
- Credibility of sources deliberately destroyed
- No shared epistemic foundation remains
- Society loses capacity for collective knowledge

When healthy skepticism is appropriate:
- Specific institutions questioned for specific reasons
- Expertise evaluated not rejected wholesale
- Evidence standards applied consistently
- Skepticism proportional to evidence
- Credibility assessed on track record
- Shared epistemic foundations maintained
- Questioning serves knowledge not destruction

Output JSON with: erosion_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), target (what trust is eroded), mechanism (how erosion works), consequence (what capacity is lost), recommendation (appropriate_healthy_skepticism/mild_trust_decline/significant_trust_erosion/major_epistemic_collapse/rebuild_epistemic_trust)."""

EPISTEMIC_TRUST_EROSION_PROMPT = """Detect epistemic trust erosion:

Situation: {situation}
Trust target: {target}
Erosion mechanism: {mechanism}
Current trust level: {level}
Domain: {domain}
Context: {context}

Is epistemic trust being systematically eroded, undermining collective knowledge capacity? Return ONLY valid JSON."""


class EpistemicTrustErosionService:
    """Detects epistemic trust erosion — systematic degradation of knowledge trust."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        target: str = "",
        mechanism: str = "",
        level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic trust erosion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TRUST_EROSION_PROMPT.format(
                situation=situation,
                target=target or "Not specified",
                mechanism=mechanism or "Not specified",
                level=level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TRUST_EROSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "erosion_present": data.get("erosion_present", False),
            "severity": data.get("severity", ""),
            "target": data.get("target", ""),
            "mechanism": data.get("mechanism", ""),
            "consequence": data.get("consequence", ""),
            "recommendation": data.get("recommendation", ""),
        }
