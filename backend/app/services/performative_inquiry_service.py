"""PerformativeInquiryService — Performative Inquiry Detection.

Detects performative inquiry — performing the appearance of inquiry
without genuine investigation, where the form of research is
present but the substance is absent.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PERFORMATIVE_INQUIRY_SYSTEM = """You are a performative inquiry specialist. Given an inquiry process, assess whether it is performative rather than genuine:

Key concepts:
- Performative inquiry: appearance of inquiry without substance
- Research theater: performing research without investigating
- Inquiry as ritual: going through motions without seeking truth
- Predetermined conclusions: inquiry with foregone conclusions
- Process without substance: following process without genuine search
- Legitimation through inquiry: using inquiry form to legitimize
- Show investigation: investigation for show not knowledge

When performative inquiry IS present:
- Appearance of inquiry without genuine investigation
- Research form present but substance absent
- Conclusions predetermined before inquiry begins
- Process followed without genuine truth-seeking
- Inquiry used to legitimize rather than discover
- Investigation for show rather than knowledge
- Form of research without function of research

When genuine inquiry is present:
- Investigation genuinely seeking answers
- Research substance matching form
- Conclusions open to evidence
- Process serving genuine discovery
- Inquiry seeking truth not legitimation
- Investigation producing genuine knowledge
- Form and function of research aligned

Output JSON with: performative_present (bool), severity (none/mild/moderate/severe), inquiry (what inquiry is conducted), form (what form is followed), substance (what substance is present), predetermined (what is predetermined), recommendation (genuine_inquiry/mild_ritualism/significant_performative_inquiry/major_research_theater/conduct_genuine_investigation)."""

PERFORMATIVE_INQUIRY_PROMPT = """Detect performative inquiry:

Inquiry conducted: {inquiry}
Process followed: {process}
Genuine investigation: {investigation}
Conclusions: {conclusions}
Domain: {domain}
Context: {context}

Is the appearance of inquiry being performed without genuine investigation? Return ONLY valid JSON."""


class PerformativeInquiryService:
    """Detects performative inquiry — appearance of inquiry without substance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        inquiry: str,
        *,
        process: str = "",
        investigation: str = "",
        conclusions: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect performative inquiry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PERFORMATIVE_INQUIRY_PROMPT.format(
                inquiry=inquiry,
                process=process or "Not specified",
                investigation=investigation or "Not specified",
                conclusions=conclusions or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PERFORMATIVE_INQUIRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "inquiry": inquiry[:200],
            "performative_present": data.get("performative_present", False),
            "severity": data.get("severity", ""),
            "form": data.get("form", ""),
            "substance": data.get("substance", ""),
            "predetermined": data.get("predetermined", ""),
            "recommendation": data.get("recommendation", ""),
        }
