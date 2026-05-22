"""ArgumentMapperService — Logical Argument Analysis.

Maps the logical structure of research arguments: premises, inferences,
conclusions, hidden assumptions. Identifies logical fallacies, evaluates
argument strength, and finds the weakest links in reasoning chains.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ARGUMENT_MAP_SYSTEM = """You are a formal logic and argumentation expert. Given a research argument or claim chain, map its logical structure completely: identify all premises (stated and hidden), inference steps, and conclusions. Evaluate the validity and soundness of each step.

Output JSON with: argument_map.conclusion, argument_map.premises (list of premise/type stated|hidden|assumed/confidence 0-1), argument_map.inference_chain (list of from/to/inference_type deductive|inductive|abductive|analogical/strength 0-1/potential_flaw), argument_map.hidden_assumptions (list of assumption/criticality 0-1/if_false_then), argument_map.weakest_link (the single weakest point/why/how_to_strengthen), argument_map.fallacies (list of fallacy_type/where/severity), argument_map.overall_validity (0-1), argument_map.overall_soundness (0-1), argument_map.steel_man (strongest version of this argument), argument_map.straw_man_risk (aspects that could be misrepresented)."""

ARGUMENT_MAP_PROMPT = """Map the logical structure of this argument:

Argument/Claim: {argument}
Context: {context}
Domain: {domain}

Supporting evidence:
{evidence_text}

Map the complete logical structure. Return ONLY valid JSON."""

FALLACY_SYSTEM = """You are a critical thinking expert specializing in detecting logical fallacies in research reasoning. Given a piece of reasoning, identify all fallacies present - both formal (structural) and informal (content-based).

Output JSON with: fallacy_analysis.text_analyzed, fallacy_analysis.fallacies_found (list of name/type formal|informal/location/explanation/severity critical|major|minor/how_it_misleads), fallacy_analysis.reasoning_quality (0-1), fallacy_analysis.most_dangerous (the fallacy most likely to mislead readers), fallacy_analysis.corrections (list of original/corrected/what_changes), fallacy_analysis.clean_version (the argument rewritten without fallacies)."""

FALLACY_PROMPT = """Detect logical fallacies in this reasoning:

Text: {text}
Domain: {domain}
Claimed conclusion: {conclusion}

Identify all fallacies. Return ONLY valid JSON."""


class ArgumentMapperService:
    """Maps logical structure and detects fallacies in arguments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def map_argument(
        self,
        argument: str,
        *,
        context: str = "",
        domain: str = "",
        evidence: list[str] | None = None,
        dossier_id: str | None = None,
    ) -> dict:
        """Map the complete logical structure of an argument."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        extra = await self._gather_context(argument, dossier_id)
        all_evidence = (evidence or []) + extra
        evidence_text = "\n".join(f"- {e}" for e in all_evidence[:8]) or "None provided"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ARGUMENT_MAP_PROMPT.format(
                argument=argument,
                context=context or "Academic research",
                domain=domain or "general",
                evidence_text=evidence_text,
            ),
            system=ARGUMENT_MAP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        amap = data.get("argument_map", data)

        return {
            "conclusion": amap.get("conclusion", argument),
            "premises": amap.get("premises", []),
            "inference_chain": amap.get("inference_chain", []),
            "hidden_assumptions": amap.get("hidden_assumptions", []),
            "weakest_link": amap.get("weakest_link", ""),
            "fallacies": amap.get("fallacies", []),
            "overall_validity": amap.get("overall_validity", 0),
            "overall_soundness": amap.get("overall_soundness", 0),
            "steel_man": amap.get("steel_man", ""),
            "straw_man_risk": amap.get("straw_man_risk", ""),
        }

    async def detect_fallacies(
        self,
        text: str,
        *,
        domain: str = "",
        conclusion: str = "",
    ) -> dict:
        """Detect logical fallacies in reasoning text."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FALLACY_PROMPT.format(
                text=text,
                domain=domain or "research",
                conclusion=conclusion or "Implied by text",
            ),
            system=FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        analysis = data.get("fallacy_analysis", data)

        return {
            "fallacies_found": analysis.get("fallacies_found", []),
            "reasoning_quality": analysis.get("reasoning_quality", 0),
            "most_dangerous": analysis.get("most_dangerous", ""),
            "corrections": analysis.get("corrections", []),
            "clean_version": analysis.get("clean_version", ""),
        }

    async def _gather_context(self, query: str, dossier_id: str | None) -> list[str]:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:100], top_k=4)
            return [r.get("payload", {}).get("text", "")[:120] for r in results]
        except Exception:
            return []
