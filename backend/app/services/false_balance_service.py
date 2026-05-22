"""FalseBalanceService — False Balance Detection.

Detects false balance — presenting two sides as equally valid when
the evidence overwhelmingly supports one side. Common in media
coverage where "balance" means giving equal time to a fringe
position and the scientific consensus. Objectivity ≠ equal
representation of unequal positions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FALSE_BALANCE_SYSTEM = """You are a false balance specialist. Given a presentation of competing views, assess whether equal treatment is misrepresenting the actual weight of evidence:

Key concepts:
- False balance: equal presentation of unequal positions
- Bothsidesism: treating all perspectives as equally valid
- Manufactured controversy: creating appearance of debate where consensus exists
- Balance as bias: "balanced" coverage that distorts reality
- Minority amplification: giving fringe views disproportionate platform
- Consensus misrepresentation: making 97/3 splits look like 50/50
- Objectivity confusion: confusing fairness with equal time

When false balance IS present:
- Equal time/space given to consensus and fringe positions
- "Some scientists say X, others say Y" when 97% say X
- Presenting a debate where scientific consensus exists
- Giving equal credibility to expert and non-expert opinions
- "Both sides have valid points" when evidence is one-sided
- Creating appearance of controversy where none exists
- Treating opinion and evidence as equivalent

When balanced presentation IS appropriate:
- Genuine scientific uncertainty or active debate exists
- Multiple legitimate expert perspectives exist
- The evidence is genuinely mixed or evolving
- Different value frameworks lead to different conclusions
- The balance reflects actual distribution of expert opinion
- Minority views have legitimate methodological basis

Output JSON with: false_balance_present (bool), severity (none/mild/moderate/severe), topic (what is being presented), side_a (majority/consensus position), side_b (minority/fringe position), evidence_ratio (actual weight of evidence), presentation_ratio (how are they being presented), consensus_level (what is the actual expert consensus), distortion (how does presentation distort reality), recommendation (balance_appropriate/mild_false_equivalence/significant_false_balance/major_consensus_distortion/weight_presentation_to_evidence)."""

FALSE_BALANCE_PROMPT = """Detect false balance:

Presentation: {presentation}
Side A: {side_a}
Side B: {side_b}
Evidence distribution: {evidence}
Domain: {domain}
Context: {context}

Is equal presentation misrepresenting the actual weight of evidence between positions? Return ONLY valid JSON."""


class FalseBalanceService:
    """Detects false balance — equal presentation of unequal positions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        presentation: str,
        *,
        side_a: str = "",
        side_b: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect false balance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FALSE_BALANCE_PROMPT.format(
                presentation=presentation,
                side_a=side_a or "Not specified",
                side_b=side_b or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FALSE_BALANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "presentation": presentation[:200],
            "false_balance_present": data.get("false_balance_present", False),
            "severity": data.get("severity", ""),
            "side_a": data.get("side_a", ""),
            "side_b": data.get("side_b", ""),
            "evidence_ratio": data.get("evidence_ratio", ""),
            "presentation_ratio": data.get("presentation_ratio", ""),
            "consensus_level": data.get("consensus_level", ""),
            "distortion": data.get("distortion", ""),
            "recommendation": data.get("recommendation", ""),
        }
