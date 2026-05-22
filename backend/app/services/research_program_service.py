"""ResearchProgramService — Research Program Compiler.

Compiles a dossier into a persistent, thread-aware, executable research program.
Decides the next highest-value epistemic move across threads, cruxes, and causal gaps.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class ResearchProgramService:
    """Orchestrates research across threads, cruxes, and causal models."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compile_program(
        self,
        dossier_id: str,
        *,
        objective: str = "maximize_certainty",
        max_threads: int = 5,
        mode: str = "build",
    ) -> dict:
        """Compile a dossier into a thread-aware research program."""
        from app.services.research_thread_service import ResearchThreadService

        thread_svc = ResearchThreadService(self.db)
        thread_result = await thread_svc.compile_threads(
            dossier_id, max_threads=max_threads
        )

        if thread_result.get("error"):
            return {"error": thread_result["error"], "dossier_id": dossier_id}

        threads = thread_result.get("threads", [])
        bridges = thread_result.get("bridge_claims", [])

        program_id = str(uuid.uuid4())
        program_threads = []

        for t in threads:
            program_threads.append({
                "thread_id": t["thread_id"],
                "title": t["title"],
                "thesis": t.get("thesis", ""),
                "confidence": t.get("confidence", 0),
                "evidence_coverage": t.get("evidence_coverage", 0),
                "claim_count": len(t.get("claim_ids", [])),
                "claim_ids": t.get("claim_ids", []),
                "open_questions": t.get("open_questions", []),
                "status": "active",
            })

        agenda = self._build_agenda(program_threads, bridges, objective)

        portfolio_priority = sorted(
            program_threads,
            key=lambda t: self._thread_priority(t, bridges, objective),
            reverse=True,
        )

        return {
            "program_id": program_id,
            "dossier_id": dossier_id,
            "objective": objective,
            "status": "compiled",
            "threads": program_threads,
            "bridges": bridges,
            "agenda": agenda[:10],
            "portfolio_priority": [
                {"thread_id": t["thread_id"], "title": t["title"],
                 "priority_score": round(self._thread_priority(t, bridges, objective), 3)}
                for t in portfolio_priority
            ],
            "stats": {
                "threads": len(program_threads),
                "bridges": len(bridges),
                "agenda_items": len(agenda),
                "total_claims": sum(t["claim_count"] for t in program_threads),
            },
        }

    async def step_program(
        self,
        dossier_id: str,
        *,
        budget_papers: int = 4,
        max_actions: int = 1,
        thread_policy: str = "highest_voi",
        objective: str = "maximize_certainty",
    ) -> dict:
        """Execute one step of the research program."""
        program = await self.compile_program(
            dossier_id, objective=objective, mode="refresh"
        )
        if program.get("error"):
            return program

        agenda = program.get("agenda", [])
        if not agenda:
            return {
                "status": "complete",
                "reason": "No actionable items in agenda",
                "dossier_id": dossier_id,
            }

        if thread_policy == "bridge_first":
            bridge_actions = [a for a in agenda if a.get("is_bridge")]
            selected = bridge_actions[:max_actions] if bridge_actions else agenda[:max_actions]
        elif thread_policy == "depth_first":
            selected = agenda[:max_actions]
        else:
            selected = agenda[:max_actions]

        results = []
        for action in selected:
            result = await self._execute_action(action, dossier_id, budget_papers)
            results.append(result)

        return {
            "status": "stepped",
            "dossier_id": dossier_id,
            "actions_taken": len(results),
            "results": results,
            "remaining_agenda": len(agenda) - len(selected),
            "next_priority": agenda[len(selected)] if len(agenda) > len(selected) else None,
        }

    async def run_program(
        self,
        dossier_id: str,
        *,
        objective: str = "maximize_certainty",
        budget_papers: int = 20,
        max_steps: int = 5,
        target_confidence: float = 0.7,
    ) -> dict:
        """Run the full research program autonomously."""
        steps_taken = 0
        papers_used = 0
        all_results = []
        stop_reason = None

        for _ in range(max_steps):
            if papers_used >= budget_papers:
                stop_reason = "budget_exhausted"
                break

            remaining_budget = budget_papers - papers_used
            per_step = max(2, remaining_budget // max(1, max_steps - steps_taken))

            step_result = await self.step_program(
                dossier_id,
                budget_papers=per_step,
                max_actions=1,
                objective=objective,
            )

            if step_result.get("status") == "complete":
                stop_reason = "agenda_empty"
                break

            steps_taken += 1
            all_results.append(step_result)

            for r in step_result.get("results", []):
                papers_used += r.get("papers_searched", 0)

            program = await self.compile_program(dossier_id, objective=objective, mode="refresh")
            threads = program.get("threads", [])
            if threads:
                avg_conf = sum(t["confidence"] for t in threads) / len(threads)
                if avg_conf >= target_confidence:
                    stop_reason = "target_confidence_met"
                    break

        if not stop_reason:
            stop_reason = "max_steps"

        final_program = await self.compile_program(dossier_id, objective=objective, mode="refresh")
        final_threads = final_program.get("threads", [])

        return {
            "status": "completed",
            "dossier_id": dossier_id,
            "objective": objective,
            "stop_reason": stop_reason,
            "steps_taken": steps_taken,
            "papers_used": papers_used,
            "per_thread_progress": [
                {
                    "thread_id": t["thread_id"],
                    "title": t["title"],
                    "confidence": t["confidence"],
                    "evidence_coverage": t["evidence_coverage"],
                }
                for t in final_threads
            ],
            "open_cruxes": [
                a for a in final_program.get("agenda", [])
                if a.get("action_type") == "resolve_crux"
            ][:5],
            "unresolved_bridges": final_program.get("bridges", []),
            "results_summary": all_results[-3:] if all_results else [],
        }

    def _build_agenda(self, threads: list, bridges: list, objective: str) -> list:
        agenda = []

        for bridge in bridges:
            agenda.append({
                "action_type": "resolve_bridge",
                "is_bridge": True,
                "claim_id": bridge.get("claim_id"),
                "from_thread_id": bridge.get("from_thread_id"),
                "to_thread_id": bridge.get("to_thread_id"),
                "priority": 0.9,
                "rationale": f"Bridge claim connects threads — resolving unlocks both",
                "tool": "claim_resolve",
                "tool_args": {"claim_id": bridge.get("claim_id"), "objective": "strengthen"},
            })

        for t in threads:
            if t["confidence"] < 0.3:
                agenda.append({
                    "action_type": "strengthen_thread",
                    "is_bridge": False,
                    "thread_id": t["thread_id"],
                    "thread_title": t["title"],
                    "priority": 0.8 - t["confidence"],
                    "rationale": f"Thread '{t['title']}' has low confidence ({t['confidence']:.2f})",
                    "tool": "research_run_start",
                    "tool_args": {
                        "objective": objective,
                        "budget_papers": 4,
                        "target_claims": t.get("claim_ids", [])[:3],
                    },
                })

            for q in t.get("open_questions", [])[:2]:
                agenda.append({
                    "action_type": "resolve_question",
                    "is_bridge": False,
                    "thread_id": t["thread_id"],
                    "question": q,
                    "priority": 0.6,
                    "rationale": f"Open question in '{t['title']}'",
                    "tool": "question_resolve",
                    "tool_args": {"question": q},
                })

            if t["evidence_coverage"] < 0.15 and t.get("claim_ids"):
                agenda.append({
                    "action_type": "resolve_crux",
                    "is_bridge": False,
                    "thread_id": t["thread_id"],
                    "priority": 0.7,
                    "rationale": f"Low evidence coverage ({t['evidence_coverage']:.2f}) in '{t['title']}'",
                    "tool": "crux_analyze",
                    "tool_args": {"question": t.get("thesis", t["title"])},
                })

        agenda.sort(key=lambda a: a["priority"], reverse=True)
        return agenda

    def _thread_priority(self, thread: dict, bridges: list, objective: str) -> float:
        score = 0.0
        bridge_count = sum(
            1 for b in bridges
            if b.get("from_thread_id") == thread["thread_id"]
            or b.get("to_thread_id") == thread["thread_id"]
        )
        score += bridge_count * 0.2
        score += (1.0 - thread["confidence"]) * 0.5
        score += (1.0 - thread["evidence_coverage"]) * 0.3
        return score

    async def _execute_action(self, action: dict, dossier_id: str, budget: int) -> dict:
        tool = action.get("tool")
        args = action.get("tool_args", {})

        try:
            if tool == "claim_resolve":
                from app.services.claim_resolution_service import ClaimResolutionService
                svc = ClaimResolutionService(self.db)
                claim_id = args.get("claim_id")
                if not claim_id:
                    return {"action": action["action_type"], "status": "skipped", "reason": "no claim_id"}
                result = await svc.resolve_claim(
                    claim_id, objective=args.get("objective", "strengthen"),
                    budget_papers=budget, dossier_id=dossier_id,
                )
                return {
                    "action": action["action_type"],
                    "tool": tool,
                    "status": result.get("status", "unknown"),
                    "papers_searched": result.get("papers_searched", 0),
                    "confidence_delta": result.get("confidence_delta", 0),
                }

            elif tool == "question_resolve":
                from app.services.question_resolution_service import QuestionResolutionService
                svc = QuestionResolutionService(self.db)
                result = await svc.resolve_question(
                    args.get("question", ""),
                    dossier_id=dossier_id, budget_papers=budget,
                )
                return {
                    "action": action["action_type"],
                    "tool": tool,
                    "status": "resolved" if result.get("answer") else "no_answer",
                    "confidence": result.get("confidence", 0),
                    "papers_searched": result.get("trace", {}).get("papers_budget", 0),
                }

            elif tool == "crux_analyze":
                from app.services.crux_engine_service import CruxEngineService
                svc = CruxEngineService(self.db)
                result = await svc.analyze_question(
                    args.get("question", ""),
                    dossier_id=dossier_id, resolve_cruxes=False, budget_papers=budget,
                )
                return {
                    "action": action["action_type"],
                    "tool": tool,
                    "status": result.get("status", "unknown"),
                    "winning_thesis": result.get("winning_thesis"),
                    "cruxes_found": len(result.get("crux_claims", [])),
                }

            elif tool == "research_run_start":
                from app.services.research_run_service import ResearchRunService
                svc = ResearchRunService(self.db)
                result = await svc.start_run(
                    dossier_id=dossier_id,
                    objective=args.get("objective", "maximize_certainty"),
                    budget_papers=budget,
                    max_steps=3,
                )
                return {
                    "action": action["action_type"],
                    "tool": tool,
                    "status": result.get("status", "unknown"),
                    "papers_searched": result.get("papers_used", 0),
                    "claims_added": result.get("claims_added", 0),
                }

            else:
                return {"action": action["action_type"], "status": "unsupported_tool", "tool": tool}

        except Exception as e:
            logger.warning("program_action_error", action=action["action_type"], error=str(e))
            return {"action": action["action_type"], "status": "error", "error": str(e)[:200]}
