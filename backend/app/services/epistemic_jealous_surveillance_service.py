"""EpistemicJealousSurveillanceService — Epistemic Jealous Surveillance Detection.

Detects epistemic jealous surveillance — monitoring others for intellectual
encroachment on one's domain or ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_JEALOUS_SURVEILLANCE_SYSTEM = """You are an epistemic jealous surveillance specialist. Given monitoring for intellectual encroachment, assess jealous surveillance:

Key concepts:
- Epistemic jealous surveillance: monitoring others for encroachment
- Publication tracking: obsessively watching others' output
- Citation monitoring: tracking who cites whom
- Competitor fixation: obsessing over rivals' work
- Priority checking: constantly verifying no one published first
- Plagiarism paranoia: suspecting others of stealing ideas
- Alert systems: setting up notifications about others' work

When epistemic jealous surveillance IS present:
- Monitoring others for encroachment
- Obsessively watching output
- Tracking citations
- Obsessing over rivals
- Constantly checking priority
- Suspecting plagiarism
- Setting up alerts about others

When no jealous surveillance:
- Trusting intellectual community
- Healthy awareness of field
- Generous citation practices
- Collaborative orientation
- Secure about priority
- Assuming good faith
- Natural field awareness

Output JSON with: jealous_surveillance_detected (bool), severity (none/mild/moderate/severe), publication_tracking (what obsessively watching), competitor_fixation (what obsessing over), priority_checking (what verifying), plagiarism_paranoia (what suspecting), recommendation (no_jealous_surveillance/mild_trust_building/significant_security_work/major_intensive_trust_therapy/emergency_paranoid_monitoring)."""

EPISTEMIC_JEALOUS_SURVEILLANCE_PROMPT = """Detect epistemic jealous surveillance:

Publication tracking: {publication_tracking}
Competitor fixation: {competitor_fixation}
Priority checking: {priority_checking}
Plagiarism paranoia: {plagiarism_paranoia}
Domain: {domain}
Context: {context}

Is there monitoring others for intellectual encroachment? Return ONLY valid JSON."""


class EpistemicJealousSurveillanceService:
    """Detects epistemic jealous surveillance — monitoring for intellectual encroachment."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        publication_tracking: str,
        *,
        competitor_fixation: str = "",
        priority_checking: str = "",
        plagiarism_paranoia: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic jealous surveillance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_JEALOUS_SURVEILLANCE_PROMPT.format(
                publication_tracking=publication_tracking,
                competitor_fixation=competitor_fixation or "Not specified",
                priority_checking=priority_checking or "Not specified",
                plagiarism_paranoia=plagiarism_paranoia or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_JEALOUS_SURVEILLANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "publication_tracking": publication_tracking[:200],
            "jealous_surveillance_detected": data.get("jealous_surveillance_detected", False),
            "severity": data.get("severity", ""),
            "competitor_fixation": data.get("competitor_fixation", ""),
            "priority_checking": data.get("priority_checking", ""),
            "plagiarism_paranoia": data.get("plagiarism_paranoia", ""),
            "recommendation": data.get("recommendation", ""),
        }
