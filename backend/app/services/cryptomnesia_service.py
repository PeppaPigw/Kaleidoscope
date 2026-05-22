"""CryptomnesiService — Cryptomnesia Detection.

Detects cryptomnesia — unconsciously mistaking a memory for
an original thought or creation. "Inadvertent plagiarism."
The person genuinely believes the idea is original because
they've forgotten the source. Common in creative work,
brainstorming, and idea generation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CRYPTOMNESIA_SYSTEM = """You are a cryptomnesia specialist. Given a claim of originality, assess whether the idea may be an unrecognized memory rather than a genuine original:

Key concepts:
- Cryptomnesia: forgotten memory mistaken for original thought
- Source monitoring failure: remembering content but not source
- Inadvertent plagiarism: reproducing without awareness of source
- Sleeper effect: message remembered but source forgotten
- Unconscious plagiarism: genuine belief in originality
- Prior exposure: the idea was encountered before
- Source amnesia: knowing something without knowing how you know it

When cryptomnesia IS likely:
- The "original" idea closely matches a known prior work
- The person was exposed to similar ideas recently
- The idea is too polished/complete for a genuine first thought
- Others recognize the idea from a specific source
- The domain has well-known ideas that match the "original"
- The person has consumed content in this area

When the idea IS genuinely original:
- No prior work matches closely
- The idea combines elements in a genuinely novel way
- The person can trace their reasoning process
- Domain experts confirm novelty
- The idea addresses a gap that prior work hasn't covered
- Independent creation is plausible given the person's background

Output JSON with: cryptomnesia_likely (bool), severity (none/mild/moderate/severe), claimed_original (what is claimed as original), potential_sources (what prior work might this come from?), similarity_level (how similar to known prior work?), exposure_history (was the person exposed to similar ideas?), source_monitoring (can the person trace where the idea came from?), novelty_assessment (what is genuinely novel vs. remembered?), consequence (what are the consequences if it's not original?), recommendation (genuinely_original/mild_similarity/significant_cryptomnesia_risk/major_inadvertent_plagiarism/verify_originality)."""

CRYPTOMNESIA_PROMPT = """Detect cryptomnesia:

Claimed original: {original}
Prior work: {prior_work}
Exposure: {exposure}
Reasoning trace: {reasoning}
Domain: {domain}
Context: {context}

Is this claimed original idea potentially an unrecognized memory? Return ONLY valid JSON."""


class CryptomnesiaService:
    """Detects cryptomnesia — mistaking memories for original thoughts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        original: str,
        *,
        prior_work: str = "",
        exposure: str = "",
        reasoning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect cryptomnesia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CRYPTOMNESIA_PROMPT.format(
                original=original,
                prior_work=prior_work or "Not specified",
                exposure=exposure or "Not specified",
                reasoning=reasoning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CRYPTOMNESIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "original": original[:200],
            "cryptomnesia_likely": data.get("cryptomnesia_likely", False),
            "severity": data.get("severity", ""),
            "potential_sources": data.get("potential_sources", ""),
            "similarity_level": data.get("similarity_level", ""),
            "exposure_history": data.get("exposure_history", ""),
            "source_monitoring": data.get("source_monitoring", ""),
            "novelty_assessment": data.get("novelty_assessment", ""),
            "consequence": data.get("consequence", ""),
            "recommendation": data.get("recommendation", ""),
        }
