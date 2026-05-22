"""EpistemicAttentionFragmentationService — Epistemic Attention Fragmentation Detection.

Detects epistemic attention fragmentation — attention so fragmented
that deep thinking becomes impossible.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ATTENTION_FRAGMENTATION_SYSTEM = """You are an epistemic attention fragmentation specialist. Given fragmented attention preventing deep thinking, assess attention fragmentation:

Key concepts:
- Epistemic attention fragmentation: attention so fragmented deep thinking impossible
- Shallow scanning: scanning many things without depth on any
- Context switching overload: too much switching destroying depth
- Depth inability: unable to sustain attention for deep thought
- Surface skimming: skimming surfaces without penetrating
- Concentration collapse: concentration collapsing before depth achieved
- Multitasking delusion: believing multitasking works when it fragments

When epistemic attention fragmentation IS present:
- Attention too fragmented for depth
- Scanning without depth
- Too much switching
- Unable to sustain for deep thought
- Skimming without penetrating
- Concentration collapsing
- Multitasking fragmenting

When no attention fragmentation:
- Sustained deep attention
- Depth on chosen topics
- Appropriate switching
- Sustained deep thought
- Penetrating analysis
- Strong concentration
- Focused single-tasking

Output JSON with: attention_fragmentation_detected (bool), severity (none/mild/moderate/severe), shallow_scanning (what scanning without depth), context_switching_overload (what switching too much between), depth_inability (what unable to go deep on), concentration_collapse (what concentration collapsing on), recommendation (no_attention_fragmentation/mild_focus_practice/significant_depth_training/major_intensive_attention_rebuilding/emergency_complete_fragmentation)."""

EPISTEMIC_ATTENTION_FRAGMENTATION_PROMPT = """Detect epistemic attention fragmentation:

Shallow scanning: {shallow_scanning}
Context switching overload: {context_switching_overload}
Depth inability: {depth_inability}
Concentration collapse: {concentration_collapse}
Domain: {domain}
Context: {context}

Is there attention so fragmented that deep thinking becomes impossible? Return ONLY valid JSON."""


class EpistemicAttentionFragmentationService:
    """Detects epistemic attention fragmentation — fragmented preventing depth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        shallow_scanning: str,
        *,
        context_switching_overload: str = "",
        depth_inability: str = "",
        concentration_collapse: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic attention fragmentation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ATTENTION_FRAGMENTATION_PROMPT.format(
                shallow_scanning=shallow_scanning,
                context_switching_overload=context_switching_overload or "Not specified",
                depth_inability=depth_inability or "Not specified",
                concentration_collapse=concentration_collapse or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ATTENTION_FRAGMENTATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "shallow_scanning": shallow_scanning[:200],
            "attention_fragmentation_detected": data.get("attention_fragmentation_detected", False),
            "severity": data.get("severity", ""),
            "context_switching_overload": data.get("context_switching_overload", ""),
            "depth_inability": data.get("depth_inability", ""),
            "concentration_collapse": data.get("concentration_collapse", ""),
            "recommendation": data.get("recommendation", ""),
        }
