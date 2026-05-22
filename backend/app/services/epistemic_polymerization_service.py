"""EpistemicPolymerizationService — Epistemic Polymerization Detection.

Detects epistemic polymerization — simple ideas chaining together
into complex structures that become rigid and unbreakable.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_POLYMERIZATION_SYSTEM = """You are an epistemic polymerization specialist. Given an idea chain pattern, assess whether simple ideas are forming rigid unbreakable structures:

Key concepts:
- Epistemic polymerization: simple ideas chaining into rigid structures
- Chain formation: ideas linking together into long chains
- Rigidity: chains becoming rigid and inflexible
- Cross-linking: chains connecting to form even more rigid networks
- Unbreakable: structures becoming impossible to decompose
- Monomer simplicity: original simple ideas lost in polymer
- Plastic thinking: thought becoming plastic rather than elastic

When polymerization IS present:
- Simple ideas chaining together into complex rigid structures
- Ideas linking into long inflexible chains
- Chains becoming rigid and resistant to change
- Cross-links forming between chains creating rigid networks
- Structures becoming impossible to decompose back to components
- Original simple ideas lost in complex polymer
- Thinking becoming rigid and plastic rather than flexible

When flexible thinking is present:
- Ideas remaining independent and flexible
- No rigid chains forming between ideas
- Ideas remaining adaptable and changeable
- No cross-links creating rigid networks
- Ideas decomposable back to components
- Simple ideas maintaining their identity
- Thinking remaining elastic and adaptable

Output JSON with: polymerization_present (bool), severity (none/mild/moderate/severe), ideas (what ideas are polymerizing), chains (what chains form), rigidity (what rigidity results), cross_links (what cross-links form), recommendation (flexible_thinking/mild_chaining/significant_polymerization/major_rigid_network/break_chains)."""

EPISTEMIC_POLYMERIZATION_PROMPT = """Detect epistemic polymerization:

Ideas: {ideas}
Chains: {chains}
Rigidity: {rigidity}
Cross links: {cross_links}
Domain: {domain}
Context: {context}

Are simple ideas chaining together into rigid unbreakable structures? Return ONLY valid JSON."""


class EpistemicPolymerizationService:
    """Detects epistemic polymerization — ideas forming rigid chain structures."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ideas: str,
        *,
        chains: str = "",
        rigidity: str = "",
        cross_links: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic polymerization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_POLYMERIZATION_PROMPT.format(
                ideas=ideas,
                chains=chains or "Not specified",
                rigidity=rigidity or "Not specified",
                cross_links=cross_links or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_POLYMERIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ideas": ideas[:200],
            "polymerization_present": data.get("polymerization_present", False),
            "severity": data.get("severity", ""),
            "chains": data.get("chains", ""),
            "rigidity": data.get("rigidity", ""),
            "cross_links": data.get("cross_links", ""),
            "recommendation": data.get("recommendation", ""),
        }
