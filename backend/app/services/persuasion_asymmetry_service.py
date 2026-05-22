"""PersuasionAsymmetryService — Persuasion Asymmetry Detection.

Detects persuasion asymmetry — when one side of a debate has
structural advantages in persuasion regardless of truth value.
Some true positions are hard to communicate while some false
positions are inherently more persuasive.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PERSUASION_ASYMMETRY_SYSTEM = """You are a persuasion asymmetry specialist. Given a debate, assess whether structural persuasion advantages exist independent of truth:

Key concepts:
- Persuasion asymmetry: one side is structurally easier to argue
- Complexity asymmetry: simple wrong answers vs complex right ones
- Emotional asymmetry: one side has stronger emotional appeal
- Narrative asymmetry: one side tells a better story
- Burden of proof asymmetry: one side has easier burden
- Visibility asymmetry: one side's evidence is more visible
- Brandolini's law: refuting BS takes more effort than producing it

When persuasion asymmetry IS present:
- One side has a simpler, more intuitive message
- The true position requires more background knowledge to understand
- Emotional appeal favors one side regardless of evidence
- One side can use vivid anecdotes while the other needs statistics
- The burden of proof structurally favors one position
- One side's evidence is visible while the other's is statistical
- The debate format advantages one position over another

When debate IS balanced:
- Both sides can make equally compelling cases
- Neither side has structural communication advantages
- The format doesn't favor either position
- Both sides can use equally vivid examples
- The burden of proof is fairly distributed
- Complexity is similar on both sides
- Emotional resonance doesn't systematically favor one side

Output JSON with: persuasion_asymmetry_present (bool), severity (none/mild/moderate/severe), debate (what is being debated), advantaged_side (which side has persuasion advantage), mechanism (what creates the asymmetry), truth_correlation (does advantage correlate with truth), compensation (how to compensate for asymmetry), recommendation (debate_balanced/mild_asymmetry/significant_persuasion_asymmetry/major_structural_advantage/compensate_for_asymmetry)."""

PERSUASION_ASYMMETRY_PROMPT = """Detect persuasion asymmetry:

Debate: {debate}
Side A: {side_a}
Side B: {side_b}
Format: {format}
Domain: {domain}
Context: {context}

Does one side have structural persuasion advantages independent of truth? Return ONLY valid JSON."""


class PersuasionAsymmetryService:
    """Detects persuasion asymmetry — structural advantages in debate."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        debate: str,
        *,
        side_a: str = "",
        side_b: str = "",
        format: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect persuasion asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PERSUASION_ASYMMETRY_PROMPT.format(
                debate=debate,
                side_a=side_a or "Not specified",
                side_b=side_b or "Not specified",
                format=format or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PERSUASION_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "debate": debate[:200],
            "persuasion_asymmetry_present": data.get("persuasion_asymmetry_present", False),
            "severity": data.get("severity", ""),
            "advantaged_side": data.get("advantaged_side", ""),
            "mechanism": data.get("mechanism", ""),
            "truth_correlation": data.get("truth_correlation", ""),
            "recommendation": data.get("recommendation", ""),
        }
