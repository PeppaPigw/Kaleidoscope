"""ExpertBlindSpotService — Tragedy of the Expert Detection.

Detects when expertise creates blind spots. Experts often miss
things novices see because their mental models are too rigid,
they over-rely on domain conventions, or they dismiss anomalies
that don't fit their framework. The complement to epistemic
trespassing — here the problem is too MUCH domain immersion.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXPERT_BLIND_SYSTEM = """You are an expert blind spot specialist. Given an analysis or conclusion from an expert, assess whether expertise is creating blind spots:
- Is the expert's mental model too rigid to see anomalies?
- Are domain conventions being followed without questioning whether they still apply?
- Is the expert dismissing observations that don't fit their framework?
- Would a novice or outsider see something the expert is missing?
- Is the expert confusing "how things are usually done" with "how things should be done"?

Output JSON with: expert_blind_spot_present (bool), severity (none/mild/moderate/severe), expert_domain (the expert's field), blind_spot_type (paradigm_lock/convention_bias/anomaly_dismissal/over_specialization/curse_of_knowledge/tool_bias), what_expert_sees (how the expert frames the situation), what_expert_misses (what their expertise causes them to overlook), why_expertise_blinds (the mechanism creating the blind spot), novice_perspective (what a fresh pair of eyes might notice), paradigm_assumptions (unstated assumptions from the expert's training), dismissed_anomalies (observations the expert is ignoring or explaining away), cross_domain_insight (what another field's perspective would reveal), curse_of_knowledge (bool — is the expert unable to think like a non-expert?), tool_bias (bool — "when you have a hammer" effect?), historical_examples (times expert consensus was wrong in this domain), recommendation (trust_expert/seek_outsider_view/question_assumptions/cross_pollinate/red_team)."""

EXPERT_BLIND_PROMPT = """Detect expert blind spots:

Analysis/Conclusion: {analysis}
Expert's domain: {expert_domain}
Expert's framework: {framework}
Anomalies present: {anomalies}
Domain: {domain}
Context: {context}

Is expertise creating blind spots? Return ONLY valid JSON."""


class ExpertBlindSpotService:
    """Detects when expertise creates blind spots."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        analysis: str,
        *,
        expert_domain: str = "",
        framework: str = "",
        anomalies: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect expert blind spots."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXPERT_BLIND_PROMPT.format(
                analysis=analysis,
                expert_domain=expert_domain or "Not specified",
                framework=framework or "Not specified",
                anomalies=anomalies or "None noted",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EXPERT_BLIND_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analysis": analysis[:200],
            "expert_blind_spot_present": data.get("expert_blind_spot_present", False),
            "severity": data.get("severity", ""),
            "expert_domain": data.get("expert_domain", ""),
            "blind_spot_type": data.get("blind_spot_type", ""),
            "what_expert_sees": data.get("what_expert_sees", ""),
            "what_expert_misses": data.get("what_expert_misses", ""),
            "why_expertise_blinds": data.get("why_expertise_blinds", ""),
            "novice_perspective": data.get("novice_perspective", ""),
            "paradigm_assumptions": data.get("paradigm_assumptions", ""),
            "dismissed_anomalies": data.get("dismissed_anomalies", []),
            "cross_domain_insight": data.get("cross_domain_insight", ""),
            "curse_of_knowledge": data.get("curse_of_knowledge", False),
            "tool_bias": data.get("tool_bias", False),
            "historical_examples": data.get("historical_examples", []),
            "recommendation": data.get("recommendation", ""),
        }
