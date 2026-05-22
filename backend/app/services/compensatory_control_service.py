"""CompensatoryControlService — Compensatory Control Detection.

Detects compensatory control — perceiving external order, patterns,
or agency when personal control is threatened. Kay et al. (2008).
When people feel they lack personal control, they compensate by
perceiving order in external systems — government, God, markets,
conspiracy — anything that suggests someone or something is in charge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COMPENSATORY_CONTROL_SYSTEM = """You are a compensatory control specialist. Given a belief or perception, assess whether it reflects compensatory control — perceiving external order when personal control is threatened:

Key concepts (Kay et al., 2008):
- Compensatory control: perceiving external order when personal control is low
- Need for control: fundamental human motivation
- External agency: attributing control to God, government, markets, fate
- Pattern perception: seeing patterns in randomness when control is threatened
- Conspiracy belief: someone must be in control (even if malevolent)
- System justification: defending the system that provides order
- Illusory pattern perception: finding meaning in noise

When compensatory control IS present:
- Increased belief in controlling agents after personal control threat
- "Everything happens for a reason" after random negative events
- Conspiracy theories emerging during periods of uncertainty
- Defending institutions more strongly when personal control is low
- Seeing patterns in random data when feeling powerless
- Preferring any explanation (even sinister) over randomness
- Increased superstitious behavior during uncertainty

When external order perception IS appropriate:
- There genuinely is an organizing agent or system
- Patterns are statistically validated, not just perceived
- The belief is held consistently regardless of personal control state
- Evidence supports the existence of the external order
- The person can distinguish between order and randomness

Output JSON with: compensatory_control_present (bool), severity (none/mild/moderate/severe), belief (what external order is perceived), control_threat (what threatens personal control), compensation_mechanism (how is control being compensated), evidence_quality (what evidence supports the belief), randomness_tolerance (can the person accept randomness), trigger (what triggered the compensatory perception), recommendation (perception_evidence_based/mild_compensatory_pattern/significant_compensatory_control/major_illusory_order/acknowledge_uncertainty)."""

COMPENSATORY_CONTROL_PROMPT = """Detect compensatory control:

Belief: {belief}
Control threat: {control_threat}
Evidence: {evidence}
Timing: {timing}
Domain: {domain}
Context: {context}

Is external order being perceived as compensation for threatened personal control? Return ONLY valid JSON."""


class CompensatoryControlService:
    """Detects compensatory control — perceiving order when control is threatened."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        control_threat: str = "",
        evidence: str = "",
        timing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect compensatory control."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COMPENSATORY_CONTROL_PROMPT.format(
                belief=belief,
                control_threat=control_threat or "Not specified",
                evidence=evidence or "Not specified",
                timing=timing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COMPENSATORY_CONTROL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "compensatory_control_present": data.get("compensatory_control_present", False),
            "severity": data.get("severity", ""),
            "control_threat": data.get("control_threat", ""),
            "compensation_mechanism": data.get("compensation_mechanism", ""),
            "evidence_quality": data.get("evidence_quality", ""),
            "randomness_tolerance": data.get("randomness_tolerance", ""),
            "trigger": data.get("trigger", ""),
            "recommendation": data.get("recommendation", ""),
        }
