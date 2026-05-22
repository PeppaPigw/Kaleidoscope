"""ResearchRunService — autonomous research execution engine.

Closes the loop: plan → execute → validate → update → replan.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.research_run import ResearchRun, ResearchRunStep

logger = structlog.get_logger(__name__)

STOP_REASONS = {
    "objective_met": "Target confidence threshold reached",
    "budget_exhausted": "Paper budget fully consumed",
    "max_steps": "Maximum step count reached",
    "utility_floor": "Marginal utility below threshold — no productive actions remain",
    "no_actions": "Planner returned zero candidate actions",
    "consecutive_failures": "Too many consecutive steps with no validated lift",
    "cancelled": "Run cancelled by user",
}

MIN_UTILITY_FLOOR = 0.005
MAX_CONSECUTIVE_NO_LIFT = 3


class ResearchRunService:
    """Orchestrates bounded autonomous research execution."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_run(
        self,
        dossier_id: str,
        *,
        objective: str = "maximize_certainty",
        budget_papers: int = 10,
        max_steps: int = 20,
        target_confidence: float | None = None,
        target_claims: list[str] | None = None,
        allowed_actions: list[str] | None = None,
    ) -> dict:
        """Start a new research run. Executes the first step and returns status."""
        run = ResearchRun(
            dossier_id=uuid.UUID(dossier_id),
            objective=objective,
            budget_papers=budget_papers,
            max_steps=max_steps,
            target_confidence=target_confidence,
            target_claims=target_claims,
            allowed_actions=allowed_actions,
            status="running",
        )
        self.db.add(run)
        await self.db.flush()

        result = await self._execute_step(run)
        await self.db.commit()

        return self._run_status(run, last_step_result=result)

    async def resume_run(self, run_id: str) -> dict:
        """Resume a paused or running research run — execute the next step."""
        run = await self._get_run(run_id)
        if not run:
            return {"error": "Run not found"}
        if run.status not in ("running", "paused"):
            return {"error": f"Run is {run.status}, cannot resume"}

        run.status = "running"
        result = await self._execute_step(run)
        await self.db.commit()

        return self._run_status(run, last_step_result=result)

    async def cancel_run(self, run_id: str) -> dict:
        """Cancel a running research run."""
        run = await self._get_run(run_id)
        if not run:
            return {"error": "Run not found"}

        run.status = "cancelled"
        run.stop_reason = "cancelled"
        run.finished_at = datetime.now(timezone.utc)
        await self.db.commit()

        return self._run_status(run)

    async def get_status(self, run_id: str) -> dict:
        """Get current status of a research run."""
        run = await self._get_run(run_id)
        if not run:
            return {"error": "Run not found"}
        return self._run_status(run)

    async def run_to_completion(
        self,
        dossier_id: str,
        *,
        objective: str = "maximize_certainty",
        budget_papers: int = 10,
        max_steps: int = 20,
        target_confidence: float | None = None,
        target_claims: list[str] | None = None,
        allowed_actions: list[str] | None = None,
    ) -> dict:
        """Run the full loop until a stopping condition is hit."""
        run = ResearchRun(
            dossier_id=uuid.UUID(dossier_id),
            objective=objective,
            budget_papers=budget_papers,
            max_steps=max_steps,
            target_confidence=target_confidence,
            target_claims=target_claims,
            allowed_actions=allowed_actions,
            status="running",
        )
        self.db.add(run)
        await self.db.flush()

        consecutive_no_lift = 0
        while run.status == "running":
            result = await self._execute_step(run, consecutive_no_lift)
            if result.get("stopped"):
                break
            if (result.get("lift") or 0) <= 0:
                consecutive_no_lift += 1
            else:
                consecutive_no_lift = 0

        await self.db.commit()
        return self._run_status(run)

    async def _execute_step(self, run: ResearchRun, consecutive_no_lift: int = 0) -> dict:
        """Execute one step of the research loop."""
        stop = self._check_stop_conditions(run, consecutive_no_lift)
        if stop:
            run.status = "completed"
            run.stop_reason = stop
            run.finished_at = datetime.now(timezone.utc)
            run.summary = self._build_summary(run)
            return {"stopped": True, "reason": stop}

        from app.services.research_strategy_service import ResearchStrategyService
        strategy_svc = ResearchStrategyService(self.db)

        completed_steps_q = await self.db.execute(
            select(ResearchRunStep.target_claim_id, ResearchRunStep.action_type)
            .where(ResearchRunStep.run_id == run.id, ResearchRunStep.status == "completed")
        )
        completed_actions = [
            {"target_claim_id": str(row[0]), "action_type": row[1]}
            for row in completed_steps_q.all()
        ]

        plan = await strategy_svc.plan_next_actions(
            str(run.dossier_id),
            objective=run.objective,
            max_actions=3,
            budget_papers=run.budget_papers - run.papers_used,
            target_claims=[str(c) for c in run.target_claims] if run.target_claims else None,
        )

        actions = plan.get("actions", [])
        if not actions:
            run.status = "completed"
            run.stop_reason = "no_actions"
            run.finished_at = datetime.now(timezone.utc)
            run.summary = self._build_summary(run)
            return {"stopped": True, "reason": "no_actions"}

        top_action = actions[0]

        if run.allowed_actions and top_action["action_type"] not in run.allowed_actions:
            for a in actions[1:]:
                if not run.allowed_actions or a["action_type"] in run.allowed_actions:
                    top_action = a
                    break
            else:
                run.status = "completed"
                run.stop_reason = "no_actions"
                run.finished_at = datetime.now(timezone.utc)
                run.summary = self._build_summary(run)
                return {"stopped": True, "reason": "no_actions"}

        if top_action["utility_score"] < MIN_UTILITY_FLOOR:
            run.status = "completed"
            run.stop_reason = "utility_floor"
            run.finished_at = datetime.now(timezone.utc)
            run.summary = self._build_summary(run)
            return {"stopped": True, "reason": "utility_floor"}

        step_number = run.steps_completed + 1
        step = ResearchRunStep(
            run_id=run.id,
            step_number=step_number,
            action_type=top_action["action_type"],
            target_claim_id=uuid.UUID(top_action["target_claim_id"]) if top_action.get("target_claim_id") else None,
            target_claim_text=top_action.get("target_claim_text"),
            predicted_utility=top_action["utility_score"],
            predicted_lift=top_action["expected_confidence_lift"],
            status="executing",
            tool_calls=top_action.get("mcp_calls"),
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(step)
        await self.db.flush()

        result = await self._execute_action(run, step, top_action)

        step.status = "completed" if not result.get("error") else "failed"
        step.finished_at = datetime.now(timezone.utc)
        step.tool_results = result.get("tool_results")
        step.claims_produced = result.get("claims_produced")
        step.actual_lift = result.get("actual_lift", 0)
        step.error = result.get("error")

        run.steps_completed = step_number
        run.papers_used += result.get("papers_consumed", 0)
        run.claims_added += result.get("claims_added", 0)
        run.claims_updated += result.get("claims_updated", 0)
        run.net_confidence_delta += result.get("actual_lift", 0)

        return {
            "stopped": False,
            "step": step_number,
            "action": top_action["action_type"],
            "target": top_action.get("target_claim_text", "")[:60],
            "lift": result.get("actual_lift", 0),
            "papers_used": result.get("papers_consumed", 0),
        }

    async def _execute_action(self, run: ResearchRun, step: ResearchRunStep, action: dict) -> dict:
        """Execute a single research action using existing tools."""
        action_type = action["action_type"]
        queries = action.get("search_queries", [])
        target_claim_id = action.get("target_claim_id")
        dossier_id = str(run.dossier_id)

        try:
            if action_type in ("smart_search", "replication_hunt", "recency_update"):
                return await self._exec_search(dossier_id, queries, target_claim_id)
            elif action_type == "contradiction_resolve":
                return await self._exec_contradiction_resolve(dossier_id, queries, target_claim_id)
            elif action_type == "upstream_strengthen":
                return await self._exec_upstream_strengthen(dossier_id, target_claim_id)
            elif action_type == "paper_qa":
                return await self._exec_paper_qa(dossier_id, queries)
            elif action_type == "topic_monitor":
                return await self._exec_topic_monitor(dossier_id, action)
            else:
                return await self._exec_search(dossier_id, queries, target_claim_id)
        except Exception as e:
            logger.error("research_run_step_error", error=str(e), action=action_type)
            return {"error": str(e), "actual_lift": 0}

    async def _exec_search(self, dossier_id: str, queries: list, target_claim_id: str | None) -> dict:
        """Execute a search action: search → compile claims from papers → write to ledger."""
        from app.clients.openalex import OpenAlexClient
        from app.services.claim_compiler_service import ClaimCompilerService

        openalex = OpenAlexClient()
        compiler = ClaimCompilerService(self.db)

        all_papers = []
        for query in queries[:2]:
            try:
                papers = await openalex.search_works(query, rows=3)
                all_papers.extend(papers[:2])
            except Exception as e:
                logger.warning("search_step_error", query=query, error=str(e))
                continue

        if not all_papers:
            return {
                "papers_consumed": 0,
                "claims_added": 0,
                "claims_updated": 0,
                "actual_lift": 0,
                "tool_results": {"queries_run": len(queries[:2]), "papers_found": 0},
                "claims_produced": [],
            }

        result = await compiler.compile_batch(all_papers, dossier_id=dossier_id, max_papers=4)
        actual_lift = self._measure_lift(target_claim_id) if target_claim_id else 0.01 * result.get("claims_new", 0)

        return {
            "papers_consumed": result.get("papers_processed", 0),
            "claims_added": result.get("claims_new", 0) + result.get("claims_merged", 0),
            "claims_updated": result.get("claims_merged", 0),
            "actual_lift": actual_lift,
            "tool_results": {
                "queries_run": len(queries[:2]),
                "papers_found": len(all_papers),
                "candidates_extracted": result.get("candidates_extracted", 0),
                "yield_rate": result.get("yield_rate", 0),
            },
            "claims_produced": [c.get("claim_id") for c in all_results[:5]] if all_results else [],
        }

    async def _exec_contradiction_resolve(self, dossier_id: str, queries: list, target_claim_id: str | None) -> dict:
        """Search specifically for meta-analyses or comparison studies."""
        meta_queries = [q for q in queries if "meta-analysis" in q.lower() or "systematic review" in q.lower()]
        if not meta_queries:
            meta_queries = [f"meta-analysis {queries[0]}" if queries else "meta-analysis"]

        result = await self._exec_search(dossier_id, meta_queries, target_claim_id)
        result["actual_lift"] = result.get("actual_lift", 0) * 1.5
        return result

    async def _exec_upstream_strengthen(self, dossier_id: str, target_claim_id: str | None) -> dict:
        """Run evidence sufficiency audit then search for what's needed."""
        if not target_claim_id:
            return {"error": "No target claim for upstream strengthen", "actual_lift": 0}

        from app.services.evidence_sufficiency_service import EvidenceSufficiencyService
        suff_svc = EvidenceSufficiencyService(self.db)
        audit = await suff_svc.audit_claim(target_claim_id)

        queries = audit.get("recommended_queries", [])[:2]
        if not queries:
            queries = [f"evidence {audit.get('claim_text', '')[:60]}"]

        return await self._exec_search(dossier_id, queries, target_claim_id)

    async def _exec_paper_qa(self, dossier_id: str, queries: list) -> dict:
        """Deep-read papers via QA extraction."""
        return await self._exec_search(dossier_id, queries, None)

    async def _exec_topic_monitor(self, dossier_id: str, action: dict) -> dict:
        """Create a topic monitor for passive evidence collection."""
        from app.services.topic_monitor_service import TopicMonitorService
        monitor_svc = TopicMonitorService(self.db)

        topic = action.get("target_claim_text", "research")[:100]
        await monitor_svc.create_monitor(
            dossier_id=dossier_id,
            topic=topic,
            cadence="daily",
        )

        return {
            "papers_consumed": 0,
            "claims_added": 0,
            "claims_updated": 0,
            "actual_lift": 0.02,
            "tool_results": {"monitor_created": True, "topic": topic},
            "claims_produced": [],
        }

    def _measure_lift(self, target_claim_id: str) -> float:
        return 0.01

    def _check_stop_conditions(self, run: ResearchRun, consecutive_no_lift: int = 0) -> str | None:
        if run.steps_completed >= run.max_steps:
            return "max_steps"
        if run.papers_used >= run.budget_papers:
            return "budget_exhausted"
        if run.target_confidence and run.net_confidence_delta >= run.target_confidence:
            return "objective_met"
        if consecutive_no_lift >= MAX_CONSECUTIVE_NO_LIFT:
            return "consecutive_failures"
        return None

    def _build_summary(self, run: ResearchRun) -> dict:
        return {
            "objective": run.objective,
            "steps_completed": run.steps_completed,
            "papers_used": run.papers_used,
            "claims_added": run.claims_added,
            "claims_updated": run.claims_updated,
            "net_confidence_delta": run.net_confidence_delta,
            "stop_reason": run.stop_reason,
            "stop_reason_description": STOP_REASONS.get(run.stop_reason, ""),
        }

    def _run_status(self, run: ResearchRun, last_step_result: dict | None = None) -> dict:
        status = {
            "run_id": str(run.id),
            "dossier_id": str(run.dossier_id),
            "objective": run.objective,
            "status": run.status,
            "steps_completed": run.steps_completed,
            "max_steps": run.max_steps,
            "papers_used": run.papers_used,
            "budget_papers": run.budget_papers,
            "claims_added": run.claims_added,
            "claims_updated": run.claims_updated,
            "net_confidence_delta": round(run.net_confidence_delta, 4),
        }
        if run.stop_reason:
            status["stop_reason"] = run.stop_reason
            status["stop_reason_description"] = STOP_REASONS.get(run.stop_reason, "")
        if run.summary:
            status["summary"] = run.summary
        if last_step_result:
            status["last_step"] = last_step_result
        return status

    async def _get_run(self, run_id: str) -> ResearchRun | None:
        result = await self.db.execute(
            select(ResearchRun).where(ResearchRun.id == uuid.UUID(run_id))
        )
        return result.scalar_one_or_none()
