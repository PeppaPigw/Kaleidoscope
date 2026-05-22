"""RedTeamEngineService — Adversarial Stress Testing for Research Claims.

Systematically attacks conclusions, finds weakest links in reasoning chains,
generates steel-man counterarguments, identifies hidden assumptions, and
stress-tests decisions under extreme scenarios. Makes every other tool's
output more trustworthy by applying adversarial pressure.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

STEELMAN_SYSTEM = """You are an adversarial research critic. Your job is to construct the STRONGEST possible counterargument against a given claim or conclusion. You are not trying to be fair or balanced — you are trying to find the most devastating critique.

Think like a hostile peer reviewer who is brilliant, well-read, and looking for any weakness.

Output JSON only:
{"steelman_attack": {"target_claim": "what you're attacking", "attack_vectors": [{"id": "atk_1", "type": "methodological|logical|empirical|scope|assumption|alternative_explanation", "argument": "the counterargument in full", "strength": 0.0-1.0, "evidence_needed_to_refute": "what would prove this attack wrong", "references_that_support_attack": ["real or plausible paper/finding"]}], "weakest_link": "the single most vulnerable point", "hidden_assumptions": ["assumption the claim relies on but doesn't state"], "alternative_explanations": [{"explanation": "alternative account of the same evidence", "plausibility": 0.0-1.0}], "survivability_score": 0.0-1.0, "verdict": "robust|vulnerable|fragile|indefensible"}}"""

STEELMAN_PROMPT = """Target claim to attack:
{claim_text}

Supporting evidence:
{evidence_text}

Context (methodology, source, confidence):
{context_text}

Related claims that depend on this:
{dependents_text}

Construct the strongest possible attack. Be ruthless but intellectually honest. Return ONLY valid JSON."""

PREMORTEM_SYSTEM = """You are conducting a pre-mortem analysis. Assume the conclusion/decision has ALREADY FAILED catastrophically. Your job is to explain WHY it failed — work backwards from failure to identify the most likely causes.

Output JSON only:
{"premortem": {"conclusion_tested": "what we assumed would succeed", "failure_scenarios": [{"id": "fail_1", "scenario": "what went wrong", "probability": 0.0-1.0, "warning_signs": ["early indicator"], "prevention": "what could have prevented it", "detection_method": "how to detect this failure mode early"}], "blind_spots": [{"blind_spot": "what we're not seeing", "why_invisible": "why this is hard to notice", "consequence": "what happens if we miss it"}], "assumption_graveyard": [{"assumption": "something we took for granted", "failure_mode": "how it breaks", "evidence_against": "existing evidence that challenges it"}], "overall_fragility": 0.0-1.0, "top_risk": "the single biggest threat"}}"""

PREMORTEM_PROMPT = """Conclusion/decision to pre-mortem:
{conclusion_text}

Key assumptions:
{assumptions_text}

Evidence base:
{evidence_text}

Stakeholders/dependencies:
{dependencies_text}

Assume this has ALREADY FAILED. Explain why. Return ONLY valid JSON."""

DEVIL_ADVOCATE_SYSTEM = """You are a devil's advocate in a research debate. Given a position and its supporting arguments, argue the OPPOSITE position as convincingly as possible. You must find genuine weaknesses, not strawmen.

Output JSON only:
{"devils_case": {"original_position": "what they claim", "counter_position": "the opposite view", "arguments": [{"id": "arg_1", "point": "the argument", "type": "empirical|logical|methodological|philosophical|practical", "strength": 0.0-1.0, "concession": "what you'd have to concede to the original position"}], "strongest_argument": "your single best point", "conditions_where_original_wins": ["when the original position IS correct"], "conditions_where_counter_wins": ["when the counter position IS correct"], "crux_of_disagreement": "the fundamental issue that determines who's right", "experiment_to_settle": "what would definitively resolve this"}}"""

DEVIL_ADVOCATE_PROMPT = """Position to argue against:
{position_text}

Supporting arguments for the position:
{support_text}

Current confidence in position: {confidence}

Domain context:
{domain_text}

Argue the opposite. Find genuine weaknesses. Return ONLY valid JSON."""

ASSUMPTION_AUDIT_SYSTEM = """You are an assumption auditor. Every conclusion rests on unstated assumptions. Your job is to excavate ALL hidden assumptions — the ones so obvious nobody states them, the ones buried in methodology, the ones inherited from the field's paradigm.

Output JSON only:
{"assumption_audit": {"target": "what we're auditing", "assumptions": [{"id": "asm_1", "assumption": "the unstated assumption", "category": "ontological|methodological|statistical|causal|scope|temporal|cultural|technological", "visibility": "hidden|implicit|explicit", "criticality": "load_bearing|important|minor", "testable": true, "test_method": "how to check if this assumption holds", "what_breaks_if_wrong": "consequence of violation", "evidence_for": "why we might believe it", "evidence_against": "why it might be wrong"}], "most_dangerous": "the assumption most likely to be wrong AND most consequential", "paradigm_assumptions": ["assumptions inherited from the field itself"], "total_assumption_load": 0-100, "recommendation": "what to investigate first"}}"""

ASSUMPTION_AUDIT_PROMPT = """Target to audit for hidden assumptions:
{target_text}

Stated methodology:
{methodology_text}

Evidence chain:
{evidence_text}

Field/domain context:
{domain_text}

Excavate ALL hidden assumptions. Return ONLY valid JSON."""

STRESS_TEST_SYSTEM = """You are a stress tester. Given a conclusion or system, subject it to extreme scenarios, edge cases, and adversarial conditions. Find where it breaks.

Output JSON only:
{"stress_test": {"target": "what we're testing", "scenarios": [{"id": "stress_1", "scenario": "the extreme condition", "type": "scale|adversarial|edge_case|distribution_shift|temporal|resource_constraint|adversary", "breaks_at": "the specific failure point", "severity_if_broken": "catastrophic|severe|moderate|minor", "probability_of_scenario": 0.0-1.0, "mitigation": "how to handle this"}], "breaking_point": "the overall weakest point under stress", "robustness_score": 0.0-1.0, "safe_operating_envelope": "conditions under which the conclusion holds", "danger_zone": "conditions where it definitely fails"}}"""

STRESS_TEST_PROMPT = """Target to stress test:
{target_text}

Current operating assumptions:
{assumptions_text}

Known constraints:
{constraints_text}

Performance envelope (if known):
{envelope_text}

