"""ClaimLedgerService — global claim deduplication, linking, and conflict detection."""

import hashlib
import re
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client import models as qmodels

from app.models.claim_ledger import GlobalClaim, ClaimMention, ClaimRelation
from app.services.search.vector_search import VectorSearchService

logger = structlog.get_logger(__name__)

CLAIM_COLLECTION = "claim_embeddings"
CLAIM_VECTOR_DIM = 1024
SIMILARITY_EQUIVALENT = 0.85
SIMILARITY_RELATED = 0.65

MAX_CLAIM_LENGTH = 200
MIN_CLAIM_LENGTH = 25

VAGUE_META_PATTERNS = [
    r"^(this|the) (paper|study|section|chapter|work|article|report) (presents|describes|discusses|examines|explores|reviews|investigates|considers|outlines|summarizes)",
    r"^(in this|in the) (paper|study|section|chapter|work|article)",
    r"^(here|herein),? we (describe|discuss|present|review|outline|summarize)",
    r"^(the following|below|above) (section|table|figure|discussion)",
    r"^(we|the authors) (also|further|additionally) (note|discuss|describe|present)",
    r"^(it is|there is|there are) (important|worth|interesting) to (note|mention|consider)",
    r"^(as (shown|discussed|mentioned|noted|described) (in|above|below|previously))",
]

REJECT_PATTERNS = [
    r"^#{1,6}\s",  # markdown headers
    r"^\*\*[^*]+\*\*$",  # bold-only lines
    r"^\s*[-*]\s",  # bullet points
    r"^\d+\.\s",  # numbered lists
    r"^(table|figure|fig\.|tab\.)\s*\d",  # table/figure references as standalone
]


