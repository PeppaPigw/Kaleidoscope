"""DecisionCompilerService — Decision Compiler.

Converts epistemic state (claims, threads, causal models) into a structured
decision record: what to do, why, under which assumptions, and what evidence
would reverse the call.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DECISION_SYSTEM = """You are a decision compiler. Given research evidence (supporting claims, contradicting claims, causal model, cruxes, and options), produce a structured decision recommendation.

Rules:
- If evidence is insufficient or cruxes are unresolved, output status "conditional" or "abstain"
- Separate evidence confidence from decision confidence
- Identify assumptions that must hold for the recommendation to be valid
- Identify boundary conditions where the recommendation breaks down
- Specify change-my-mind triggers: what new evidence would flip the decision

Output JSON:
{"status": "recommended|conditional|abstain", "recommended_option_id": "id or null", "decision_confidence": 0.0-1.0, "why_now": "one sentence on timing", "reasoning": "2-3 sentences on why this option wins", "assumptions": ["assumption 1"], "boundary_conditions": ["condition where this breaks"], "change_my_mind_triggers": ["evidence that would flip this"], "execution_steps": ["step 1", "step 2"], "risks": ["risk 1"]}"""

DECISION_PROMPT = """Decision question: {question}

Options:
{options_text}

Supporting evidence ({support_count} claims):
{supports}

Contradicting evidence ({contradict_count} claims):
{contradicts}

Unresolved cruxes: {cruxes}

Causal predictions: {predictions}

Constraints: {constraints}

Compile the decision. Return ONLY valid JSON."""

OPTIONS_SYSTEM = """You are a decision option generator. Given a research question and evidence, generate 2-4 distinct actionable options that represent genuinely different approaches.

Output JSON:
{"options": [{"id": "opt_1", "title": "short title", "description": "one sentence", "expected_outcome": "what happens if chosen", "risk_level": "low|medium|high"}]}"""

OPTIONS_PROMPT = """Decision question: {question}

Key evidence:
{evidence_text}

Research threads:
{threads_text}

