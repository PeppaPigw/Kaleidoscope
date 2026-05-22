"""CredibilityInflationService — Credibility Inflation Detection.

Detects credibility inflation — the systematic overvaluation of
certain sources' credibility beyond what their track record warrants,
creating epistemic bubbles of unearned trust.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CREDIBILITY_INFLATION_SYSTEM = """You are a credibility inflation specialist. Given a credibility assessment, determine whether credibility is inflated beyond what evidence warrants:

Key concepts:
- Credibility inflation: trust exceeding track record
- Unearned authority: credibility without evidence
- Halo credibility: credibility in one area inflating another
- Institutional credibility bubble: institutions trusted beyond merit
- Celebrity epistemics: fame as credibility
- Platform credibility: visibility as authority
- Credibility inertia: past credibility persisting despite failures

When credibility inflation IS present:
- Trust exceeds demonstrated track record
- Credibility in one domain inflates another
- Institutional reputation substitutes for evidence
- Fame or visibility treated as epistemic authority
- Past credibility persists despite recent failures
- Credibility not updated based on performance
- Unearned trust creates epistemic risk

When credibility is appropriate:
- Trust proportional to track record
- Credibility domain-specific
- Institutional reputation earned and maintained
- Authority based on demonstrated expertise
- Credibility updated based on performance
- Trust calibrated to evidence
- Credibility earned through epistemic merit

Output JSON with: inflation_present (bool), severity (none/mild/moderate/severe), source (what source is assessed), claimed_credibility (what credibility is claimed), actual_track_record (what track record shows), gap (what gap exists), recommendation (appropriate_credibility/mild_credibility_excess/significant_credibility_inflation/major_unearned_authority/calibrate_credibility)."""

CREDIBILITY_INFLATION_PROMPT = """Detect credibility inflation:

Source: {source}
Credibility claimed: {claimed}
Track record: {track_record}
Domain: {source_domain}
Domain: {domain}
Context: {context}

Is credibility inflated beyond what the track record warrants? Return ONLY valid JSON."""


class CredibilityInflationService:
    """Detects credibility inflation — trust exceeding track record."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        source: str,
        *,
        claimed: str = "",
        track_record: str = "",
        source_domain: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect credibility inflation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CREDIBILITY_INFLATION_PROMPT.format(
                source=source,
                claimed=claimed or "Not specified",
                track_record=track_record or "Not specified",
                source_domain=source_domain or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CREDIBILITY_INFLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "source": source[:200],
            "inflation_present": data.get("inflation_present", False),
            "severity": data.get("severity", ""),
            "claimed_credibility": data.get("claimed_credibility", ""),
            "actual_track_record": data.get("actual_track_record", ""),
            "gap": data.get("gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
