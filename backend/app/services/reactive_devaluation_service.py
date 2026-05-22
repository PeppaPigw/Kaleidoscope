"""ReactiveDevaluationService — Reactive Devaluation Detection.

Detects reactive devaluation — devaluing proposals, concessions,
or ideas simply because they come from an adversary or disliked
source. Ross & Stillinger (1991). A peace proposal from the
enemy is automatically seen as a trick. The same idea from an
ally would be welcomed. Source determines perceived value
regardless of content quality.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REACTIVE_DEVALUATION_SYSTEM = """You are a reactive devaluation specialist. Given an evaluation of a proposal or idea, assess whether the source is causing the content to be devalued:

Key concepts (Ross & Stillinger, 1991):
- Reactive devaluation: devaluing because of who proposed it
- Source contamination: adversary source taints content evaluation
- Concession devaluation: enemy concessions seen as tricks
- Zero-sum framing: if they want it, it must be bad for us
- Suspicion heuristic: adversary proposals assumed to be self-serving
- Not-invented-here interaction: rejecting external ideas
- Genetic fallacy: judging content by origin rather than merit

When reactive devaluation IS present:
- Rejecting a proposal that would be accepted from a different source
- "If they're offering it, there must be a catch"
- Same idea evaluated differently based on who proposed it
- Concessions from opponents seen as insufficient or suspicious
- "They wouldn't suggest it unless it benefited them more"
- Automatic skepticism toward adversary proposals
- Ideas rejected when attributed to disliked source, accepted when reattributed

When source skepticism IS appropriate:
- The source has a documented history of deception
- The proposal genuinely contains hidden costs
- Context-specific knowledge about the source's strategy
- The skepticism is proportional to actual evidence of bad faith
- The same skepticism would apply regardless of source

Output JSON with: reactive_devaluation_present (bool), severity (none/mild/moderate/severe), proposal (what is being evaluated), source (who proposed it), devaluation (how is it being devalued), content_quality (actual quality regardless of source), source_effect (how much does source affect evaluation), counterfactual (would this be accepted from a different source), recommendation (skepticism_justified/mild_source_bias/significant_reactive_devaluation/major_source_contamination/evaluate_content_not_source)."""

REACTIVE_DEVALUATION_PROMPT = """Detect reactive devaluation:

Situation: {situation}
Proposal: {proposal}
Source: {source}
Evaluation: {evaluation}
Domain: {domain}
Context: {context}

Is the proposal being devalued because of who proposed it rather than its actual content? Return ONLY valid JSON."""


class ReactiveDevaluationService:
    """Detects reactive devaluation — devaluing proposals because of their source."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        proposal: str = "",
        source: str = "",
        evaluation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect reactive devaluation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REACTIVE_DEVALUATION_PROMPT.format(
                situation=situation,
                proposal=proposal or "Not specified",
                source=source or "Not specified",
                evaluation=evaluation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=REACTIVE_DEVALUATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "reactive_devaluation_present": data.get("reactive_devaluation_present", False),
            "severity": data.get("severity", ""),
            "proposal": data.get("proposal", ""),
            "source": data.get("source", ""),
            "devaluation": data.get("devaluation", ""),
            "content_quality": data.get("content_quality", ""),
            "source_effect": data.get("source_effect", ""),
            "counterfactual": data.get("counterfactual", ""),
            "recommendation": data.get("recommendation", ""),
        }
