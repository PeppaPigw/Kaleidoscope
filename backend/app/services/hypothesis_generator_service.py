"""HypothesisGeneratorService — Novel Hypothesis Creation.

Generates novel, testable research hypotheses from existing evidence.
Uses abductive reasoning, analogy, and gap analysis to propose hypotheses
that are both surprising and well-grounded in existing knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GENERATE_SYSTEM = """You are a hypothesis generation engine. Given existing evidence and a research domain, generate novel, testable hypotheses that are both surprising and well-grounded. Good hypotheses are: specific (testable), novel (not obvious from existing work), grounded (connected to evidence), and impactful (would matter if true).

Output JSON with: hypotheses (list of hypothesis/novelty 0-1/testability 0-1/impact_if_true 0-1/grounding (what evidence supports it)/test_design (how to test it)/predicted_outcome/falsification_criteria/confidence 0-1/reasoning_type abductive|analogical|combinatorial|contrarian), meta.total_generated, meta.domain, meta.evidence_base_size, meta.most_promising (index of best hypothesis)."""

GENERATE_PROMPT = """Generate novel research hypotheses:

Domain: {domain}
Research question: {question}

Existing evidence:
{evidence_text}

Known gaps:
{gaps_text}

Generate {count} novel, testable hypotheses. Return ONLY valid JSON."""

REFINE_SYSTEM = """You are a hypothesis refinement expert. Given a rough hypothesis, sharpen it into a precise, testable prediction with clear operationalization, boundary conditions, and falsification criteria.

Output JSON with: refined.original, refined.sharpened (precise testable statement), refined.operationalization (how to measure each variable), refined.boundary_conditions (list of condition/why), refined.predictions (list of specific_prediction/if_true/if_false), refined.required_sample, refined.statistical_test, refined.effect_size_estimate, refined.confidence_interval, refined.pre_registration_elements (list)."""

REFINE_PROMPT = """Refine this hypothesis into a precise, testable prediction:

Hypothesis: {hypothesis}
Domain: {domain}
Available methods: {methods}

Sharpen into a testable prediction. Return ONLY valid JSON."""


class HypothesisGeneratorService:
    """Generates and refines novel research hypotheses."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(
        self,
        question: str,
        *,
        domain: str = "",
        evidence: list[str] | None = None,
        gaps: list[str] | None = None,
        count: int = 5,
        dossier_id: str | None = None,
    ) -> dict:
        """Generate novel, testable hypotheses from evidence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        extra = await self._gather_context(question, dossier_id)
        all_evidence = (evidence or []) + extra
        evidence_text = "\n".join(f"- {e}" for e in all_evidence[:10]) or "General domain knowledge"
        gaps_text = "\n".join(f"- {g}" for g in (gaps or [])[:5]) or "Identify from evidence"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GENERATE_PROMPT.format(
                domain=domain or "research",
                question=question,
                evidence_text=evidence_text,
                gaps_text=gaps_text,
                count=min(count, 7),
            ),
            system=GENERATE_SYSTEM,
            max_tokens=4096,
            temperature=0.6,
        )
        data = parse_llm_json(raw)

        hypotheses = data.get("hypotheses", [])
        meta = data.get("meta", {})

        return {
            "question": question,
            "hypotheses": hypotheses,
            "total_generated": meta.get("total_generated", len(hypotheses)),
            "most_promising": meta.get("most_promising", 0),
            "domain": domain,
        }

    async def refine(
        self,
        hypothesis: str,
        *,
        domain: str = "",
        methods: str = "",
    ) -> dict:
        """Refine a rough hypothesis into a precise, testable prediction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REFINE_PROMPT.format(
                hypothesis=hypothesis,
                domain=domain or "research",
                methods=methods or "Standard quantitative and qualitative methods",
            ),
            system=REFINE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        refined = data.get("refined", data)

        return {
            "original": hypothesis,
            "sharpened": refined.get("sharpened", ""),
            "operationalization": refined.get("operationalization", ""),
            "boundary_conditions": refined.get("boundary_conditions", []),
            "predictions": refined.get("predictions", []),
            "required_sample": refined.get("required_sample", ""),
            "statistical_test": refined.get("statistical_test", ""),
            "effect_size_estimate": refined.get("effect_size_estimate", ""),
            "pre_registration_elements": refined.get("pre_registration_elements", []),
        }

    async def _gather_context(self, query: str, dossier_id: str | None) -> list[str]:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:100], top_k=5)
            return [r.get("payload", {}).get("text", "")[:120] for r in results]
        except Exception:
            return []
