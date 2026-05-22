"""EpistemicPowerEpistemicInjusticeService - Epistemic Power Epistemic Injustice Detection.

Detects epistemic injustice where power structures determine whose knowledge counts.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_POWER_EPISTEMIC_INJUSTICE_SYSTEM = """You are an epistemic power and epistemic injustice specialist. Given testimonial injustice, assess whether power structures determine whose knowledge counts:

Key concepts:
- Epistemic injustice: unfair treatment of people as knowers
- Testimonial injustice: credibility assigned through identity and power rather than evidence
- Hermeneutical injustice: interpretive resources are unavailable or controlled
- Credibility deficit: knowledge discounted below evidential merit
- Epistemic exploitation: marginalized knowers made to educate or justify themselves unfairly

When epistemic power injustice IS present:
- Power determines whose knowledge is treated as authoritative
- Testimony from less powerful groups is discounted
- Interpretive frameworks exclude affected knowers
- Credibility tracks status rather than evidence
- Marginalized knowers bear disproportionate explanatory labor

When no epistemic injustice:
- Credibility tracks evidence, expertise, and reliability
- Affected knowers can shape interpretation
- Testimony is assessed consistently across status groups
- Explanatory burden is fairly distributed
- Knowledge standards are transparent and contestable

Output JSON with: injustice_detected (bool), severity (none/mild/moderate/severe), power_structure (what power structure shapes knowledge), whose_knowledge_counts (whose knowledge is privileged), credibility_deficit (what credibility deficit appears), hermeneutical_injustice (what interpretive exclusion appears), epistemic_exploitation (what unfair explanatory labor appears), recommendation (no_injustice/mild_power_awareness/significant_epistemic_injustice/major_power_rebalancing/emergency_epistemic_redress)."""

EPISTEMIC_POWER_EPISTEMIC_INJUSTICE_PROMPT = """Detect epistemic power and epistemic injustice:

Testimonial injustice: {testimonial_injustice}
Hermeneutical injustice: {hermeneutical_injustice}
Credibility deficit: {credibility_deficit}
Epistemic exploitation: {epistemic_exploitation}
Domain: {domain}
Context: {context}

Are power structures determining whose knowledge counts? Return ONLY valid JSON."""


class EpistemicPowerEpistemicInjusticeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        testimonial_injustice: str,
        *,
        hermeneutical_injustice: str = "",
        credibility_deficit: str = "",
        epistemic_exploitation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_POWER_EPISTEMIC_INJUSTICE_PROMPT.format(
                testimonial_injustice=testimonial_injustice,
                hermeneutical_injustice=hermeneutical_injustice or "Not specified",
                credibility_deficit=credibility_deficit or "Not specified",
                epistemic_exploitation=epistemic_exploitation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_POWER_EPISTEMIC_INJUSTICE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "testimonial_injustice": testimonial_injustice[:200],
            "injustice_detected": data.get("injustice_detected", False),
            "severity": data.get("severity", ""),
            "power_structure": data.get("power_structure", ""),
            "whose_knowledge_counts": data.get("whose_knowledge_counts", ""),
            "credibility_deficit": data.get("credibility_deficit", ""),
            "hermeneutical_injustice": data.get("hermeneutical_injustice", ""),
            "epistemic_exploitation": data.get("epistemic_exploitation", ""),
            "recommendation": data.get("recommendation", ""),
        }
