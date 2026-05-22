"""DebateEngineService — Multi-Perspective Structured Argumentation.

Orchestrates structured debates between multiple expert personas on research
questions. Unlike the Red Team (which is purely adversarial), the Debate Engine
creates genuine multi-sided discourse where different perspectives illuminate
different aspects of a problem. Produces synthesis judgments that are stronger
than any single perspective.
"""

import uuid
from datetime import datetime, timezone

import structlog

from app.services.llm_utils import parse_llm_json
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PANEL_SYSTEM = """You are assembling an expert panel for a structured research debate. Given a question, identify 3-4 distinct expert perspectives that would produce the most illuminating disagreement.

Output JSON only:
{"panel": {"question": "the debate question", "experts": [{"id": "exp_1", "role": "Methodologist|Domain Expert|Theorist|Practitioner|Skeptic|Statistician|Ethicist|Systems Thinker", "name": "Dr. [Name]", "perspective": "their core stance in 1 sentence", "expertise": "what they bring to the debate", "likely_position": "for|against|nuanced|orthogonal", "blind_spots": ["what this expert might miss"]}], "key_tensions": ["fundamental disagreement that will drive the debate"], "expected_outcome": "what we hope to learn from this debate"}}"""

PANEL_PROMPT = """Research question to debate:
{question}

Domain context:
{context_text}

Current evidence state:
{evidence_text}

Assemble the most illuminating expert panel. Return ONLY valid JSON."""

ARGUE_SYSTEM_TEMPLATE = "You are {expert_name}, a {expert_role} with the perspective: \"{expert_perspective}\".\n\nYou are participating in a structured research debate. Make your STRONGEST argument from your specific expertise and perspective. Be intellectually honest but advocate firmly for your position. Acknowledge what you don't know.\n\nOutput JSON with keys: argument.position (1 sentence claim), argument.reasoning (list of point/type/strength/evidence), argument.concessions, argument.conditions, argument.crux, argument.confidence (0-1)."

ARGUE_PROMPT = """Debate question: {question}

Your role: {expert_role}
Your perspective: {expert_perspective}

Evidence available:
{evidence_text}

Previous arguments in this debate:
{previous_args_text}

Make your argument. Return ONLY valid JSON."""

REBUT_SYSTEM_TEMPLATE = "You are {expert_name}, a {expert_role}. You've heard the other experts' arguments. Now respond directly to their points — rebut what you disagree with, acknowledge what's valid, and sharpen your position.\n\nOutput JSON with keys: rebuttal.target_expert, rebuttal.rebuttals (list of their_point/your_response/type), rebuttal.updated_position, rebuttal.remaining_disagreement, rebuttal.new_insight, rebuttal.confidence_change (-0.5 to 0.5)."

REBUT_PROMPT = """Debate question: {question}

Your role: {expert_role}
Your perspective: {expert_perspective}

All arguments made:
{all_args_text}

Respond to the other experts. Return ONLY valid JSON."""

JUDGE_SYSTEM = """You are a debate judge synthesizing a structured research debate. Your job is NOT to pick a winner, but to extract the collective wisdom — what did the debate reveal that no single expert could see alone?

Output JSON only:
{"judgment": {"question": "the original question", "synthesis": "the integrated conclusion that accounts for all valid perspectives (2-3 sentences)", "key_insights": [{"insight": "what we learned", "source": "which expert(s) contributed this", "novelty": 0.0-1.0}], "resolved_tensions": [{"tension": "what was disagreed on", "resolution": "how it was resolved or reframed"}], "unresolved_tensions": [{"tension": "what remains genuinely uncertain", "why_unresolvable": "what would be needed to resolve it", "experiment_needed": "what would settle this"}], "expert_contributions": [{"expert": "name", "best_point": "their strongest contribution", "blind_spot_confirmed": "what they missed"}], "confidence_in_synthesis": 0.0-1.0, "actionable_next_steps": [{"step": "what to do", "rationale": "why"}], "meta_observation": "what the debate process itself revealed about the question"}}"""

JUDGE_PROMPT = """Debate question: {question}

Expert panel:
{panel_text}

Round 1 arguments:
{round1_text}

Round 2 rebuttals:
{round2_text}

Synthesize the debate. What did we learn that no single expert could see? Return ONLY valid JSON."""