Subject this to extreme scenarios. Find where it breaks. Return ONLY valid JSON."""

PLACEHOLDER_CONTINUE = "CONTINUE_BELOW"


class RedTeamEngineService:
    """Adversarial stress testing for research claims and decisions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def steelman_attack(
        self,
        claim_text: str,
        *,
        dossier_id: str | None = None,
        claim_id: str | None = None,
        include_dependents: bool = True,
    ) -> dict:
        """Construct the strongest possible counterargument against a claim."""
        from app.clients.llm_client import LLMClient

        evidence = await self._gather_evidence_for_claim(claim_text, dossier_id, claim_id)
        context = await self._gather_claim_context(claim_text, dossier_id, claim_id)
        dependents = []
        if include_dependents and claim_id:
            dependents = await self._gather_dependents(claim_id)

        evidence_text = "\n".join(
            f"- [{e.get('type', '?')}] {e.get('text', '')[:120]} "
            f"(strength: {e.get('strength', '?')})"
            for e in evidence[:10]
        ) or "No explicit evidence provided"

        context_text = "\n".join(
            f"- {k}: {v}" for k, v in context.items()
        ) if context else "No additional context"

        dependents_text = "\n".join(
            f"- {d.get('text', '')[:100]}" for d in dependents[:5]
        ) or "No dependent claims identified"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STEELMAN_PROMPT.format(
                claim_text=claim_text,
                evidence_text=evidence_text,
                context_text=context_text,
                dependents_text=dependents_text,
            ),
            system=STEELMAN_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = self._parse_json(raw)
        attack = data.get("steelman_attack", data)

        return {
            "claim_text": claim_text,
            "claim_id": claim_id,
            "attack_vectors": attack.get("attack_vectors", []),
            "weakest_link": attack.get("weakest_link", ""),
            "hidden_assumptions": attack.get("hidden_assumptions", []),
            "alternative_explanations": attack.get("alternative_explanations", []),
            "survivability_score": attack.get("survivability_score", 0.5),
            "verdict": attack.get("verdict", "unknown"),
        }

    async def premortem(
        self,
        conclusion: str,
        *,
        dossier_id: str | None = None,
        assumptions: list[str] | None = None,
        decision_id: str | None = None,
    ) -> dict:
        """Run a pre-mortem: assume failure happened, explain why."""
        from app.clients.llm_client import LLMClient

        evidence = await self._gather_evidence_for_claim(conclusion, dossier_id)
        deps = await self._gather_decision_dependencies(decision_id) if decision_id else []

        assumptions_text = "\n".join(
            f"- {a}" for a in (assumptions or [])
        ) or "No explicit assumptions stated (find the hidden ones)"

        evidence_text = "\n".join(
            f"- {e.get('text', '')[:120]}" for e in evidence[:8]
        ) or "Limited evidence base"

        dependencies_text = "\n".join(
            f"- {d}" for d in deps[:5]
        ) or "No explicit dependencies"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PREMORTEM_PROMPT.format(
                conclusion_text=conclusion,
                assumptions_text=assumptions_text,
                evidence_text=evidence_text,
                dependencies_text=dependencies_text,
            ),
            system=PREMORTEM_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = self._parse_json(raw)
        premortem = data.get("premortem", data)

        scenarios = premortem.get("failure_scenarios", [])
        high_prob = [s for s in scenarios if s.get("probability", 0) >= 0.5]

        return {
            "conclusion": conclusion,
            "failure_scenarios": scenarios,
            "high_probability_failures": len(high_prob),
            "blind_spots": premortem.get("blind_spots", []),
            "assumption_graveyard": premortem.get("assumption_graveyard", []),
            "overall_fragility": premortem.get("overall_fragility", 0.5),
            "top_risk": premortem.get("top_risk", ""),
        }

    async def devils_advocate(
        self,
        position: str,
        *,
        supporting_arguments: list[str] | None = None,
        confidence: float = 0.7,
        dossier_id: str | None = None,
    ) -> dict:
        """Argue the opposite position as convincingly as possible."""
        from app.clients.llm_client import LLMClient

        domain_context = await self._gather_domain_context(position, dossier_id)

        support_text = "\n".join(
            f"- {a}" for a in (supporting_arguments or [])
        ) or "No explicit supporting arguments provided"

        domain_text = "\n".join(
            f"- {d}" for d in domain_context[:8]
        ) or "General research domain"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DEVIL_ADVOCATE_PROMPT.format(
                position_text=position,
                support_text=support_text,
                confidence=confidence,
                domain_text=domain_text,
            ),
            system=DEVIL_ADVOCATE_SYSTEM,
            max_tokens=4096,
            temperature=0.5,
        )
        data = self._parse_json(raw)
        case = data.get("devils_case", data)

        return {
            "original_position": position,
            "counter_position": case.get("counter_position", ""),
            "arguments": case.get("arguments", []),
            "strongest_argument": case.get("strongest_argument", ""),
            "crux_of_disagreement": case.get("crux_of_disagreement", ""),
            "experiment_to_settle": case.get("experiment_to_settle", ""),
            "conditions_where_original_wins": case.get("conditions_where_original_wins", []),
            "conditions_where_counter_wins": case.get("conditions_where_counter_wins", []),
        }

    async def assumption_audit(
        self,
        target: str,
        *,
        methodology: str | None = None,
        dossier_id: str | None = None,
    ) -> dict:
        """Excavate all hidden assumptions underlying a conclusion."""
        from app.clients.llm_client import LLMClient

        evidence = await self._gather_evidence_for_claim(target, dossier_id)
        domain_context = await self._gather_domain_context(target, dossier_id)

        methodology_text = methodology or "Not explicitly stated"
        evidence_text = "\n".join(
            f"- {e.get('text', '')[:120]}" for e in evidence[:8]
        ) or "Limited evidence chain"
        domain_text = "\n".join(
            f"- {d}" for d in domain_context[:6]
        ) or "General research domain"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ASSUMPTION_AUDIT_PROMPT.format(
                target_text=target,
                methodology_text=methodology_text,
                evidence_text=evidence_text,
                domain_text=domain_text,
            ),
            system=ASSUMPTION_AUDIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = self._parse_json(raw)
        audit = data.get("assumption_audit", data)

        assumptions = audit.get("assumptions", [])
        load_bearing = [a for a in assumptions if a.get("criticality") == "load_bearing"]
        hidden = [a for a in assumptions if a.get("visibility") == "hidden"]

        return {
            "target": target,
            "assumptions_found": len(assumptions),
            "load_bearing_count": len(load_bearing),
            "hidden_count": len(hidden),
            "assumptions": assumptions,
            "most_dangerous": audit.get("most_dangerous", ""),
            "paradigm_assumptions": audit.get("paradigm_assumptions", []),
            "total_assumption_load": audit.get("total_assumption_load", 0),
            "recommendation": audit.get("recommendation", ""),
        }

    async def stress_test(
        self,
        target: str,
        *,
        assumptions: list[str] | None = None,
        constraints: list[str] | None = None,
        dossier_id: str | None = None,
    ) -> dict:
        """Subject a conclusion to extreme scenarios and find breaking points."""
        from app.clients.llm_client import LLMClient

        assumptions_text = "\n".join(
            f"- {a}" for a in (assumptions or [])
        ) or "Standard operating assumptions"

        constraints_text = "\n".join(
            f"- {c}" for c in (constraints or [])
        ) or "No explicit constraints"

        envelope_text = "Not characterized"
        if dossier_id:
            context = await self._gather_domain_context(target, dossier_id)
            envelope_text = "\n".join(f"- {c}" for c in context[:5]) or "Not characterized"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STRESS_TEST_PROMPT.format(
                target_text=target,
                assumptions_text=assumptions_text,
                constraints_text=constraints_text,
                envelope_text=envelope_text,
            ),
            system=STRESS_TEST_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = self._parse_json(raw)
        test = data.get("stress_test", data)

        scenarios = test.get("scenarios", [])
        catastrophic = [s for s in scenarios if s.get("severity_if_broken") == "catastrophic"]

        return {
            "target": target,
            "scenarios_tested": len(scenarios),
            "catastrophic_failures": len(catastrophic),
            "scenarios": scenarios,
            "breaking_point": test.get("breaking_point", ""),
            "robustness_score": test.get("robustness_score", 0.5),
            "safe_operating_envelope": test.get("safe_operating_envelope", ""),
            "danger_zone": test.get("danger_zone", ""),
        }

    async def full_red_team(
        self,
        claim_text: str,
        *,
        dossier_id: str | None = None,
        claim_id: str | None = None,
    ) -> dict:
        """Run the complete adversarial battery: attack + premortem + assumptions + stress."""
        attack = await self.steelman_attack(
            claim_text, dossier_id=dossier_id, claim_id=claim_id
        )
        premortem_result = await self.premortem(
            claim_text, dossier_id=dossier_id,
            assumptions=attack.get("hidden_assumptions", []),
        )
        audit = await self.assumption_audit(
            claim_text, dossier_id=dossier_id
        )
        stress = await self.stress_test(
            claim_text, dossier_id=dossier_id,
            assumptions=attack.get("hidden_assumptions", []),
        )

        # Composite resilience score
        scores = [
            attack.get("survivability_score", 0.5),
            1.0 - premortem_result.get("overall_fragility", 0.5),
            1.0 - (audit.get("total_assumption_load", 50) / 100.0),
            stress.get("robustness_score", 0.5),
        ]
        resilience = sum(scores) / len(scores)

        return {
            "claim_text": claim_text,
            "resilience_score": round(resilience, 3),
            "verdict": self._resilience_verdict(resilience),
            "steelman_attack": attack,
            "premortem": premortem_result,
            "assumption_audit": audit,
            "stress_test": stress,
            "executive_summary": {
                "survivability": attack.get("survivability_score", 0),
                "fragility": premortem_result.get("overall_fragility", 0),
                "assumption_load": audit.get("total_assumption_load", 0),
                "robustness": stress.get("robustness_score", 0),
                "weakest_link": attack.get("weakest_link", ""),
                "top_risk": premortem_result.get("top_risk", ""),
                "most_dangerous_assumption": audit.get("most_dangerous", ""),
                "breaking_point": stress.get("breaking_point", ""),
            },
        }

    def _resilience_verdict(self, score: float) -> str:
        if score >= 0.8:
            return "battle_hardened"
        elif score >= 0.6:
            return "defensible"
        elif score >= 0.4:
            return "vulnerable"
        elif score >= 0.2:
            return "fragile"
        return "indefensible"

    # --- Private helpers ---

    async def _gather_evidence_for_claim(
        self, claim_text: str, dossier_id: str | None = None, claim_id: str | None = None
    ) -> list[dict]:
        evidence = []
        try:
            from app.services.search.vector_search import VectorSearchService
            search_svc = VectorSearchService()
            results = search_svc.search(query=claim_text[:200], top_k=8)
            for r in results:
                p = r.get("payload", {})
                evidence.append({
                    "text": p.get("text", p.get("title", ""))[:150],
                    "type": p.get("type", "unknown"),
                    "strength": r.get("score", 0.5),
                })
        except Exception as e:
            logger.warning("gather_evidence_failed", error=str(e))
        return evidence

    async def _gather_claim_context(
        self, claim_text: str, dossier_id: str | None, claim_id: str | None
    ) -> dict:
        context = {}
        if claim_id:
            try:
                from app.models.claim_ledger import GlobalClaim
                from sqlalchemy import select
                result = await self.db.execute(
                    select(GlobalClaim).where(GlobalClaim.id == claim_id)
                )
                claim = result.scalar_one_or_none()
                if claim:
                    context["confidence"] = claim.effective_confidence or claim.confidence
                    context["status"] = claim.status
                    context["support_count"] = claim.support_count
                    context["contradict_count"] = claim.contradict_count
                    context["evidence_strength"] = claim.evidence_strength_score
            except Exception:
                pass
        return context

    async def _gather_dependents(self, claim_id: str) -> list[dict]:
        dependents = []
        try:
            from app.models.claim_ledger import ClaimRelation, GlobalClaim
            from sqlalchemy import select
            result = await self.db.execute(
                select(GlobalClaim).join(
                    ClaimRelation, ClaimRelation.target_claim_id == GlobalClaim.id
                ).where(ClaimRelation.source_claim_id == claim_id).limit(5)
            )
            for claim in result.scalars().all():
                dependents.append({"text": claim.canonical_text or "", "id": str(claim.id)})
        except Exception:
            pass
        return dependents

    async def _gather_decision_dependencies(self, decision_id: str) -> list[str]:
        deps = []
        try:
            from app.models.decision_monitor import DecisionMonitor
            from sqlalchemy import select
            result = await self.db.execute(
                select(DecisionMonitor).where(DecisionMonitor.decision_id == decision_id)
            )
            monitor = result.scalar_one_or_none()
            if monitor:
                assumptions = monitor.assumptions or []
                deps = [str(a) for a in assumptions[:5]]
        except Exception:
            pass
        return deps

    async def _gather_domain_context(
        self, text: str, dossier_id: str | None
    ) -> list[str]:
        context = []
        try:
            from app.services.search.vector_search import VectorSearchService
            search_svc = VectorSearchService()
            results = search_svc.search(query=text[:150], top_k=5)
            for r in results:
                p = r.get("payload", {})
                context.append(p.get("text", p.get("title", ""))[:120])
        except Exception:
            pass
        return context

    def _parse_json(self, text: str) -> dict:
        import json
        import re

        if not text:
            return {}
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1).strip()
        if not text.startswith("{"):
            start = text.find("{")
            if start >= 0:
                text = text[start:]
            else:
                return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            end = text.rfind("}")
            if end > 0:
                try:
                    return json.loads(text[: end + 1])
                except json.JSONDecodeError:
                    pass
            # Repair truncated JSON
            repaired = self._repair_json(text)
            if repaired:
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError:
                    pass
            return {}

    def _repair_json(self, text: str) -> str:
        last_comma = text.rfind(',')
        if last_comma > 0:
            text = text[:last_comma]
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        text += ']' * max(0, open_brackets) + '}' * max(0, open_braces)
        return text