class ClaimLedgerService:
    """Cross-dossier claim deduplication and conflict detection."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._vs = VectorSearchService()

    def validate_and_atomize(self, text: str) -> list[str]:
        """Gate all claims entering the ledger. Returns list of valid atomic claims."""
        text = text.strip()
        if not text:
            return []

        # Reject markdown formatting
        for pattern in REJECT_PATTERNS:
            if re.match(pattern, text, re.IGNORECASE):
                return []

        # Reject vague meta-statements
        for pattern in VAGUE_META_PATTERNS:
            if re.match(pattern, text.lower()):
                return []

        # Split into sentences if too long
        if len(text) > MAX_CLAIM_LENGTH:
            sentences = re.split(r'(?<=[.!?])\s+', text)
            atoms = []
            for sent in sentences:
                sent = sent.strip()
                if len(sent) < MIN_CLAIM_LENGTH:
                    continue
                if len(sent) > MAX_CLAIM_LENGTH:
                    sent = sent[:MAX_CLAIM_LENGTH].rsplit(" ", 1)[0]
                if self._is_valid_atom(sent):
                    atoms.append(sent)
            return atoms
        else:
            if len(text) < MIN_CLAIM_LENGTH:
                return []
            if self._is_valid_atom(text):
                return [text]
            return []

    def _is_valid_atom(self, text: str) -> bool:
        """Check if a single sentence qualifies as an atomic claim."""
        lower = text.lower()
        for pattern in VAGUE_META_PATTERNS:
            if re.match(pattern, lower):
                return False
        for pattern in REJECT_PATTERNS:
            if re.match(pattern, text, re.IGNORECASE):
                return False
        if not any(c.isalpha() for c in text):
            return False
        # Must contain at least one verb-like word (crude but effective)
        verb_indicators = [
            " is ", " are ", " was ", " were ", " has ", " have ",
            " show", " demonstrate", " improve", " reduce", " increase",
            " achieve", " outperform", " enable", " cause", " lead",
            " affect", " produce", " require", " prevent", " suggest",
        ]
        if not any(v in lower for v in verb_indicators):
            return False
        return True

    def _normalize_claim(self, text: str) -> str:
        """Normalize claim text for hashing and comparison."""
        t = text.lower().strip()
        t = re.sub(r"\s+", " ", t)
        t = re.sub(r"\[[\d,\s]+\]", "", t)  # strip citation brackets
        t = re.sub(r"\([\d,\s]+\)", "", t)
        # strip weak preambles
        for prefix in [
            "we show that ", "we demonstrate that ", "we find that ",
            "our results show that ", "results indicate that ",
            "this paper shows that ", "in this paper, we ",
            "we propose ", "we introduce ",
        ]:
            if t.startswith(prefix):
                t = t[len(prefix):]
                break
        return t.strip()

    def _hash_claim(self, normalized: str) -> str:
        return hashlib.sha256(normalized.encode()).hexdigest()

    async def _embed_claim(self, text: str) -> list[float]:
        return await self._vs.encode_text_async(text)

    async def _ensure_qdrant_collection(self):
        try:
            self._vs.client.get_collection(CLAIM_COLLECTION)
        except Exception:
            self._vs.client.create_collection(
                collection_name=CLAIM_COLLECTION,
                vectors_config=qmodels.VectorParams(
                    size=CLAIM_VECTOR_DIM,
                    distance=qmodels.Distance.COSINE,
                ),
            )

    async def _find_semantic_matches(
        self, embedding: list[float], limit: int = 10
    ) -> list[dict]:
        """Find semantically similar claims in Qdrant."""
        await self._ensure_qdrant_collection()
        try:
            results = self._vs.client.query_points(
                collection_name=CLAIM_COLLECTION,
                query=embedding,
                limit=limit,
            )
            return [
                {"id": str(r.id), "score": r.score, "payload": r.payload}
                for r in results.points
                if r.score >= SIMILARITY_RELATED
            ]
        except Exception as e:
            logger.warning("claim_semantic_search_failed", error=str(e))
            return []

    async def _store_embedding(self, claim_id: str, embedding: list[float], text: str):
        """Store claim embedding in Qdrant."""
        await self._ensure_qdrant_collection()
        self._vs.client.upsert(
            collection_name=CLAIM_COLLECTION,
            points=[
                qmodels.PointStruct(
                    id=claim_id,
                    vector=embedding,
                    payload={"text": text[:500]},
                )
            ],
        )

    async def upsert_claim(
        self,
        text: str,
        *,
        dossier_id: str | None = None,
        paper_id: str | None = None,
        source_tool: str = "unknown",
        stance: str = "unknown",
        verdict: str | None = None,
        confidence: float | None = None,
        evidence: list[dict] | None = None,
        metadata: dict | None = None,
        skip_validation: bool = False,
    ) -> dict:
        """Record a claim into the global ledger, deduplicating and linking.

        All claims pass through validate_and_atomize unless skip_validation=True.
        If the text atomizes into multiple claims, each is upserted separately.
        """
        if not skip_validation:
            atoms = self.validate_and_atomize(text)
            if not atoms:
                return {
                    "global_claim_id": None,
                    "match": "rejected",
                    "reason": "failed validation (too short, vague, or malformed)",
                    "original_text": text[:100],
                }
            if len(atoms) > 1:
                results = []
                for atom in atoms:
                    r = await self._upsert_single_claim(
                        atom,
                        dossier_id=dossier_id,
                        paper_id=paper_id,
                        source_tool=source_tool,
                        stance=stance,
                        verdict=verdict,
                        confidence=confidence,
                        evidence=evidence,
                        metadata=metadata,
                    )
                    results.append(r)
                return {
                    "global_claim_id": results[0]["global_claim_id"],
                    "match": "atomized",
                    "atoms": len(results),
                    "results": results,
                }
            text = atoms[0]

        return await self._upsert_single_claim(
            text,
            dossier_id=dossier_id,
            paper_id=paper_id,
            source_tool=source_tool,
            stance=stance,
            verdict=verdict,
            confidence=confidence,
            evidence=evidence,
            metadata=metadata,
        )

    async def _upsert_single_claim(
        self,
        text: str,
        *,
        dossier_id: str | None = None,
        paper_id: str | None = None,
        source_tool: str = "unknown",
        stance: str = "unknown",
        verdict: str | None = None,
        confidence: float | None = None,
        evidence: list[dict] | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Internal: upsert a single validated claim."""
        normalized = self._normalize_claim(text)
        claim_hash = self._hash_claim(normalized)

        # Step 1: Check exact match
        existing = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.claim_hash == claim_hash)
        )
        global_claim = existing.scalar_one_or_none()

        match_type = "existing"
        if global_claim:
            # Exact match — just add a mention
            pass
        else:
            # Step 2: Semantic match
            embedding = await self._embed_claim(normalized)
            matches = await self._find_semantic_matches(embedding, limit=5)

            equivalent_match = None
            related_matches = []
            for m in matches:
                if m["score"] >= SIMILARITY_EQUIVALENT:
                    equivalent_match = m
                    break
                elif m["score"] >= SIMILARITY_RELATED:
                    related_matches.append(m)

            if equivalent_match:
                # Merge into existing
                result = await self.db.execute(
                    select(GlobalClaim).where(
                        GlobalClaim.id == uuid.UUID(equivalent_match["id"])
                    )
                )
                global_claim = result.scalar_one_or_none()
                match_type = "merged"
            else:
                # Create new global claim
                claim_id = uuid.uuid4()
                global_claim = GlobalClaim(
                    id=claim_id,
                    canonical_text=text,
                    normalized_text=normalized,
                    claim_hash=claim_hash,
                    first_seen_dossier_id=uuid.UUID(dossier_id) if dossier_id else None,
                    first_seen_paper_id=uuid.UUID(paper_id) if paper_id else None,
                    confidence=confidence,
                )
                self.db.add(global_claim)
                await self.db.flush()
                match_type = "new"

                # Store embedding
                await self._store_embedding(str(claim_id), embedding, normalized)

                # Create relations to related claims
                for rm in related_matches[:3]:
                    relation = ClaimRelation(
                        source_claim_id=claim_id,
                        target_claim_id=uuid.UUID(rm["id"]),
                        relation="related",
                        confidence=rm["score"],
                        method="embedding",
                    )
                    self.db.add(relation)

        # Step 3: Add mention
        mention = ClaimMention(
            global_claim_id=global_claim.id,
            dossier_id=uuid.UUID(dossier_id) if dossier_id else None,
            paper_id=uuid.UUID(paper_id) if paper_id else None,
            source_tool=source_tool,
            original_text=text,
            stance=stance,
            verdict=verdict,
            confidence=confidence,
            evidence=evidence or [],
            metadata_json=metadata or {},
        )
        self.db.add(mention)

        # Step 4: Update counters
        if stance in ("supports", "supported"):
            global_claim.support_count = (global_claim.support_count or 0) + 1
        elif stance in ("contradicts", "refuted"):
            global_claim.contradict_count = (global_claim.contradict_count or 0) + 1
            if (global_claim.contradict_count or 0) > 0:
                global_claim.status = "disputed"
        elif stance in ("qualifies", "mixed"):
            global_claim.qualify_count = (global_claim.qualify_count or 0) + 1

        # Step 5: Auto-score evidence strength
        try:
            from app.services.evidence_strength_service import EvidenceStrengthService
            scorer = EvidenceStrengthService(self.db)
            context_parts = []
            if evidence:
                for ev in evidence:
                    if isinstance(ev, dict):
                        context_parts.append(ev.get("text", ""))
                    elif isinstance(ev, str):
                        context_parts.append(ev)
            breakdown = scorer.score_text(text, " ".join(context_parts))
            mention.strength_score = breakdown["total"]
            mention.strength_breakdown = breakdown

            # Update global claim aggregate
            support_weight = mention.strength_score if stance in ("supports", "supported") else 0
            contradict_weight = mention.strength_score if stance in ("contradicts", "refuted") else 0
            if support_weight > 0:
                prev = global_claim.weighted_support or 0
                count = global_claim.support_count or 1
                global_claim.weighted_support = round(
                    ((prev * (count - 1)) + support_weight) / count, 1
                )
            if contradict_weight > 0:
                prev = global_claim.weighted_contradict or 0
                count = global_claim.contradict_count or 1
                global_claim.weighted_contradict = round(
                    ((prev * (count - 1)) + contradict_weight) / count, 1
                )
            if mention.strength_score > (global_claim.evidence_strength_score or 0):
                global_claim.evidence_strength_score = mention.strength_score
        except Exception as e:
            logger.warning("evidence_scoring_failed", error=str(e)[:100])

        await self.db.commit()

        return {
            "global_claim_id": str(global_claim.id),
            "match": match_type,
            "canonical_text": global_claim.canonical_text,
            "support_count": global_claim.support_count,
            "contradict_count": global_claim.contradict_count,
            "qualify_count": global_claim.qualify_count,
            "status": global_claim.status,
            "evidence_strength": mention.strength_score,
        }

    async def search_claims(
        self,
        query: str,
        *,
        dossier_id: str | None = None,
        include_cross_dossier: bool = True,
        limit: int = 10,
    ) -> dict:
        """Search the global claim ledger semantically."""
        embedding = await self._embed_claim(query)
        matches = await self._find_semantic_matches(embedding, limit=limit)

        if not matches:
            return {"claims": [], "total": 0}

        claim_ids = [uuid.UUID(m["id"]) for m in matches]
        score_map = {m["id"]: m["score"] for m in matches}

        result = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.id.in_(claim_ids))
        )
        claims = result.scalars().all()

        output = []
        for claim in claims:
            # Get mention count per dossier
            mention_q = select(
                ClaimMention.dossier_id,
                func.count(ClaimMention.id).label("cnt"),
            ).where(
                ClaimMention.global_claim_id == claim.id
            ).group_by(ClaimMention.dossier_id)
            mention_result = await self.db.execute(mention_q)
            dossier_mentions = {
                str(row[0]): row[1] for row in mention_result.all() if row[0]
            }

            # Filter if dossier-specific and not cross-dossier
            if dossier_id and not include_cross_dossier:
                if dossier_id not in dossier_mentions:
                    continue

            output.append({
                "global_claim_id": str(claim.id),
                "canonical_text": claim.canonical_text,
                "similarity": score_map.get(str(claim.id), 0),
                "support_count": claim.support_count,
                "contradict_count": claim.contradict_count,
                "qualify_count": claim.qualify_count,
                "status": claim.status,
                "dossier_mentions": dossier_mentions,
                "total_mentions": sum(dossier_mentions.values()),
            })

        output.sort(key=lambda x: x["similarity"], reverse=True)
        return {"claims": output[:limit], "total": len(output)}

    async def detect_conflicts(
        self,
        claim_text: str,
        *,
        dossier_id: str | None = None,
        limit: int = 10,
    ) -> dict:
        """Find claims that potentially contradict the given claim."""
        embedding = await self._embed_claim(claim_text)
        matches = await self._find_semantic_matches(embedding, limit=20)

        if not matches:
            return {"conflicts": [], "total": 0}

        claim_ids = [uuid.UUID(m["id"]) for m in matches]
        score_map = {m["id"]: m["score"] for m in matches}
        result = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.id.in_(claim_ids))
        )
        candidates = result.scalars().all()

        # Use negation heuristic + LLM for classification
        negation_markers = [
            "not ", "no ", "don't ", "doesn't ", "cannot ", "fails to ",
            "unable to ", "insufficient ", "limited ", "negligible ",
            "does not ", "do not ", "without ", "lack of ",
        ]
        claim_lower = claim_text.lower()
        claim_has_negation = any(n in claim_lower for n in negation_markers)

        conflicts = []
        from app.clients.llm_client import LLMClient, DEFAULT_CHAT_MODEL

        llm = LLMClient()
        for candidate in candidates[:8]:
            if candidate.canonical_text.strip() == claim_text.strip():
                continue

            cand_lower = candidate.canonical_text.lower()
            cand_has_negation = any(n in cand_lower for n in negation_markers)
            sim = score_map.get(str(candidate.id), 0)

            # Heuristic: high similarity + opposite negation = likely contradiction
            relation = None
            if sim > 0.70 and claim_has_negation != cand_has_negation:
                relation = "contradicts"
            elif sim > 0.80 and candidate.status == "disputed":
                relation = "qualifies"
            else:
                # Try LLM classification for borderline cases
                prompt = (
                    f"I have two research claims:\n"
                    f"1. {claim_text}\n"
                    f"2. {candidate.canonical_text}\n\n"
                    f"Do these claims agree with each other, or do they disagree? "
                    f"Return a JSON object: {{\"relation\": \"agrees\" or \"disagrees\" or \"partially\"}}"
                )
                try:
                    raw = await llm.complete(
                        prompt=prompt,
                        model=DEFAULT_CHAT_MODEL,
                        max_tokens=50,
                        temperature=0.1,
                    )
                    if "disagree" in raw.lower():
                        relation = "contradicts"
                    elif "partial" in raw.lower():
                        relation = "qualifies"
                except Exception:
                    pass

            if relation in ("contradicts", "qualifies"):
                conflicts.append({
                    "global_claim_id": str(candidate.id),
                    "text": candidate.canonical_text,
                    "relation": relation,
                    "similarity": sim,
                    "support_count": candidate.support_count,
                    "contradict_count": candidate.contradict_count,
                    "status": candidate.status,
                })

                # Record the relation in DB
                normalized = self._normalize_claim(claim_text)
                claim_hash = self._hash_claim(normalized)
                source_q = await self.db.execute(
                    select(GlobalClaim).where(GlobalClaim.claim_hash == claim_hash)
                )
                source = source_q.scalar_one_or_none()
                if source:
                    existing_rel = await self.db.execute(
                        select(ClaimRelation).where(
                            ClaimRelation.source_claim_id == source.id,
                            ClaimRelation.target_claim_id == candidate.id,
                            ClaimRelation.relation == relation,
                        )
                    )
                    if not existing_rel.scalar_one_or_none():
                        new_rel = ClaimRelation(
                            source_claim_id=source.id,
                            target_claim_id=candidate.id,
                            relation=relation,
                            confidence=sim,
                            method="heuristic",
                            rationale=f"Negation asymmetry detected" if claim_has_negation != cand_has_negation else "LLM classified",
                        )
                        self.db.add(new_rel)
                        if relation == "contradicts":
                            candidate.contradict_count = (candidate.contradict_count or 0) + 1
                            candidate.status = "disputed"

        await llm.close()
        await self.db.commit()

        return {
            "conflicts": conflicts[:limit],
            "total": len(conflicts),
            "query_claim": claim_text,
        }

    async def get_claim_graph(
        self,
        dossier_id: str,
        *,
        depth: int = 1,
        include_external: bool = True,
    ) -> dict:
        """Get the claim graph for a dossier with cross-dossier connections."""
        # Get all claims mentioned in this dossier
        mentions_q = await self.db.execute(
            select(ClaimMention).where(
                ClaimMention.dossier_id == uuid.UUID(dossier_id)
            )
        )
        mentions = mentions_q.scalars().all()

        if not mentions:
            return {"nodes": [], "edges": [], "cross_dossier_claims": []}

        claim_ids = list(set(m.global_claim_id for m in mentions))

        # Get global claims
        claims_q = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.id.in_(claim_ids))
        )
        claims = claims_q.scalars().all()

        nodes = []
        for c in claims:
            nodes.append({
                "id": str(c.id),
                "text": c.canonical_text,
                "status": c.status,
                "support_count": c.support_count,
                "contradict_count": c.contradict_count,
            })

        # Get relations between these claims
        relations_q = await self.db.execute(
            select(ClaimRelation).where(
                (ClaimRelation.source_claim_id.in_(claim_ids)) |
                (ClaimRelation.target_claim_id.in_(claim_ids))
            )
        )
        relations = relations_q.scalars().all()

        edges = []
        external_claim_ids = set()
        for r in relations:
            edges.append({
                "source": str(r.source_claim_id),
                "target": str(r.target_claim_id),
                "relation": r.relation,
                "confidence": r.confidence,
            })
            if r.target_claim_id not in claim_ids:
                external_claim_ids.add(r.target_claim_id)
            if r.source_claim_id not in claim_ids:
                external_claim_ids.add(r.source_claim_id)

        # Get cross-dossier mentions for these claims
        cross_dossier = []
        if include_external:
            cross_q = await self.db.execute(
                select(
                    ClaimMention.global_claim_id,
                    ClaimMention.dossier_id,
                    func.count(ClaimMention.id).label("cnt"),
                ).where(
                    ClaimMention.global_claim_id.in_(claim_ids),
                    ClaimMention.dossier_id != uuid.UUID(dossier_id),
                ).group_by(
                    ClaimMention.global_claim_id,
                    ClaimMention.dossier_id,
                )
            )
            for row in cross_q.all():
                cross_dossier.append({
                    "claim_id": str(row[0]),
                    "dossier_id": str(row[1]),
                    "mention_count": row[2],
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "cross_dossier_claims": cross_dossier,
        }

    async def backfill_claims(self) -> dict:
        """Re-validate all existing claims. Remove or re-atomize invalid ones."""
        result = await self.db.execute(select(GlobalClaim))
        all_claims = result.scalars().all()

        removed = []
        kept = []
        re_atomized = []

        for claim in all_claims:
            atoms = self.validate_and_atomize(claim.canonical_text)
            if not atoms:
                removed.append({
                    "id": str(claim.id),
                    "text": claim.canonical_text[:80],
                    "reason": "failed validation",
                })
                await self.db.execute(
                    update(GlobalClaim)
                    .where(GlobalClaim.id == claim.id)
                    .values(status="rejected")
                )
            elif len(atoms) == 1 and atoms[0] == claim.canonical_text:
                kept.append(str(claim.id))
            else:
                re_atomized.append({
                    "id": str(claim.id),
                    "original": claim.canonical_text[:80],
                    "atoms": atoms,
                })
                await self.db.execute(
                    update(GlobalClaim)
                    .where(GlobalClaim.id == claim.id)
                    .values(canonical_text=atoms[0], status="active")
                )

        await self.db.commit()

        return {
            "total_reviewed": len(all_claims),
            "kept": len(kept),
            "removed": len(removed),
            "re_atomized": len(re_atomized),
            "removed_claims": removed[:20],
            "re_atomized_claims": re_atomized[:10],
        }
