"""PeerReviewSimulatorService — Simulated Academic Peer Review.

Generates realistic peer reviews from multiple reviewer archetypes.
Helps researchers identify weaknesses before submission by simulating
the adversarial review process with different reviewer personalities
and expertise areas.
"""

import uuid
from datetime import datetime, timezone

import structlog

from app.services.llm_utils import parse_llm_json
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REVIEWER_ASSIGN_SYSTEM = """You are an academic journal editor assigning reviewers. Given a research submission, select 3 reviewers with complementary expertise who will provide the most useful critical feedback.

Output JSON with: reviewers (list of id/archetype/name/expertise/known_biases/likely_concerns/harshness 0-1)."""

REVIEWER_ASSIGN_PROMPT = """Submission to review:
Title: {title}
Abstract/Summary: {summary}
Key claims: {claims_text}
Methodology: {methodology}
Domain: {domain}

Assign 3 reviewers. Return ONLY valid JSON."""

REVIEW_SYSTEM = """You are {reviewer_name}, a {reviewer_archetype} reviewer with expertise in {reviewer_expertise}. You have these known biases: {reviewer_biases}.

Write a realistic peer review. Be specific, cite exact weaknesses, suggest concrete improvements. Your harshness level is {harshness}/1.0.

Output JSON with: review.overall_recommendation (accept|minor_revision|major_revision|reject), review.confidence (0-1), review.summary_judgment (2 sentences), review.strengths (list of specific strengths), review.weaknesses (list of specific weaknesses with severity critical/major/minor), review.questions_for_authors (list), review.missing_references (list), review.suggested_experiments (list), review.score (1-10)."""

REVIEW_PROMPT = """Paper under review:
Title: {title}
Summary: {summary}
Claims: {claims_text}
Methodology: {methodology}
Evidence: {evidence_text}

Other reviewers' scores (if available): {other_scores}

Write your review. Return ONLY valid JSON."""

META_REVIEW_SYSTEM = """You are the meta-reviewer (area chair) synthesizing multiple peer reviews into a final decision. Weigh reviewer expertise, identify consensus vs disagreement, and make a fair decision.

Output JSON with: meta_review.decision (accept|minor_revision|major_revision|reject), meta_review.confidence (0-1), meta_review.consensus_strengths (agreed strengths), meta_review.consensus_weaknesses (agreed weaknesses), meta_review.disputed_points (where reviewers disagree and who is right), meta_review.critical_revisions_needed (must-fix items), meta_review.author_response_guidance (what authors should address in rebuttal), meta_review.publication_readiness (0-1)."""

META_REVIEW_PROMPT = """Paper: {title}

Reviews:
{reviews_text}

Synthesize into a meta-review and final decision. Return ONLY valid JSON."""

REBUTTAL_SYSTEM = """You are a research author preparing a rebuttal to peer reviews. Address each concern directly, concisely, and professionally. Acknowledge valid criticisms, explain misunderstandings, and propose concrete revisions.

Output JSON with: rebuttal.addressed_concerns (list of concern/response/revision_proposed), rebuttal.acknowledged_limitations (list), rebuttal.proposed_additional_experiments (list), rebuttal.estimated_revision_time (days), rebuttal.confidence_in_acceptance (0-1)."""

REBUTTAL_PROMPT = """Your paper: {title}
Your claims: {claims_text}

Reviews received:
{reviews_text}

Meta-review decision: {decision}
Critical revisions needed: {critical_revisions}

Write your rebuttal. Return ONLY valid JSON."""


