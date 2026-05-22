"""EpistemicPollinationFailureService — Epistemic Pollination Failure Detection.

Detects epistemic pollination failure — ideas failing to cross-fertilize
between domains, preventing hybrid vigor.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_POLLINATION_FAILURE_SYSTEM = """You are an epistemic pollination failure specialist. Given an intellectual ecosystem, assess whether ideas fail to cross-fertilize:

Key concepts:
- Epistemic pollination failure: ideas not cross-fertilizing between domains
- Isolation: domains isolated from each other
- Hybrid vigor loss: losing the strength that comes from cross-fertilization
- Barrier to transfer: barriers preventing idea transfer
- Inbreeding: intellectual inbreeding from lack of cross-pollination
- Stagnation: stagnation from lack of new genetic material
- Pollinator absence: no mechanism for transferring ideas between domains

When pollination failure IS present:
- Ideas not cross-fertilizing between domains
- Domains isolated from each other intellectually
- Losing strength that comes from cross-fertilization
- Barriers preventing idea transfer between domains
- Intellectual inbreeding from lack of cross-pollination
- Stagnation from lack of new intellectual material
- No mechanism for transferring ideas between domains

When healthy pollination is present:
- Ideas freely cross-fertilizing between domains
- Domains connected and exchanging ideas
- Hybrid vigor from cross-fertilization
- No barriers to idea transfer
- Fresh intellectual material from other domains
- Active growth from cross-pollination
- Mechanisms for idea transfer functioning

Output JSON with: pollination_failure (bool), severity (none/mild/moderate/severe), domains (what domains are isolated), barriers (what barriers exist), stagnation (what stagnation results), hybrid_loss (what hybrid vigor is lost), recommendation (healthy_pollination/mild_isolation/significant_pollination_failure/major_intellectual_inbreeding/create_transfer_mechanisms)."""

EPISTEMIC_POLLINATION_FAILURE_PROMPT = """Detect epistemic pollination failure:

Domains: {domains}
Barriers: {barriers}
Stagnation: {stagnation}
Hybrid loss: {hybrid_loss}
Domain: {domain}
Context: {context}

Are ideas failing to cross-fertilize between domains? Return ONLY valid JSON."""


class EpistemicPollinationFailureService:
    """Detects epistemic pollination failure — ideas not cross-fertilizing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        domains: str,
        *,
        barriers: str = "",
        stagnation: str = "",
        hybrid_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic pollination failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_POLLINATION_FAILURE_PROMPT.format(
                domains=domains,
                barriers=barriers or "Not specified",
                stagnation=stagnation or "Not specified",
                hybrid_loss=hybrid_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_POLLINATION_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "domains": domains[:200],
            "pollination_failure": data.get("pollination_failure", False),
            "severity": data.get("severity", ""),
            "barriers": data.get("barriers", ""),
            "stagnation": data.get("stagnation", ""),
            "hybrid_loss": data.get("hybrid_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }
