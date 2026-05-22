"""EpistemicNostalgiaService — Epistemic Nostalgia Detection.

Detects epistemic nostalgia — romanticizing past epistemic states
over current evidence, preferring how things used to be known.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NOSTALGIA_SYSTEM = """You are an epistemic nostalgia specialist. Given a knowledge preference, assess whether past epistemic states are being romanticized over current evidence:

Key concepts:
- Epistemic nostalgia: romanticizing past epistemic states
- Golden age thinking: believing knowledge was better in the past
- Progress denial: denying genuine epistemic progress
- Simplicity nostalgia: preferring past simplicity over current complexity
- Authority nostalgia: preferring past authority structures
- Certainty nostalgia: preferring past (false) certainty
- Method nostalgia: preferring past methods despite better alternatives

When epistemic nostalgia IS present:
- Past epistemic states romanticized over current evidence
- Golden age of knowledge imagined without basis
- Genuine progress denied in favor of past
- Past simplicity preferred over necessary complexity
- Past authority structures preferred over current evidence
- Past certainty preferred over honest uncertainty
- Past methods preferred despite demonstrated improvements

When appropriate historical appreciation is present:
- Past contributions acknowledged without romanticization
- Progress recognized alongside past achievements
- Complexity accepted as reflecting genuine understanding
- Current methods adopted based on evidence
- Uncertainty accepted as honest
- Historical methods appreciated in context

Output JSON with: nostalgia_present (bool), severity (none/mild/moderate/severe), preference (what past state is preferred), romanticization (how past is romanticized), current_evidence (what current evidence shows), progress_denied (what progress is denied), recommendation (appropriate_appreciation/mild_nostalgia/significant_epistemic_nostalgia/major_progress_denial/accept_current_evidence)."""

EPISTEMIC_NOSTALGIA_PROMPT = """Detect epistemic nostalgia:

Preference: {preference}
Romanticization: {romanticization}
Current evidence: {current}
Progress: {progress}
Domain: {domain}
Context: {context}

Are past epistemic states being romanticized over current evidence? Return ONLY valid JSON."""


class EpistemicNostalgiaService:
    """Detects epistemic nostalgia — romanticizing past epistemic states."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        preference: str,
        *,
        romanticization: str = "",
        current: str = "",
        progress: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic nostalgia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NOSTALGIA_PROMPT.format(
                preference=preference,
                romanticization=romanticization or "Not specified",
                current=current or "Not specified",
                progress=progress or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NOSTALGIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "preference": preference[:200],
            "nostalgia_present": data.get("nostalgia_present", False),
            "severity": data.get("severity", ""),
            "romanticization": data.get("romanticization", ""),
            "current_evidence": data.get("current_evidence", ""),
            "progress_denied": data.get("progress_denied", ""),
            "recommendation": data.get("recommendation", ""),
        }