class PeerReviewSimulatorService:
    """Simulated academic peer review process."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assign_reviewers(
        self,
        title: str,
        summary: str,
        *,
        claims: list[str] | None = None,
        methodology: str = "",
        domain: str = "",
    ) -> dict:
        """Assign reviewer panel for a submission."""
        from app.clients.llm_client import LLMClient

        claims_text = "\n".join(f"- {c}" for c in (claims or [])[:8]) or "Not specified"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REVIEWER_ASSIGN_PROMPT.format(
                title=title,
                summary=summary[:300],
                claims_text=claims_text,
                methodology=methodology or "Not specified",
                domain=domain or "Not specified",
            ),
            system=REVIEWER_ASSIGN_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)

        return {
            "title": title,
            "reviewers": data.get("reviewers", []),
        }

    async def run_review(
        self,
        title: str,
        summary: str,
        *,
        claims: list[str] | None = None,
        methodology: str = "",
        evidence: list[str] | None = None,
        domain: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Run full peer review simulation with multiple reviewers."""
        from app.clients.llm_client import LLMClient

        claims_list = claims or []
        if not claims_list and dossier_id:
            claims_list = await self._gather_claims(dossier_id)

        evidence_list = evidence or []
        if not evidence_list:
            evidence_list = await self._gather_evidence(title, dossier_id)

        claims_text = "\n".join(f"- {c}" for c in claims_list[:8]) or "Not specified"
        evidence_text = "\n".join(f"- {e[:100]}" for e in evidence_list[:8]) or "Limited"

        panel = await self.assign_reviewers(
            title, summary, claims=claims_list, methodology=methodology, domain=domain
        )
        reviewers = panel.get("reviewers", [])
        if not reviewers:
            return {"error": "Failed to assign reviewers"}

        llm = LLMClient()
        reviews = []
        for reviewer in reviewers:
            other_scores = ", ".join(
                f"{r.get('reviewer','?')}: {r.get('score','?')}/10"
                for r in reviews
            ) or "You are first to review"

            raw = await llm.complete(
                prompt=REVIEW_PROMPT.format(
                    title=title,
                    summary=summary[:300],
                    claims_text=claims_text,
                    methodology=methodology or "Not described",
                    evidence_text=evidence_text,
                    other_scores=other_scores,
                ),
                system=REVIEW_SYSTEM.format(
                    reviewer_name=reviewer.get("name", "Reviewer"),
                    reviewer_archetype=reviewer.get("archetype", "expert"),
                    reviewer_expertise=reviewer.get("expertise", "general"),
                    reviewer_biases=", ".join(reviewer.get("known_biases", ["none"])),
                    harshness=reviewer.get("harshness", 0.5),
                ),
                max_tokens=4096,
                temperature=0.4,
            )
            review_data = parse_llm_json(raw)
            review = review_data.get("review", review_data)
            review["reviewer"] = reviewer.get("name", "Anonymous")
            review["archetype"] = reviewer.get("archetype", "")
            reviews.append(review)

        # Meta-review
        reviews_text = "\n\n".join(
            f"--- {r.get('reviewer','?')} ({r.get('archetype','')}) ---\n"
            f"Recommendation: {r.get('overall_recommendation','?')}\n"
            f"Score: {r.get('score','?')}/10\n"
            f"Strengths: {'; '.join(str(s)[:50] for s in r.get('strengths',[])[:3])}\n"
            f"Weaknesses: {'; '.join(str(w)[:50] if isinstance(w,str) else w.get('weakness','')[:50] for w in r.get('weaknesses',[])[:3])}"
            for r in reviews
        )

        raw = await llm.complete(
            prompt=META_REVIEW_PROMPT.format(title=title, reviews_text=reviews_text),
            system=META_REVIEW_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        meta_data = parse_llm_json(raw)
        meta = meta_data.get("meta_review", meta_data)

        scores = [r.get("score", 5) for r in reviews if r.get("score")]
        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            "title": title,
            "reviewers": reviewers,
            "reviews": reviews,
            "meta_review": meta,
            "decision": meta.get("decision", "unknown"),
            "average_score": round(avg_score, 1),
            "publication_readiness": meta.get("publication_readiness", 0),
            "critical_revisions": meta.get("critical_revisions_needed", []),
        }

    async def generate_rebuttal(
        self,
        title: str,
        claims: list[str],
        reviews: list[dict],
        decision: str = "",
        critical_revisions: list[str] | None = None,
    ) -> dict:
        """Generate an author rebuttal to peer reviews."""
        from app.clients.llm_client import LLMClient

        claims_text = "\n".join(f"- {c}" for c in claims[:8])
        reviews_text = "\n\n".join(
            f"--- {r.get('reviewer','?')} ---\n"
            f"Recommendation: {r.get('overall_recommendation','?')}\n"
            f"Weaknesses: {'; '.join(str(w)[:60] if isinstance(w,str) else w.get('weakness','')[:60] for w in r.get('weaknesses',[])[:4])}\n"
            f"Questions: {'; '.join(str(q)[:60] for q in r.get('questions_for_authors',[])[:3])}"
            for r in reviews[:3]
        )
        crit_text = "\n".join(f"- {c}" for c in (critical_revisions or [])[:5]) or "None specified"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REBUTTAL_PROMPT.format(
                title=title,
                claims_text=claims_text,
                reviews_text=reviews_text,
                decision=decision or "major_revision",
                critical_revisions=crit_text,
            ),
            system=REBUTTAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        rebuttal = data.get("rebuttal", data)

        return {
            "title": title,
            "addressed_concerns": rebuttal.get("addressed_concerns", []),
            "acknowledged_limitations": rebuttal.get("acknowledged_limitations", []),
            "proposed_experiments": rebuttal.get("proposed_additional_experiments", []),
            "estimated_revision_days": rebuttal.get("estimated_revision_time", 0),
            "confidence_in_acceptance": rebuttal.get("confidence_in_acceptance", 0),
        }

    # --- Private helpers ---

    async def _gather_claims(self, dossier_id: str) -> list[str]:
        claims = []
        try:
            from app.models.dossier import ResearchDossier
            from sqlalchemy import select
            stmt = select(ResearchDossier).where(ResearchDossier.id == dossier_id)
            result = await self.db.execute(stmt)
            dossier = result.scalar_one_or_none()
            if dossier and dossier.claims:
                for c in dossier.claims[:10]:
                    if isinstance(c, dict):
                        claims.append(c.get("text", c.get("claim", str(c)))[:200])
                    else:
                        claims.append(str(c)[:200])
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
