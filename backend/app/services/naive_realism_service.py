"""NaiveRealismService — Naive Realism Detection.

Detects naive realism — the belief that you see the world
objectively and that people who disagree must be uninformed,
irrational, or biased. Ross & Ward (1996). "I see reality as
it is; those who disagree are wrong." Leads to false consensus,
hostile attribution, and inability to understand opposing views.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NAIVE_REALISM_SYSTEM = """You are a naive realism specialist. Given a disagreement or judgment about others' views, assess whether naive realism is preventing genuine understanding:

Key concepts (Ross & Ward, 1996):
- Naive realism: believing your perception of reality is objective
- Three tenets: (1) I see reality as it is, (2) others will agree if rational and informed, (3) those who disagree are uninformed, irrational, or biased
- Bias blind spot: seeing bias in others but not in yourself
- False consensus overlap: assuming others share your view
- Hostile attribution: attributing disagreement to bad faith
- Objectivity illusion: believing your views are free from bias

When naive realism IS present:
- "Anyone rational would agree with me"
- Attributing disagreement to ignorance, stupidity, or bad faith
- Inability to imagine how a reasonable person could hold the opposing view
- "I'm just being objective" while dismissing others as biased
- Surprise or anger when informed people disagree
- Treating your interpretation as "the facts" rather than a perspective

When confidence in one's view IS warranted:
- The claim is empirically verifiable and has been verified
- Expert consensus supports the position
- The person has genuinely considered opposing arguments
- The disagreement is about values, not facts, and is acknowledged as such
- The person can articulate the strongest version of the opposing view

Output JSON with: naive_realism_present (bool), severity (none/mild/moderate/severe), claim (what view is being held as objective), disagreement (what opposing view exists), attribution_for_disagreement (how is the disagreement explained), objectivity_claim (bool — is the person claiming to be objective?), bias_blind_spot (bool — seeing bias in others but not self?), hostile_attribution (bool — attributing disagreement to bad faith?), steelman_ability (can the person articulate the opposing view charitably?), empirical_basis (is the claim empirically testable?), value_vs_fact (is this a factual or value disagreement?), perspective_taking (has the person genuinely tried to understand the other view?), recommendation (confidence_warranted/mild_naive_realism/significant_objectivity_illusion/major_naive_realism/consider_other_perspectives)."""

NAIVE_REALISM_PROMPT = """Detect naive realism:

Claim held: {claim}
Disagreement: {disagreement}
Explanation for disagreement: {explanation}
Evidence considered: {evidence}
Domain: {domain}
Context: {context}

Is naive realism preventing genuine understanding of opposing views? Return ONLY valid JSON."""


class NaiveRealismService:
    """Detects naive realism — believing your perception is objective reality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        disagreement: str = "",
        explanation: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect naive realism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NAIVE_REALISM_PROMPT.format(
                claim=claim,
                disagreement=disagreement or "Not specified",
                explanation=explanation or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NAIVE_REALISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "naive_realism_present": data.get("naive_realism_present", False),
            "severity": data.get("severity", ""),
            "attribution_for_disagreement": data.get("attribution_for_disagreement", ""),
            "objectivity_claim": data.get("objectivity_claim", False),
            "bias_blind_spot": data.get("bias_blind_spot", False),
            "hostile_attribution": data.get("hostile_attribution", False),
            "steelman_ability": data.get("steelman_ability", ""),
            "empirical_basis": data.get("empirical_basis", ""),
            "value_vs_fact": data.get("value_vs_fact", ""),
            "perspective_taking": data.get("perspective_taking", ""),
            "recommendation": data.get("recommendation", ""),
        }
