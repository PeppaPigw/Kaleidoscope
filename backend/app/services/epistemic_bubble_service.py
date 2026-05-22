"""EpistemicBubbleService — Epistemic Bubble Detection.

Detects epistemic bubbles — environments where other viewpoints are
simply not heard (as opposed to echo chambers where they are actively
discredited). Nguyen (2020). The distinction matters for intervention.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BUBBLE_SYSTEM = """You are an epistemic bubble specialist. Given an information environment, assess whether it constitutes an epistemic bubble — where other viewpoints are simply absent:

Key concepts (Nguyen, 2020):
- Epistemic bubble: other views not heard (omission)
- Echo chamber: other views actively discredited (commission)
- Filter bubble: algorithmic curation limiting exposure
- Homophily: tendency to associate with similar others
- Information diet: what sources a person consumes
- Viewpoint diversity: range of perspectives encountered
- Structural vs active exclusion: not hearing vs refusing to hear

When epistemic bubble IS present:
- The person simply hasn't encountered opposing viewpoints
- Information sources are homogeneous without active exclusion
- Algorithmic curation limits exposure to diverse views
- Social network is homogeneous by accident, not design
- The person would engage with other views if exposed
- No active mechanism discredits outside information
- The limitation is structural, not ideological

When echo chamber IS present (different from bubble):
- Other views are actively discredited or dismissed
- Trust in outside sources has been systematically undermined
- There are active mechanisms to reject disconfirming information
- The person has been taught to distrust specific sources
- Exposure to other views triggers defensive reactions
- The environment actively inoculates against outside information

When information environment IS healthy:
- Multiple perspectives are regularly encountered
- Sources span different viewpoints and methodologies
- The person actively seeks disconfirming information
- Disagreement is engaged with rather than avoided or dismissed
- Information diet is deliberately diverse
- Both structural access and willingness to engage are present

Output JSON with: epistemic_bubble_present (bool), severity (none/mild/moderate/severe), environment (what information environment), missing_views (what viewpoints are absent), mechanism (how views are excluded), bubble_vs_chamber (is this bubble or echo chamber), diversity (viewpoint diversity level), recommendation (environment_healthy/mild_homogeneity/significant_epistemic_bubble/major_information_isolation/diversify_information_sources)."""

EPISTEMIC_BUBBLE_PROMPT = """Detect epistemic bubble:

Information environment: {environment}
Sources: {sources}
Missing viewpoints: {missing}
Mechanism: {mechanism}
Domain: {domain}
Context: {context}

Is this an epistemic bubble where other viewpoints are simply not heard? Return ONLY valid JSON."""


class EpistemicBubbleService:
    """Detects epistemic bubbles — environments where other viewpoints are absent."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        environment: str,
        *,
        sources: str = "",
        missing: str = "",
        mechanism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic bubble."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BUBBLE_PROMPT.format(
                environment=environment,
                sources=sources or "Not specified",
                missing=missing or "Not specified",
                mechanism=mechanism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BUBBLE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "environment": environment[:200],
            "epistemic_bubble_present": data.get("epistemic_bubble_present", False),
            "severity": data.get("severity", ""),
            "missing_views": data.get("missing_views", ""),
            "mechanism": data.get("mechanism", ""),
            "bubble_vs_chamber": data.get("bubble_vs_chamber", ""),
            "diversity": data.get("diversity", ""),
            "recommendation": data.get("recommendation", ""),
        }
