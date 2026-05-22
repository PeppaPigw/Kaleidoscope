"""CargoCultService — Cargo Cult Detection.

Detects cargo cult reasoning — mimicking the superficial form of
something without understanding the underlying causal mechanism.
Named after Pacific Islanders who built mock airstrips hoping
planes would return. Feynman's "cargo cult science." Applies to
organizations copying successful companies' practices without
understanding why they worked, or implementing rituals without
understanding their purpose.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CARGO_CULT_SYSTEM = """You are a cargo cult detection specialist. Given a practice or imitation, assess whether cargo cult reasoning is at play:

Key concepts (Feynman's "Cargo Cult Science"):
- Copying the form without understanding the function
- Confusing correlation with causation in what made something work
- Ritual without mechanism: doing the steps without knowing why
- Surface imitation: copying visible features, missing invisible ones
- Context blindness: what worked there won't work here because conditions differ
- Success theater: performing the appearance of success without substance

Common manifestations:
- Organizations copying Google/Amazon practices without Google/Amazon's context
- Agile ceremonies without agile principles
- "Best practices" applied without understanding prerequisites
- Metrics that look like success metrics but don't track actual success
- Process compliance mistaken for quality

Output JSON with: cargo_cult_present (bool), severity (none/mild/moderate/severe/extreme), practice_being_copied (what is being imitated), original_context (where/why it worked originally), current_context (where it's being applied now), context_mismatch (how the contexts differ), form_copied (what visible elements are being replicated), mechanism_missing (what underlying causal mechanism is not understood), why_original_worked (actual reason for success in original context), why_copy_fails (why the imitation doesn't produce same results), ritual_without_understanding (what is being done without knowing why), prerequisites_missing (what conditions are absent that were present originally), success_theater (bool — is the appearance of success being performed?), what_would_actually_work (what approach would address the real goal), recommendation (practice_appropriate/mild_cargo_cult/significant_cargo_cult/pure_ritual/redesign_from_principles)."""

CARGO_CULT_PROMPT = """Detect cargo cult reasoning:

Practice: {practice}
Original source: {source}
Current implementation: {implementation}
Results observed: {results}
Domain: {domain}
Context: {context}

Is this cargo cult reasoning? Return ONLY valid JSON."""


class CargoCultService:
    """Detects cargo cult reasoning — form without function."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        practice: str,
        *,
        source: str = "",
        implementation: str = "",
        results: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect cargo cult reasoning."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CARGO_CULT_PROMPT.format(
                practice=practice,
                source=source or "Not specified",
                implementation=implementation or "Not specified",
                results=results or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CARGO_CULT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "practice": practice[:200],
            "cargo_cult_present": data.get("cargo_cult_present", False),
            "severity": data.get("severity", ""),
            "practice_being_copied": data.get("practice_being_copied", ""),
            "original_context": data.get("original_context", ""),
            "current_context": data.get("current_context", ""),
            "context_mismatch": data.get("context_mismatch", ""),
            "form_copied": data.get("form_copied", ""),
            "mechanism_missing": data.get("mechanism_missing", ""),
            "why_original_worked": data.get("why_original_worked", ""),
            "why_copy_fails": data.get("why_copy_fails", ""),
            "ritual_without_understanding": data.get("ritual_without_understanding", ""),
            "prerequisites_missing": data.get("prerequisites_missing", ""),
            "success_theater": data.get("success_theater", False),
            "what_would_actually_work": data.get("what_would_actually_work", ""),
            "recommendation": data.get("recommendation", ""),
        }
