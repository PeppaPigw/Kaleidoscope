"""EpistemicCredibilityTheftService — Epistemic Credibility Theft Detection.

Detects epistemic credibility theft — stealing intellectual credibility
from others by appropriating their ideas or undermining their authority.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CREDIBILITY_THEFT_SYSTEM = """You are an epistemic credibility theft specialist. Given stealing intellectual credibility, assess credibility theft:

Key concepts:
- Epistemic credibility theft: stealing intellectual credibility from others
- Idea appropriation: taking credit for others' ideas
- Credit erasure: erasing others' contributions
- Authority undermining: undermining others' intellectual authority
- Contribution invisibilization: making others' contributions invisible
- Intellectual plagiarism: plagiarizing intellectual work
- Reputation parasitism: building reputation on others' work

When epistemic credibility theft IS present:
- Stealing credibility
- Taking credit for others' ideas
- Erasing contributions
- Undermining authority
- Making contributions invisible
- Plagiarizing work
- Building on others' work without credit

When no credibility theft:
- Respecting credibility
- Giving proper credit
- Acknowledging contributions
- Supporting authority
- Making contributions visible
- Original work
- Proper attribution

Output JSON with: credibility_theft_detected (bool), severity (none/mild/moderate/severe), idea_appropriation (whose ideas appropriated), credit_erasure (whose credit erased), authority_undermining (whose authority undermined), contribution_invisibilization (whose contributions made invisible), recommendation (no_credibility_theft/mild_attribution_practice/significant_credit_restoration/major_intensive_accountability/emergency_complete_credibility_theft)."""

EPISTEMIC_CREDIBILITY_THEFT_PROMPT = """Detect epistemic credibility theft:

Idea appropriation: {idea_appropriation}
Credit erasure: {credit_erasure}
Authority undermining: {authority_undermining}
Contribution invisibilization: {contribution_invisibilization}
Domain: {domain}
Context: {context}

Is there stealing intellectual credibility from others? Return ONLY valid JSON."""


class EpistemicCredibilityTheftService:
    """Detects epistemic credibility theft — stealing intellectual credibility."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        idea_appropriation: str,
        *,
        credit_erasure: str = "",
        authority_undermining: str = "",
        contribution_invisibilization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic credibility theft."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CREDIBILITY_THEFT_PROMPT.format(
                idea_appropriation=idea_appropriation,
                credit_erasure=credit_erasure or "Not specified",
                authority_undermining=authority_undermining or "Not specified",
                contribution_invisibilization=contribution_invisibilization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CREDIBILITY_THEFT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "idea_appropriation": idea_appropriation[:200],
            "credibility_theft_detected": data.get("credibility_theft_detected", False),
            "severity": data.get("severity", ""),
            "credit_erasure": data.get("credit_erasure", ""),
            "authority_undermining": data.get("authority_undermining", ""),
            "contribution_invisibilization": data.get("contribution_invisibilization", ""),
            "recommendation": data.get("recommendation", ""),
        }
