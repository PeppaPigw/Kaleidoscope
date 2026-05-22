"""BlindSpotDetectorService — Epistemic Humility & Unknown Unknowns.

Specifically designed to find what research is NOT looking at. Surfaces
invisible assumptions, unasked questions, and systematic blind spots.
The anti-confidence engine: explicitly models what we don't know,
can't know, and might be wrong about.

Most research tools help you find answers. This one helps you find
the questions you forgot to ask.
"""

import uuid
from datetime import datetime, timezone

import structlog

from app.services.llm_utils import parse_llm_json
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BLIND_SPOT_SYSTEM = """You are an epistemic auditor specializing in finding what researchers are NOT seeing. Your job is to identify blind spots - the questions nobody is asking, the assumptions nobody is questioning, the perspectives nobody is considering.

Categories of blind spots:
- Methodological: what methods are NOT being used that could reveal different answers?
- Perspectival: whose viewpoint is missing from the analysis?
- Temporal: what time horizons are being ignored?
- Scale: what scales (micro/macro) are being overlooked?
- Negative space: what ABSENCE of evidence is being ignored?
- Framing: how does the way the question is framed exclude certain answers?

Output JSON with: blind_spots (list of spot/category/severity/what_it_hides/how_to_address/confidence), meta_blind_spot (a blind spot about the blind spot analysis itself), epistemic_humility_score (0-1 where 1 means highly humble/aware of limitations), overconfidence_areas (list), unknown_unknowns_estimate (qualitative assessment of how much we might be missing)."""

BLIND_SPOT_PROMPT = """Research question: {question}
Domain: {domain}

Current claims and conclusions:
{claims_text}

Methods used:
{methods_text}

Perspectives considered:
{perspectives_text}

Find the blind spots. What is this research NOT seeing? Return ONLY valid JSON."""

ASSUMPTION_SURFACE_SYSTEM = """You are an assumption archaeologist. Every research conclusion rests on hidden assumptions - premises so deeply embedded they become invisible. Your job is to excavate them.

For each assumption found, assess:
- How hidden is it? (obvious/subtle/deeply_buried/invisible)
- How load-bearing is it? (if wrong, does the conclusion collapse?)
- How testable is it? (can we actually check this?)
- How likely is it wrong? (based on available evidence)

Output JSON with: assumptions (list of assumption/hiddenness/load_bearing_score 0-1/testability/probability_wrong 0-1/if_wrong_then/how_to_test), most_dangerous_assumption (the one most likely to be wrong AND most load-bearing), assumption_debt (total hidden assumption load), recommendations (list)."""

ASSUMPTION_SURFACE_PROMPT = """Research conclusion: {conclusion}

Supporting evidence:
{evidence_text}

Reasoning chain:
{reasoning_text}

Excavate the hidden assumptions. Return ONLY valid JSON."""

OVERCONFIDENCE_SYSTEM = """You are a calibration expert detecting overconfidence in research claims. Overconfidence is the most common epistemic failure - we systematically believe we know more than we do.

Signs of overconfidence:
- Precision beyond what evidence supports
- Ignoring base rates
- Neglecting regression to the mean
- Confirmation bias in evidence selection
- Survivorship bias in examples
- Anchoring on initial estimates

Output JSON with: calibration_assessment (list of claim/stated_confidence/warranted_confidence/gap/reason_for_gap), overall_overconfidence (0-1 where 1 is maximally overconfident), worst_offenders (list), calibration_advice (list of specific adjustments), reference_class_neglect (what base rates are being ignored)."""

OVERCONFIDENCE_PROMPT = """Claims with confidence levels:
{claims_with_confidence}

Evidence base:
{evidence_text}

Domain: {domain}

Detect overconfidence. Return ONLY valid JSON."""

UNKNOWABILITY_SYSTEM = """You are a limits-of-knowledge analyst. Some questions are fundamentally hard or impossible to answer with current methods. Identify what CANNOT be known (with current tools) vs what is merely unknown (could be discovered).

Categories:
- Computationally intractable: would require impossible computation
- Empirically inaccessible: cannot be observed or measured
- Fundamentally underdetermined: multiple theories fit the same data
- Temporally locked: answer depends on future events
- Reflexively paradoxical: studying it changes it

Output JSON with: unknowables (list of question/category/why_unknowable/closest_approximation/what_would_change_this), merely_unknown (list of question/what_would_answer_it/estimated_effort), knowledge_frontier (where knowable meets unknowable), productive_ignorance (what we can usefully do DESPITE not knowing)."""

UNKNOWABILITY_PROMPT = """Research domain: {domain}
Key questions: {questions_text}
Current knowledge state: {knowledge_text}

What CANNOT be known vs what is merely unknown? Return ONLY valid JSON."""


