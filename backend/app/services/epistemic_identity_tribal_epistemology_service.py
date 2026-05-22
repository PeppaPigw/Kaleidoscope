"""EpistemicIdentityTribalEpistemologyService — Epistemic Identity Tribal Epistemology Detection.

Detects tribal epistemology where group membership determines what is accepted
as true or false.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IDENTITY_TRIBAL_EPISTEMOLOGY_SYSTEM = """You are an epistemic identity tribal epistemology specialist. Given group-truth patterns, assess tribal truth filtering:

Key concepts:
- Tribal epistemology: group membership determines truth status
- Ingroup truth criterion: claims are accepted because they come from the ingroup
- Outgroup dismissal: claims are rejected because they come from the outgroup
- Loyalty over accuracy: group loyalty overrides evidential accuracy
- Epistemic tribalism: belief systems are sorted by affiliation rather than evidence

When tribal epistemology IS present:
- Ingroup status determines credibility
- Outgroup evidence is dismissed
- Loyalty outranks accuracy
- Truth is affiliation-dependent
- Evidence standards shift by group

When no tribal epistemology:
- Claims are evaluated independent of group
- Outgroup evidence can count
- Loyalty is separated from accuracy
- Truth criteria remain stable
- Evidence standards are symmetric

Output JSON with: tribal_epistemology_detected (bool), severity (none/mild/moderate/severe), outgroup_dismissal (what outgroup evidence is dismissed), loyalty_over_accuracy (where loyalty overrides accuracy), epistemic_tribalism (how affiliation determines belief), recommendation (no_tribal_epistemology/mild_source_decoupling/significant_symmetric_standards/major_cross_group_review/emergency_complete_tribal_decoupling)."""

EPISTEMIC_IDENTITY_TRIBAL_EPISTEMOLOGY_PROMPT = """Detect epistemic identity tribal epistemology:

Ingroup truth criterion: {ingroup_truth_criterion}
Outgroup dismissal: {outgroup_dismissal}
Loyalty over accuracy: {loyalty_over_accuracy}
Epistemic tribalism: {epistemic_tribalism}
Domain: {domain}
Context: {context}

Is group membership determining what counts as true? Return ONLY valid JSON."""


class EpistemicIdentityTribalEpistemologyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ingroup_truth_criterion: str,
        *,
        outgroup_dismissal: str = "",
        loyalty_over_accuracy: str = "",
        epistemic_tribalism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IDENTITY_TRIBAL_EPISTEMOLOGY_PROMPT.format(
                ingroup_truth_criterion=ingroup_truth_criterion,
                outgroup_dismissal=outgroup_dismissal or "Not specified",
                loyalty_over_accuracy=loyalty_over_accuracy or "Not specified",
                epistemic_tribalism=epistemic_tribalism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IDENTITY_TRIBAL_EPISTEMOLOGY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ingroup_truth_criterion": ingroup_truth_criterion[:200],
            "tribal_epistemology_detected": data.get("tribal_epistemology_detected", False),
            "severity": data.get("severity", ""),
            "outgroup_dismissal": data.get("outgroup_dismissal", ""),
            "loyalty_over_accuracy": data.get("loyalty_over_accuracy", ""),
            "epistemic_tribalism": data.get("epistemic_tribalism", ""),
            "recommendation": data.get("recommendation", ""),
        }
