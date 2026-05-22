"""GellMannAmnesiaService — Gell-Mann Amnesia Detection.

Detects Gell-Mann amnesia — the phenomenon where you notice a source
is unreliable in your area of expertise but continue trusting it in
other areas. Michael Crichton (2002). Named after physicist Murray
Gell-Mann. You read a newspaper article about your field, notice it's
full of errors, then turn the page and read about another field with
equal credulity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GELL_MANN_AMNESIA_SYSTEM = """You are a Gell-Mann amnesia specialist. Given a trust assessment of a source, assess whether known unreliability in one domain is being ignored when consuming information from the same source in other domains:

Key concepts (Crichton, 2002):
- Gell-Mann amnesia: trusting unreliable sources outside your expertise
- Domain-specific credibility: a source can be wrong in one area, right in another
- Expertise asymmetry: you can only detect errors in your own field
- Transfer of distrust: should known errors reduce trust across domains?
- Source reliability: track record matters across all coverage
- Selective skepticism: applying different standards to same source
- Calibration failure: not updating trust based on observed errors

When Gell-Mann amnesia IS present:
- Knowing a source is wrong about your field but trusting it on others
- "They got X wrong, but their coverage of Y is probably fine"
- Not updating overall source credibility after finding errors
- Compartmentalizing known unreliability
- Trusting a source's authority in domains you can't verify
- Assuming errors are isolated rather than systematic
- Forgetting observed unreliability when reading the next article

When continued trust IS appropriate:
- The source has different experts/processes for different domains
- The errors were acknowledged and corrected
- The unreliability is in a specific narrow area, not systematic
- You have independent verification for the other domain
- The source's methodology differs by domain
- The errors were minor/editorial, not substantive
- Other reliable sources corroborate the claims

Output JSON with: gell_mann_amnesia_present (bool), severity (none/mild/moderate/severe), source (what source is being evaluated), known_errors (what errors have been observed), trusted_domain (what domain is still being trusted), error_pattern (are errors systematic or isolated), calibration (has trust been appropriately updated), recommendation (trust_appropriate/mild_amnesia/significant_gell_mann/major_credibility_failure/update_source_reliability)."""

GELL_MANN_AMNESIA_PROMPT = """Detect Gell-Mann amnesia:

Source: {source}
Known errors: {errors}
Trusted domain: {trusted}
Verification: {verification}
Domain: {domain}
Context: {context}

Is known unreliability in one domain being ignored when trusting this source in other domains? Return ONLY valid JSON."""


class GellMannAmnesiaService:
    """Detects Gell-Mann amnesia — trusting unreliable sources outside expertise."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        source: str,
        *,
        errors: str = "",
        trusted: str = "",
        verification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Gell-Mann amnesia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GELL_MANN_AMNESIA_PROMPT.format(
                source=source,
                errors=errors or "Not specified",
                trusted=trusted or "Not specified",
                verification=verification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GELL_MANN_AMNESIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "source": source[:200],
            "gell_mann_amnesia_present": data.get("gell_mann_amnesia_present", False),
            "severity": data.get("severity", ""),
            "known_errors": data.get("known_errors", ""),
            "trusted_domain": data.get("trusted_domain", ""),
            "error_pattern": data.get("error_pattern", ""),
            "calibration": data.get("calibration", ""),
            "recommendation": data.get("recommendation", ""),
        }
