"""SelfReferenceService — Self-Reference Effect Detection.

Detects the self-reference effect — better encoding and recall
of information that relates to oneself. Rogers, Kuiper & Kirker
(1977). People remember self-relevant information far better
than other-relevant information. This can distort evidence
evaluation when personal relevance drives salience rather
than actual importance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SELF_REFERENCE_SYSTEM = """You are a self-reference effect specialist. Given an information evaluation or decision situation, assess whether self-relevance is distorting what information gets attention and weight:

Key concepts (Rogers, Kuiper & Kirker, 1977):
- Self-reference effect: self-relevant info encoded more deeply
- Self-schema: information matching self-concept gets priority
- Personal relevance bias: overweighting personally relevant data
- Egocentric encoding: processing through lens of personal experience
- Self-serving recall: better memory for self-flattering information
- Autobiographical memory advantage: personal stories trump statistics
- Anecdotal evidence preference: own experience over base rates

When the self-reference effect IS distorting:
- Overweighting evidence because it matches personal experience
- "That happened to me too" as primary evaluation criterion
- Dismissing data that doesn't match personal narrative
- Using personal anecdotes to override statistical evidence
- Remembering only the parts of a report that relate to oneself
- Evaluating proposals based on personal impact rather than merit
- "I can relate to this" driving credibility judgments

When self-reference IS appropriate:
- Personal experience provides genuinely relevant context
- Self-knowledge helps calibrate uncertainty
- The decision genuinely is about personal fit
- Lived experience reveals flaws in abstract models
- Self-awareness improves metacognitive accuracy

Output JSON with: self_reference_present (bool), severity (none/mild/moderate/severe), situation (what is being evaluated), self_relevant_info (what information relates to self), other_info (what non-self-relevant information exists), weighting_distortion (how is self-relevance distorting weights), personal_narrative (what personal story is dominating), objective_importance (what actually matters most), recommendation (self_reference_appropriate/mild_personal_bias/significant_self_reference_effect/major_egocentric_evaluation/weight_by_relevance_not_relatability)."""

SELF_REFERENCE_PROMPT = """Detect self-reference effect:

Situation: {situation}
Personal connection: {personal}
Evidence available: {evidence}
Weighting: {weighting}
Domain: {domain}
Context: {context}

Is self-relevance causing disproportionate attention to or weighting of certain information? Return ONLY valid JSON."""


class SelfReferenceService:
    """Detects self-reference effect — self-relevance distorting information weighting."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        personal: str = "",
        evidence: str = "",
        weighting: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect self-reference effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SELF_REFERENCE_PROMPT.format(
                situation=situation,
                personal=personal or "Not specified",
                evidence=evidence or "Not specified",
                weighting=weighting or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SELF_REFERENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "self_reference_present": data.get("self_reference_present", False),
            "severity": data.get("severity", ""),
            "self_relevant_info": data.get("self_relevant_info", ""),
            "other_info": data.get("other_info", ""),
            "weighting_distortion": data.get("weighting_distortion", ""),
            "personal_narrative": data.get("personal_narrative", ""),
            "objective_importance": data.get("objective_importance", ""),
            "recommendation": data.get("recommendation", ""),
        }