class DebateEngineService:
    """Multi-perspective structured argumentation engine."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assemble_panel(
        self,
        question: str,
        *,
        dossier_id: str | None = None,
        num_experts: int = 3,
    ) -> dict:
        """Assemble an expert panel for a structured debate."""
        from app.clients.llm_client import LLMClient

        context = await self._gather_context(question, dossier_id)
        evidence = await self._gather_evidence(question, dossier_id)

        context_text = "\n".join(f"- {c}" for c in context[:8]) or "General research context"
        evidence_text = "\n".join(
            f"- [{e.get('confidence', 0):.2f}] {e.get('text', '')[:100]}"
            for e in evidence[:10]
        ) or "Limited evidence available"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PANEL_PROMPT.format(
                question=question,
                context_text=context_text,
                evidence_text=evidence_text,
            ),
            system=PANEL_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)

        # Retry with concise prompt if panel is empty (LLM truncation)
        if not data.get("panel", {}).get("experts") and not data.get("experts"):
            raw = await llm.complete(
                prompt=(
                    f"Assemble a {num_experts}-expert debate panel for: {question}\n\n"
                    f"Context: {context_text[:200]}\n\n"
                    "Return JSON: {\"panel\": {\"experts\": [{\"id\": \"exp_1\", \"role\": \"role\", "
                    "\"name\": \"Dr. Name\", \"perspective\": \"stance\", \"expertise\": \"area\", "
                    "\"likely_position\": \"for|against|nuanced\"}], "
                    "\"key_tensions\": [\"tension\"], \"expected_outcome\": \"what we learn\"}}"
                ),
                system="Output valid JSON only. No markdown.",
                max_tokens=4096,
                temperature=0.4,
            )
            data = parse_llm_json(raw)
        panel = data.get("panel", data)

        return {
            "question": question,
            "experts": panel.get("experts", [])[:num_experts],
            "key_tensions": panel.get("key_tensions", []),
            "expected_outcome": panel.get("expected_outcome", ""),
        }

    async def run_debate(
        self,
        question: str,
        *,
        dossier_id: str | None = None,
        num_experts: int = 3,
        rounds: int = 2,
    ) -> dict:
        """Run a complete structured debate with multiple rounds."""
        from app.clients.llm_client import LLMClient

        panel_result = await self.assemble_panel(
            question, dossier_id=dossier_id, num_experts=num_experts
        )
        experts = panel_result.get("experts", [])
        if not experts:
            return {"error": "Failed to assemble panel"}

        evidence = await self._gather_evidence(question, dossier_id)
        evidence_text = "\n".join(
            f"- [{e.get('confidence', 0):.2f}] {e.get('text', '')[:100]}"
            for e in evidence[:10]
        ) or "Limited evidence"

        llm = LLMClient()

        # Round 1: Initial arguments
        round1 = []
        for expert in experts:
            previous_text = "\n".join(
                f"[{a['expert']}]: {a['position']}" for a in round1
            ) or "You are first to argue."

            raw = await llm.complete(
                prompt=ARGUE_PROMPT.format(
                    question=question,
                    expert_role=expert.get("role", "Expert"),
                    expert_perspective=expert.get("perspective", ""),
                    evidence_text=evidence_text,
                    previous_args_text=previous_text,
                ),
                system=ARGUE_SYSTEM_TEMPLATE.format(
                    expert_name=expert.get("name", "Expert"),
                    expert_role=expert.get("role", "Expert"),
                    expert_perspective=expert.get("perspective", ""),
                ),
                max_tokens=4096,
                temperature=0.5,
            )
            arg_data = parse_llm_json(raw)
            argument = arg_data.get("argument", arg_data)
            if not argument.get("position"):
                # Retry with concise prompt
                raw = await llm.complete(
                    prompt=(
                        f"You are {expert.get('name', 'Expert')}, a {expert.get('role', 'Expert')}.\n"
                        f"Debate: {question}\nYour stance: {expert.get('perspective', '')}\n\n"
                        "Return JSON: {\"argument\": {\"position\": \"your claim\", "
                        "\"reasoning\": [{\"point\": \"arg\", \"strength\": 0.8}], "
                        "\"crux\": \"key point\", \"confidence\": 0.7}}"
                    ),
                    system="Output valid JSON only.",
                    max_tokens=4096,
                    temperature=0.5,
                )
                arg_data = parse_llm_json(raw)
                argument = arg_data.get("argument", arg_data)
            argument["expert"] = expert.get("name", "Expert")
            argument["role"] = expert.get("role", "Expert")
            round1.append(argument)

        # Round 2: Rebuttals
        round2 = []
        if rounds >= 2:
            all_args_text = "\n\n".join(
                f"[{a['expert']} ({a['role']})]:\n"
                f"Position: {a.get('position', '')}\n"
                f"Key points: {'; '.join(p.get('point', '') for p in a.get('reasoning', [])[:3])}\n"
                f"Crux: {a.get('crux', '')}"
                for a in round1
            )

            for expert in experts:
                raw = await llm.complete(
                    prompt=REBUT_PROMPT.format(
                        question=question,
                        expert_role=expert.get("role", "Expert"),
                        expert_perspective=expert.get("perspective", ""),
                        all_args_text=all_args_text,
                    ),
                    system=REBUT_SYSTEM_TEMPLATE.format(
                        expert_name=expert.get("name", "Expert"),
                        expert_role=expert.get("role", "Expert"),
                    ),
                    max_tokens=4096,
                    temperature=0.4,
                )
                reb_data = parse_llm_json(raw)
                rebuttal = reb_data.get("rebuttal", reb_data)
                rebuttal["expert"] = expert.get("name", "Expert")
                rebuttal["role"] = expert.get("role", "Expert")
                round2.append(rebuttal)

        # Judge: Synthesize
        panel_text = "\n".join(
            f"- {e.get('name', '?')} ({e.get('role', '?')}): {e.get('perspective', '')}"
            for e in experts
        )
        round1_text = "\n\n".join(
            f"[{a['expert']}]: {a.get('position', '')}\n"
            f"Confidence: {a.get('confidence', 0)}\n"
            f"Crux: {a.get('crux', '')}"
            for a in round1
        )
        round2_text = "\n\n".join(
            f"[{r['expert']}]: {r.get('updated_position', '')}\n"
            f"New insight: {r.get('new_insight', '')}\n"
            f"Remaining disagreement: {r.get('remaining_disagreement', '')}"
            for r in round2
        ) or "No rebuttals (single round)"

        raw = await llm.complete(
            prompt=JUDGE_PROMPT.format(
                question=question,
                panel_text=panel_text,
                round1_text=round1_text,
                round2_text=round2_text,
            ),
            system=JUDGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        judge_data = parse_llm_json(raw)
        judgment = judge_data.get("judgment", judge_data)

        return {
            "question": question,
            "panel": experts,
            "round1_arguments": round1,
            "round2_rebuttals": round2,
            "judgment": judgment,
            "synthesis": judgment.get("synthesis", ""),
            "confidence": judgment.get("confidence_in_synthesis", 0),
            "unresolved": judgment.get("unresolved_tensions", []),
            "next_steps": judgment.get("actionable_next_steps", []),
        }

    async def quick_debate(
        self,
        question: str,
        *,
        dossier_id: str | None = None,
    ) -> dict:
        """Run a fast single-round debate with 3 experts."""
        return await self.run_debate(
            question, dossier_id=dossier_id, num_experts=3, rounds=1
        )

    # --- Private helpers ---

    async def _gather_context(self, question: str, dossier_id: str | None) -> list[str]:
        context = []
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=question[:150], top_k=6)
            for r in results:
                p = r.get("payload", {})
                context.append(p.get("title", p.get("text", ""))[:120])
        except Exception:
            pass
        return context

    async def _gather_evidence(self, question: str, dossier_id: str | None) -> list[dict]:
        evidence = []
        if dossier_id:
            try:
                from app.models.claim_ledger import GlobalClaim, ClaimMention
                from sqlalchemy import select
                stmt = (
                    select(GlobalClaim)
                    .join(ClaimMention, ClaimMention.global_claim_id == GlobalClaim.id)
                    .where(ClaimMention.dossier_id == dossier_id)
                    .limit(10)
                )
                result = await self.db.execute(stmt)
                for claim in result.scalars().all():
                    evidence.append({
                        "text": (claim.canonical_text or "")[:120],
                        "confidence": (claim.evidence_strength_score or 50) / 100.0,
                    })
            except Exception:
                pass

        if not evidence:
            try:
                from app.services.search.vector_search import VectorSearchService
                svc = VectorSearchService()
                results = svc.search(query=question[:150], top_k=8)
                for r in results:
                    p = r.get("payload", {})
                    evidence.append({
                        "text": p.get("text", p.get("title", ""))[:120],
                        "confidence": r.get("score", 0.5),
                    })
            except Exception:
                pass
        return evidence