Generate 2-4 distinct options. Return ONLY valid JSON."""


class DecisionCompilerService:
    """Compiles research into structured, monitorable decisions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compile_decision(
        self,
        dossier_id: str,
        *,
        decision_question: str,
        options: list[dict] | None = None,
        objective: str = "maximize_expected_value",
        constraints: dict | None = None,
        auto_monitor: bool = True,
    ) -> dict:
        """Compile a full decision record from dossier state."""
        from app.clients.llm_client import LLMClient

        program = await self._get_program_state(dossier_id)
        if program.get("error"):
            return {"error": program["error"], "dossier_id": dossier_id}

        threads = program.get("threads", [])
        bridges = program.get("bridges", [])
        agenda = program.get("agenda", [])

        evidence = await self._gather_evidence(dossier_id, threads)

        if not options:
            options = await self._generate_options(
                decision_question, evidence, threads
            )

        crux_summary = await self._get_cruxes(decision_question, dossier_id)
        causal_predictions = await self._get_causal_predictions(dossier_id, decision_question)

        llm = LLMClient()

        options_text = "\n".join(
            f"- [{o.get('id', f'opt_{i}')}] {o.get('title', 'Untitled')}: {o.get('description', '')}"
            for i, o in enumerate(options)
        )
        supports_text = "\n".join(
            f"- {s['text'][:100]} (strength={s.get('strength', 0):.0f})"
            for s in evidence.get("supporting", [])[:8]
        ) or "None found"
        contradicts_text = "\n".join(
            f"- {c['text'][:100]} (strength={c.get('strength', 0):.0f})"
            for c in evidence.get("contradicting", [])[:5]
        ) or "None found"
        cruxes_text = ", ".join(
            c.get("text", "")[:60] for c in crux_summary[:3]
        ) or "None identified"
        predictions_text = ", ".join(
            p.get("predicted_effect", "")[:60] for p in causal_predictions[:3]
        ) or "None available"
        constraints_text = str(constraints or {"risk_tolerance": "medium"})

        raw = await llm.complete(
            prompt=DECISION_PROMPT.format(
                question=decision_question,
                options_text=options_text,
                support_count=len(evidence.get("supporting", [])),
                supports=supports_text,
                contradict_count=len(evidence.get("contradicting", [])),
                contradicts=contradicts_text,
                cruxes=cruxes_text,
                predictions=predictions_text,
                constraints=constraints_text,
            ),
            system=DECISION_SYSTEM,
            max_tokens=2048,
            temperature=0.2,
        )
        decision_data = self._parse_json(raw)

        decision_id = str(uuid.uuid4())
        status = decision_data.get("status", "conditional")
        rec_option_id = decision_data.get("recommended_option_id")

        recommended_option = None
        ranked_options = []
        for o in options:
            oid = o.get("id", "")
            is_recommended = (oid == rec_option_id)
            entry = {
                "id": oid,
                "title": o.get("title", ""),
                "description": o.get("description", ""),
                "is_recommended": is_recommended,
                "confidence": decision_data.get("decision_confidence", 0) if is_recommended else 0,
            }
            if is_recommended:
                recommended_option = entry
            ranked_options.append(entry)

        if not recommended_option and ranked_options:
            recommended_option = ranked_options[0]
            recommended_option["is_recommended"] = True

        ranked_options.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        decisive_claims = [
            {"claim_id": s.get("claim_id"), "text": s["text"][:80], "role": "supporting"}
            for s in evidence.get("supporting", [])[:5]
        ] + [
            {"claim_id": c.get("claim_id"), "text": c["text"][:80], "role": "contradicting"}
            for c in evidence.get("contradicting", [])[:3]
        ]

        fragility = self._compute_fragility(evidence, crux_summary)

        monitor_triggers = []
        if auto_monitor:
            for trigger in decision_data.get("change_my_mind_triggers", []):
                monitor_triggers.append({
                    "trigger": trigger,
                    "type": "evidence_change",
                    "action": "re_evaluate_decision",
                })
            for crux in crux_summary[:2]:
                monitor_triggers.append({
                    "trigger": f"Crux resolved: {crux.get('text', '')[:50]}",
                    "type": "crux_resolution",
                    "action": "re_evaluate_decision",
                })

        return {
            "decision_id": decision_id,
            "dossier_id": dossier_id,
            "decision_question": decision_question,
            "status": status,
            "recommended_option": recommended_option,
            "ranked_options": ranked_options,
            "decision_confidence": decision_data.get("decision_confidence", 0),
            "why_now": decision_data.get("why_now", ""),
            "reasoning": decision_data.get("reasoning", ""),
            "expected_outcomes": causal_predictions[:3],
            "decisive_claims": decisive_claims,
            "unresolved_cruxes": crux_summary[:5],
            "assumptions": decision_data.get("assumptions", []),
            "boundary_conditions": decision_data.get("boundary_conditions", []),
            "fragility": fragility,
            "change_my_mind_triggers": monitor_triggers,
            "execution_steps": decision_data.get("execution_steps", []),
            "risks": decision_data.get("risks", []),
            "constraints": constraints or {},
            "provenance": {
                "threads_analyzed": len(threads),
                "claims_considered": len(evidence.get("supporting", [])) + len(evidence.get("contradicting", [])),
                "cruxes_identified": len(crux_summary),
                "causal_predictions": len(causal_predictions),
            },
        }

    async def _get_program_state(self, dossier_id: str) -> dict:
        from app.services.research_program_service import ResearchProgramService
        svc = ResearchProgramService(self.db)
        return await svc.compile_program(dossier_id, mode="refresh")

    async def _gather_evidence(self, dossier_id: str, threads: list) -> dict:
        from sqlalchemy import select
        import uuid as uuid_mod
        from app.models.claim_ledger import GlobalClaim, ClaimMention, ClaimRelation

        mention_q = await self.db.execute(
            select(ClaimMention.global_claim_id)
            .where(ClaimMention.dossier_id == uuid_mod.UUID(dossier_id))
            .distinct()
            .limit(50)
        )
        claim_ids = [r[0] for r in mention_q.all()]
        if not claim_ids:
            return {"supporting": [], "contradicting": [], "qualifying": []}

        claims_q = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.id.in_(claim_ids))
        )
        claims = list(claims_q.scalars().all())

        supporting = []
        contradicting = []
        qualifying = []

        for c in claims:
            entry = {
                "claim_id": str(c.id),
                "text": c.canonical_text,
                "strength": c.evidence_strength_score or 0,
                "confidence": c.effective_confidence or c.direct_confidence or 0,
            }
            if (c.support_count or 0) > (c.contradict_count or 0):
                supporting.append(entry)
            elif (c.contradict_count or 0) > (c.support_count or 0):
                contradicting.append(entry)
            else:
                qualifying.append(entry)

        supporting.sort(key=lambda x: x["strength"], reverse=True)
        contradicting.sort(key=lambda x: x["strength"], reverse=True)

        return {
            "supporting": supporting,
            "contradicting": contradicting,
            "qualifying": qualifying,
        }

    async def _generate_options(
        self, question: str, evidence: dict, threads: list
    ) -> list[dict]:
        from app.clients.llm_client import LLMClient

        evidence_text = "\n".join(
            f"- {s['text'][:80]}" for s in evidence.get("supporting", [])[:5]
        ) or "Limited evidence available"
        threads_text = "\n".join(
            f"- {t['title']}: {t.get('thesis', '')[:60]}" for t in threads[:4]
        ) or "No threads"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OPTIONS_PROMPT.format(
                question=question,
                evidence_text=evidence_text,
                threads_text=threads_text,
            ),
            system=OPTIONS_SYSTEM,
            max_tokens=1024,
            temperature=0.3,
        )
        data = self._parse_json(raw)
        options = data.get("options", [])
        if not options:
            options = [
                {"id": "opt_proceed", "title": "Proceed with current evidence", "description": "Act on available evidence"},
                {"id": "opt_investigate", "title": "Investigate further", "description": "Gather more evidence before deciding"},
            ]
        return options

    async def _get_cruxes(self, question: str, dossier_id: str) -> list:
        try:
            from app.services.crux_engine_service import CruxEngineService
            svc = CruxEngineService(self.db)
            result = await svc.analyze_question(
                question, dossier_id=dossier_id,
                n_theses=2, resolve_cruxes=False, budget_papers=0,
            )
            return result.get("crux_claims", [])
        except Exception as e:
            logger.warning("crux_fetch_error", error=str(e))
            return []

    async def _get_causal_predictions(self, dossier_id: str, question: str) -> list:
        try:
            from app.services.causal_model_service import CausalModelService
            svc = CausalModelService(self.db)
            result = await svc.compile_model(
                dossier_id=dossier_id, question=question,
                mode="intervene", max_claims=15,
            )
            return result.get("intervention_predictions", [])
        except Exception as e:
            logger.warning("causal_prediction_error", error=str(e))
            return []

    def _compute_fragility(self, evidence: dict, cruxes: list) -> dict:
        supporting = evidence.get("supporting", [])
        contradicting = evidence.get("contradicting", [])

        if not supporting:
            return {"score": 1.0, "level": "high", "reason": "No supporting evidence"}

        avg_strength = sum(s["strength"] for s in supporting) / len(supporting)
        contradiction_ratio = len(contradicting) / (len(supporting) + len(contradicting)) if (supporting or contradicting) else 0
        unresolved_crux_penalty = min(0.3, len(cruxes) * 0.1)

        fragility_score = (
            (1.0 - avg_strength / 100.0) * 0.4
            + contradiction_ratio * 0.3
            + unresolved_crux_penalty
        )
        fragility_score = max(0.0, min(1.0, fragility_score))

        level = "low" if fragility_score < 0.3 else "medium" if fragility_score < 0.6 else "high"

        return {
            "score": round(fragility_score, 3),
            "level": level,
            "reason": (
                f"avg_evidence_strength={avg_strength:.0f}, "
                f"contradiction_ratio={contradiction_ratio:.2f}, "
                f"unresolved_cruxes={len(cruxes)}"
            ),
        }

    def _parse_json(self, text: str) -> dict:
        import json
        import re
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        fence = re.search(r"```(?:json)?\s*\n?(.*?)(?:\n?```|$)", text, re.DOTALL)
        if fence:
            candidate = fence.group(1).strip()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                repaired = self._repair_json(candidate)
                if repaired:
                    return repaired
        match = re.search(r"\{.*", text, re.DOTALL)
        if match:
            candidate = match.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                repaired = self._repair_json(candidate)
                if repaired:
                    return repaired
        return {}

    def _repair_json(self, text: str) -> dict | None:
        import json
        text = text.rstrip().rstrip(",")
        stack = []
        in_string = False
        escape = False
        for ch in text:
            if escape:
                escape = False
                continue
            if ch == '\\' and in_string:
                escape = True
                continue
            if ch == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                stack.append('}')
            elif ch == '[':
                stack.append(']')
            elif ch in ('}', ']'):
                if stack and stack[-1] == ch:
                    stack.pop()
        if in_string:
            text += '"'
        text = text.rstrip().rstrip(",")
        text += ''.join(reversed(stack))
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
