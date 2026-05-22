"""EpistemicAuthorityManufactureService — Epistemic Authority Manufacture Detection.

Detects epistemic authority manufacture — manufacturing authority through
credentials, titles, or institutional affiliation without substantive expertise.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AUTHORITY_MANUFACTURE_SYSTEM = """You are an epistemic authority manufacture specialist. Given manufactured authority, assess false credentialing:

Key concepts:
- Epistemic authority manufacture: creating authority without substance
- Credential stacking: accumulating credentials without depth
- Title inflation: inflating titles to suggest expertise
- Institutional affiliation exploitation: using affiliation for unearned authority
- Publication quantity over quality: using publication count as authority
- Conference circuit authority: speaking engagements as expertise proxy
- Self-citation networks: building authority through self-referential citation

When epistemic authority manufacture IS present:
- Authority manufactured without substance
- Credentials stacked without depth
- Titles inflated
- Affiliations exploited
- Publication quantity over quality
- Conference circuit as authority
- Self-citation networks active

When no authority manufacture:
- Authority earned through substance
- Credentials reflect genuine expertise
- Titles appropriate
- Affiliations genuine
- Publications quality-focused
- Speaking reflects expertise
- Citations organic

Output JSON with: authority_manufacture_detected (bool), severity (none/mild/moderate/severe), credential_stacking (what credentials stacked), title_inflation (what titles inflated), affiliation_exploitation (what affiliations exploited), quantity_over_quality (what quantity over quality), recommendation (no_authority_manufacture/mild_substance_checking/significant_credential_verification/major_intensive_expertise_audit/emergency_complete_authority_manufacture)."""

EPISTEMIC_AUTHORITY_MANUFACTURE_PROMPT = """Detect epistemic authority manufacture:

Credential stacking: {credential_stacking}
Title inflation: {title_inflation}
Affiliation exploitation: {affiliation_exploitation}
Quantity over quality: {quantity_over_quality}
Domain: {domain}
Context: {context}

Is authority being manufactured through credentials without substantive expertise? Return ONLY valid JSON."""


class EpistemicAuthorityManufactureService:
    """Detects epistemic authority manufacture — false credentialing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        credential_stacking: str,
        *,
        title_inflation: str = "",
        affiliation_exploitation: str = "",
        quantity_over_quality: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic authority manufacture."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AUTHORITY_MANUFACTURE_PROMPT.format(
                credential_stacking=credential_stacking,
                title_inflation=title_inflation or "Not specified",
                affiliation_exploitation=affiliation_exploitation or "Not specified",
                quantity_over_quality=quantity_over_quality or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AUTHORITY_MANUFACTURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "credential_stacking": credential_stacking[:200],
            "authority_manufacture_detected": data.get("authority_manufacture_detected", False),
            "severity": data.get("severity", ""),
            "title_inflation": data.get("title_inflation", ""),
            "affiliation_exploitation": data.get("affiliation_exploitation", ""),
            "quantity_over_quality": data.get("quantity_over_quality", ""),
            "recommendation": data.get("recommendation", ""),
        }