class BlindSpotDetectorService:
    """Epistemic humility engine - finds what research is NOT seeing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_blind_spots(
        self,
        question: str,
        *,
        domain: str = "",
        dossier_id: str | None = None,
        methods_used: list[str] | None = None,
        perspectives: list[str] | None = None,
    ) -> dict:
        """Find what the research is NOT seeing."""
        from app.clients.llm_client import LLMClient

        claims = await self._gather_claims(question, dossier_id)
        claims_text = "\n".join(f"- {c}" for c in claims[:10]) or "No claims available"
        methods_text = "\n".join(f"- {m}" for m in (methods_used or [])) or "Not specified"
        perspectives_text = "\n".join(f"- {p}" for p in (perspectives or [])) or "Not specified"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BLIND_SPOT_PROMPT.format(
                question=question,
                domain=domain or "unspecified",
                claims_text=claims_text,
                methods_text=methods_text,
                perspectives_text=perspectives_text,
            ),
            system=BLIND_SPOT_SYSTEM,
            max_tokens=4096,
            temperature=0.5,
        )
        data = parse_llm_json(raw)

        spots = data.get("blind_spots", [])
        critical = [s for s in spots if s.get("severity") in ("critical", "high")]

        return {
            "question": question,
            "blind_spots_found": len(spots),
            "critical_spots": len(critical),
            "blind_spots": spots,
            "meta_blind_spot": data.get("meta_blind_spot", ""),
            "epistemic_humility_score": data.get("epistemic_humility_score", 0),
            "overconfidence_areas": data.get("overconfidence_areas", []),
            "unknown_unknowns_estimate": data.get("unknown_unknowns_estimate", ""),
        }

    async def surface_assumptions(
        self,
        conclusion: str,
        *,
        evidence: list[str] | None = None,
        reasoning: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Excavate hidden assumptions beneath a conclusion."""
        from app.clients.llm_client import LLMClient

        evidence_list = evidence or await self._gather_evidence(conclusion, dossier_id)
        evidence_text = "\n".join(f"- {e[:120]}" for e in evidence_list[:8]) or "Limited evidence"
        reasoning_text = reasoning or "Reasoning chain not explicitly provided"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ASSUMPTION_SURFACE_PROMPT.format(
                conclusion=conclusion,
                evidence_text=evidence_text,
                reasoning_text=reasoning_text[:500],
            ),
            system=ASSUMPTION_SURFACE_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)

        assumptions = data.get("assumptions", [])
        dangerous = [a for a in assumptions if
                     a.get("load_bearing_score", 0) > 0.7 and
                     a.get("probability_wrong", 0) > 0.3]

        return {
            "conclusion": conclusion,
            "assumptions_found": len(assumptions),
            "dangerous_assumptions": len(dangerous),
            "assumptions": assumptions,
            "most_dangerous": data.get("most_dangerous_assumption", ""),
            "assumption_debt": data.get("assumption_debt", 0),
            "recommendations": data.get("recommendations", []),
        }

    async def detect_overconfidence(
        self,
        claims_with_confidence: list[dict],
        *,
        domain: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Detect overconfidence in research claims."""
        from app.clients.llm_client import LLMClient

        claims_text = "\n".join(
            f"- [{c.get('confidence', '?')}] {c.get('text', c.get('claim', ''))[:120]}"
            for c in claims_with_confidence[:10]
        )
        evidence = await self._gather_evidence(
            " ".join(c.get("text", "")[:50] for c in claims_with_confidence[:3]),
            dossier_id,
        )
        evidence_text = "\n".join(f"- {e[:100]}" for e in evidence[:8]) or "Limited"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OVERCONFIDENCE_PROMPT.format(
                claims_with_confidence=claims_text,
                evidence_text=evidence_text,
                domain=domain or "research",
            ),
            system=OVERCONFIDENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "overall_overconfidence": data.get("overall_overconfidence", 0),
            "calibration_assessment": data.get("calibration_assessment", []),
            "worst_offenders": data.get("worst_offenders", []),
            "calibration_advice": data.get("calibration_advice", []),
            "reference_class_neglect": data.get("reference_class_neglect", ""),
        }

    async def map_unknowability(
        self,
        domain: str,
        *,
        questions: list[str] | None = None,
        dossier_id: str | None = None,
    ) -> dict:
        """Map what cannot be known vs what is merely unknown."""
        from app.clients.llm_client import LLMClient

        q_list = questions or []
        if not q_list:
            knowledge = await self._gather_claims(domain, dossier_id)
            q_list = [f"Is '{k[:60]}' actually true?" for k in knowledge[:5]]

        questions_text = "\n".join(f"- {q}" for q in q_list[:8]) or "General questions"
        knowledge = await self._gather_claims(domain, dossier_id)
        knowledge_text = "\n".join(f"- {k[:100]}" for k in knowledge[:8]) or "Limited"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=UNKNOWABILITY_PROMPT.format(
                domain=domain,
                questions_text=questions_text,
                knowledge_text=knowledge_text,
            ),
            system=UNKNOWABILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)

        unknowables = data.get("unknowables", [])
        merely_unknown = data.get("merely_unknown", [])

        return {
            "domain": domain,
            "unknowables": unknowables,
            "merely_unknown": merely_unknown,
            "num_unknowable": len(unknowables),
            "num_merely_unknown": len(merely_unknown),
            "knowledge_frontier": data.get("knowledge_frontier", ""),
            "productive_ignorance": data.get("productive_ignorance", ""),
        }

    # --- Private helpers ---

    async def _gather_claims(self, query: str, dossier_id: str | None) -> list[str]:
        claims = []
        if dossier_id:
            try:
                from app.models.dossier import ResearchDossier
                from sqlalchemy import select
                stmt = select(ResearchDossier).where(ResearchDossier.id == dossier_id)
                result = await self.db.execute(stmt)
                dossier = result.scalar_one_or_none()
                if dossier and dossier.claims:
                    for c in dossier.claims[:12]:
                        if isinstance(c, dict):
                            claims.append(c.get("text", c.get("claim", str(c)))[:200])
                        else:
                            claims.append(str(c)[:200])
            except Exception:
                pass
        if not claims:
            try:
                from app.services.search.vector_search import VectorSearchService
                svc = VectorSearchService()
                results = svc.search(query=query[:150], top_k=8)
                for r in results:
                    p = r.get("payload", {})
                    claims.append(p.get("text", p.get("title", ""))[:200])
            except Exception:
                pass
        return claims

    async def _gather_evidence(self, query: str, dossier_id: str | None) -> list[str]:
        evidence = []
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:150], top_k=6)
            for r in results:
                p = r.get("payload", {})
                evidence.append(p.get("text", p.get("title", ""))[:150])
        except Exception:
            pass
        return evidence
