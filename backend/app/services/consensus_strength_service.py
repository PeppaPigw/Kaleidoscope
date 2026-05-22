"""ConsensusStrengthService — Scientific Consensus Robustness Analysis.

Measures not just whether consensus exists, but how robust it is.
Distinguishes between strong consensus (deep evidence, multiple methods,
withstood challenges) and fragile consensus (thin evidence, groupthink,
untested assumptions).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONSENSUS_SYSTEM = """You are a consensus strength analyst. Given a topic, assess not just whether scientific consensus exists, but how ROBUST that consensus is. A strong consensus has:
- Multiple independent lines of evidence
- Diverse methodologies all pointing the same way
- Survived serious challenges and attempted falsifications
- Mechanistic understanding (not just correlation)
- Replication across labs, populations, and time periods

A fragile consensus might have:
- Single methodology dominance
- Groupthink or authority-driven agreement
- Untested core assumptions
- Limited replication attempts
- Sensitivity to analytical choices

Output JSON with: consensus.exists (bool), consensus.position (what the consensus says), consensus.strength (fragile/moderate/strong/overwhelming), consensus.evidence_diversity (0-1, how many independent lines), consensus.methodological_diversity (0-1), consensus.challenge_survival (0-1, has it survived serious challenges), consensus.replication_breadth (0-1), consensus.mechanistic_depth (0-1, do we understand WHY), consensus.dissent_quality (0-1, how strong are the dissenters' arguments), consensus.fragility_factors (list of what could break the consensus), consensus.overall_robustness (0-1), consensus.confidence_warranted (0-1, how much should we trust this consensus)."""

CONSENSUS_PROMPT = """Analyze consensus strength on this topic:

Topic: {topic}
Domain: {domain}
Specific question: {question}

How robust is the scientific consensus? Return ONLY valid JSON."""


class ConsensusStrengthService:
    """Analyzes the robustness of scientific consensus."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_strength(
        self,
        topic: str,
        *,
        question: str = "",
        domain: str = "",
    ) -> dict:
        """Analyze how robust scientific consensus is on a topic."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONSENSUS_PROMPT.format(
                topic=topic,
                domain=domain or "science",
                question=question or topic,
            ),
            system=CONSENSUS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        c = data.get("consensus", data)

        return {
            "topic": topic,
            "exists": c.get("exists", False),
            "position": c.get("position", ""),
            "strength": c.get("strength", ""),
            "evidence_diversity": c.get("evidence_diversity", 0),
            "methodological_diversity": c.get("methodological_diversity", 0),
            "challenge_survival": c.get("challenge_survival", 0),
            "replication_breadth": c.get("replication_breadth", 0),
            "mechanistic_depth": c.get("mechanistic_depth", 0),
            "dissent_quality": c.get("dissent_quality", 0),
            "fragility_factors": c.get("fragility_factors", []),
            "overall_robustness": c.get("overall_robustness", 0),
            "confidence_warranted": c.get("confidence_warranted", 0),
        }
