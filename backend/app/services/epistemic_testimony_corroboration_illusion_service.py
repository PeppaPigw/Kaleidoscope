"""EpistemicTestimonyCorroborationIllusionService — Epistemic Testimony Corroboration Illusion Detection.

Detects epistemic testimony corroboration illusion — treating non-independent sources
as independent corroboration when they share common origins or influences.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TESTIMONY_CORROBORATION_ILLUSION_SYSTEM = """You are an epistemic testimony corroboration illusion specialist. Given false corroboration, assess independence violations:

Key concepts:
- Epistemic corroboration illusion: non-independent sources treated as independent
- Common source: multiple accounts tracing to single origin
- Social influence: witnesses influencing each other before testifying
- Media contamination: media exposure creating shared false memories
- Echo chamber corroboration: same claim circulating appearing as multiple sources
- Citation chain: single source cited by many appearing as consensus
- Coordinated testimony: coordinated accounts appearing independent

When epistemic corroboration illusion IS present:
- Non-independent sources treated as independent
- Common source undetected
- Social influence contaminating
- Media creating shared accounts
- Echo chambers creating false corroboration
- Citation chains creating false consensus
- Coordination undetected

When no corroboration illusion:
- Independence verified
- Common sources identified
- Social influence controlled
- Media contamination assessed
- Echo chamber effects recognized
- Citation chains traced
- Coordination checked

Output JSON with: corroboration_illusion_detected (bool), severity (none/mild/moderate/severe), common_source (what common source undetected), social_influence (what social influence contaminating), echo_chamber_corroboration (what echo chambers creating), citation_chain (what citation chains creating), recommendation (no_corroboration_illusion/mild_independence_checking/significant_source_tracing/major_intensive_provenance_analysis/emergency_complete_corroboration_illusion)."""

EPISTEMIC_TESTIMONY_CORROBORATION_ILLUSION_PROMPT = """Detect epistemic testimony corroboration illusion:

Common source: {common_source}
Social influence: {social_influence}
Echo chamber corroboration: {echo_chamber_corroboration}
Citation chain: {citation_chain}
Domain: {domain}
Context: {context}

Are non-independent sources being treated as independent corroboration? Return ONLY valid JSON."""


class EpistemicTestimonyCorroborationIllusionService:
    """Detects epistemic testimony corroboration illusion — false independence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        common_source: str,
        *,
        social_influence: str = "",
        echo_chamber_corroboration: str = "",
        citation_chain: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic testimony corroboration illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TESTIMONY_CORROBORATION_ILLUSION_PROMPT.format(
                common_source=common_source,
                social_influence=social_influence or "Not specified",
                echo_chamber_corroboration=echo_chamber_corroboration or "Not specified",
                citation_chain=citation_chain or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TESTIMONY_CORROBORATION_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "common_source": common_source[:200],
            "corroboration_illusion_detected": data.get("corroboration_illusion_detected", False),
            "severity": data.get("severity", ""),
            "social_influence": data.get("social_influence", ""),
            "echo_chamber_corroboration": data.get("echo_chamber_corroboration", ""),
            "citation_chain": data.get("citation_chain", ""),
            "recommendation": data.get("recommendation", ""),
        }
