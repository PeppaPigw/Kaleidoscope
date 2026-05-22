"""CollingridgeDilemmaService — Collingridge Dilemma Detection.

Detects Collingridge dilemma — the tension between controlling
technology early (when it's easy to change but hard to understand)
versus late (when it's easy to understand but hard to change).
David Collingridge (1980). By the time you understand a technology's
effects, it's too entrenched to control.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COLLINGRIDGE_DILEMMA_SYSTEM = """You are a Collingridge dilemma specialist. Given a technology governance situation, assess whether the timing tension between understanding and control is present:

Key concepts (Collingridge, 1980):
- Collingridge dilemma: early control is easy but uninformed; late control is informed but hard
- Information problem: effects unknown until technology is widely adopted
- Control problem: once entrenched, technology resists change
- Lock-in: path dependence makes alternatives increasingly costly
- Pacing problem overlap: governance can't keep up with technology
- Precautionary tension: act early without information or late without leverage
- Adaptive governance: iterative approach to managing the dilemma

When Collingridge dilemma IS present:
- A technology is being deployed without understanding its effects
- By the time effects are understood, the technology is entrenched
- Calls for regulation come too late to be effective
- Early warnings are dismissed as speculative
- Lock-in effects make course correction increasingly expensive
- "We'll deal with problems as they arise" in a path-dependent system
- Governance is reactive rather than anticipatory

When timing IS appropriate:
- The technology's effects are well-understood from analogues
- Adaptive governance mechanisms are in place
- The technology can be recalled or modified after deployment
- Monitoring systems detect problems early
- The deployment is reversible or incremental
- Sunset clauses or review periods are built in
- Both early and late governance mechanisms exist

Output JSON with: collingridge_dilemma_present (bool), severity (none/mild/moderate/severe), technology (what technology is involved), understanding (how well are effects understood), control (how much control exists), lock_in (how entrenched is the technology), timing (is governance early or late), recommendation (timing_appropriate/mild_dilemma/significant_collingridge/major_lock_in_risk/implement_adaptive_governance)."""

COLLINGRIDGE_DILEMMA_PROMPT = """Detect Collingridge dilemma:

Technology: {technology}
Understanding: {understanding}
Control: {control}
Lock-in: {lock_in}
Domain: {domain}
Context: {context}

Is the tension between early control (uninformed) and late control (powerless) present? Return ONLY valid JSON."""


class CollingridgeDilemmaService:
    """Detects Collingridge dilemma — timing tension in technology governance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        technology: str,
        *,
        understanding: str = "",
        control: str = "",
        lock_in: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Collingridge dilemma."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COLLINGRIDGE_DILEMMA_PROMPT.format(
                technology=technology,
                understanding=understanding or "Not specified",
                control=control or "Not specified",
                lock_in=lock_in or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COLLINGRIDGE_DILEMMA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "technology": technology[:200],
            "collingridge_dilemma_present": data.get("collingridge_dilemma_present", False),
            "severity": data.get("severity", ""),
            "understanding": data.get("understanding", ""),
            "control": data.get("control", ""),
            "lock_in": data.get("lock_in", ""),
            "recommendation": data.get("recommendation", ""),
        }
