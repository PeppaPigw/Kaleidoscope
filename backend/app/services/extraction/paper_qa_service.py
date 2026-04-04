"""Paper QA service — embed recall → rerank → LLM answer.

Design principles:
- Low-latency: no multi-step LLM intermediate processing
- Grounded: answers cite retrieved passage numbers
- Idempotent: prepare() can be called multiple times safely
"""

from __future__ import annotations

import json as _json
import re
import time

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.llm_client import LLMClient
from app.config import settings
from app.models.paper_qa import PaperChunk, PaperEmbeddingJob
from app.services.extraction.prompts import (
    PAPER_QA_PROMPT,
    PAPER_QA_RETRY_PROMPT,
    PAPER_QA_SYSTEM,
)

logger = structlog.get_logger(__name__)

SECTION_CITATION_RE = re.compile(r"\[([^\[\]]+)\](?!\()")
SECTION_NUMBER_PREFIX_RE = re.compile(
    r"^(?:section\s+)?\d+(?:\.\d+)*(?:[:.)-]\s*|\s+)", re.IGNORECASE
)
SECTION_PAREN_RE = re.compile(r"\s*\([^)]*\)")
REFUSAL_MARKERS = (
    "as an ai",
    "i cannot answer",
    "i can't answer",
    "i cannot provide",
    "i can't provide",
    "i must refuse",
    "legal and ethical",
    "law and ethics",
    "不予回答",
    "不能提供答案",
    "不能就您提出的问题进行回答",
    "法律和伦理",
    "法律或道德",
    "作为ai",
    "作为一个ai",
    "作为人工智能",
    "恪守法律和伦理的界限",
    "恪守法律与道德的界线",
    "违反法律或不符合道德规范",
    "有责任感的ai机器人",
    "不予以回答",
)
NOT_COVERED_MARKERS = (
    "this information is not explicitly covered in the retrieved passages",
    "i cannot find this information in the provided passages",
    "not in the retrieved passages",
    "not covered in the retrieved passages",
    "未在检索到的段落中明确提及",
)
NUMERIC_CITATION_RE = re.compile(r"\[(\d+)\]")
QUESTION_REWRITE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"^[A-Z][A-Za-z0-9_-]{0,7}\s*(?:主要解决的问题|解决的主要问题|主要解决什么问题|解决什么问题|主要做什么)\??$",
            re.IGNORECASE,
        ),
        "这篇论文主要解决的问题",
    ),
    (
        re.compile(r"\blimitation section\b", re.IGNORECASE),
        "discussion of trade-offs or caveats",
    ),
    (re.compile(r"\blimitations?\b", re.IGNORECASE), "trade-offs or caveats"),
    (
        re.compile(
            r"(?:局限性|局限|限制|不足)(?:\s*(?:和|及|与|、|/)\s*(?:局限性|局限|限制|不足))+"
        ),
        "权衡或注意事项",
    ),
    (re.compile(r"局限性|局限|限制|不足"), "权衡或注意事项"),
)
CONTEXT_DEPENDENT_QUESTION_RE = re.compile(
    r"\b(it|its|they|them|this|that|these|those|he|she|former|latter|compare|comparison|same|above|previous|earlier)\b|"
    r"(它|其|这个|那个|这些|那些|上面|前面|刚才|之前|前述|上述|继续|展开|进一步|比较一下|相比之下)",
    re.IGNORECASE,
)


class PaperQAService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.llm = LLMClient()

    # ── Status ────────────────────────────────────────────────────────────────

    async def get_status(self, paper_id: str) -> dict:
        """Return embedding status for a paper."""
        result = await self.db.execute(
            select(PaperEmbeddingJob).where(PaperEmbeddingJob.paper_id == paper_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            return {"status": "not_started", "chunk_count": 0}
        return {
            "status": job.status,
            "chunk_count": job.chunk_count or 0,
            "error_message": job.error_message,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        }

    # ── Prepare ───────────────────────────────────────────────────────────────

    async def prepare(self, paper_id: str) -> dict:
        """Create or reprioritize the embedding job for a paper."""
        from app.tasks.embedding_tasks import process_paper_embedding

        result = await self.db.execute(
            select(PaperEmbeddingJob).where(PaperEmbeddingJob.paper_id == paper_id)
        )
        job = result.scalar_one_or_none()

        if job and job.status == "completed":
            return {"status": "already_complete", "chunk_count": job.chunk_count}

        if job and job.status in ("pending", "running"):
            # Bump priority
            job.priority = 10
            await self.db.flush()
            return {"status": job.status}

        if job and job.status == "failed":
            job.status = "pending"
            job.priority = 10
            job.error_message = None
            await self.db.flush()
        else:
            job = PaperEmbeddingJob(paper_id=paper_id, status="pending", priority=10)
            self.db.add(job)
            await self.db.flush()

        process_paper_embedding.apply_async(
            args=[paper_id],
            kwargs={"priority": 10},
            priority=10,
        )
        logger.info("paper_embedding_queued", paper_id=paper_id)
        return {"status": "queued"}

    # ── Ask ───────────────────────────────────────────────────────────────────

    async def ask(
        self,
        paper_id: str,
        question: str,
        history: list[dict[str, str]] | None = None,
        context_snippet: str | None = None,
    ) -> dict:
        """Full RAG QA: embed question → recall → rerank → LLM answer."""
        start = time.monotonic()
        top_k = settings.paper_qa_embed_recall_top_k
        top_n = settings.paper_qa_rerank_top_n
        answer_model = settings.paper_qa_answer_model or settings.llm_model
        model_question = _sanitize_question_for_model(question)

        # 1. Embed question
        q_embeddings = await self.llm.embed([model_question])
        q_vec = q_embeddings[0]

        # 2. Load chunks with embeddings (exclude references)
        result = await self.db.execute(
            select(PaperChunk)
            .where(PaperChunk.paper_id == paper_id)
            .where(PaperChunk.embedding.isnot(None))
            .where(PaperChunk.is_references == False)  # noqa: E712
            .order_by(PaperChunk.order_index)
        )
        chunks = list(result.scalars().all())

        if not chunks:
            return {
                "answer": "Paper index not ready yet. Please wait for embedding to complete.",
                "sources": [],
                "latency_ms": 0,
            }

        # 3. Cosine similarity recall
        scored = _cosine_recall(q_vec, chunks, top_k)

        # 4. Rerank
        candidate_texts = [c.content for _, c in scored]
        try:
            reranked = await self.llm.rerank(
                query=model_question,
                documents=candidate_texts,
                top_n=top_n,
            )
        except Exception as e:
            logger.warning("rerank_failed_fallback", error=str(e))
            # Fallback: use cosine order
            reranked = [
                {"index": i, "relevance_score": score}
                for i, (score, _) in enumerate(scored[:top_n])
            ]

        # 5. Build context from top reranked chunks
        context_chunks = []
        for item in reranked[:top_n]:
            idx = item.get("index", 0)
            if 0 <= idx < len(scored):
                context_chunks.append((item.get("relevance_score", 0), scored[idx][1]))

        if not context_chunks:
            context_chunks = [(s, c) for s, c in scored[:top_n]]

        def build_context(
            selected_chunks: list[tuple[float | None, PaperChunk]],
        ) -> str:
            return "\n\n".join(
                f"[{i + 1}] (Section: {c.section_title})\n{c.content}"
                for i, (_, c) in enumerate(selected_chunks)
            )

        def build_sources(
            selected_chunks: list[tuple[float | None, PaperChunk]],
        ) -> list[dict]:
            return [
                {
                    "section_title": c.section_title,
                    "normalized_section": c.normalized_section_title,
                    "text_snippet": c.content[:300]
                    + ("..." if len(c.content) > 300 else ""),
                    "score": round(score, 3) if score is not None else None,
                }
                for score, c in selected_chunks
            ]

        async def complete_with_prompt(prompt: str) -> str:
            return await self.llm.complete(
                prompt=prompt,
                system=PAPER_QA_SYSTEM,
                model=answer_model,
                max_tokens=5000,
                temperature=0.0,
            )

        # 6. LLM answer
        history_str = (
            _format_chat_history(history or [])
            if _question_requires_history(question)
            else "(none)"
        )
        context_str = build_context(context_chunks)
        snippet_header = _build_snippet_header(context_snippet)
        prompt = PAPER_QA_PROMPT.format(
            question=model_question,
            context=context_str,
            history=history_str,
            snippet_header=snippet_header,
        )
        answer_text = await complete_with_prompt(prompt)
        sources = build_sources(context_chunks)

        if _needs_full_context_fallback(answer_text):
            logger.info(
                "paper_qa_full_context_fallback",
                paper_id=paper_id,
                question=question[:160],
                reason=(
                    "refusal"
                    if _looks_like_refusal(answer_text)
                    else "insufficient_support"
                ),
            )
            context_chunks = [(1.0, chunk) for chunk in chunks]
            context_str = build_context(context_chunks)
            sources = build_sources(context_chunks)
            fallback_prompt = (
                PAPER_QA_RETRY_PROMPT.format(
                    history=history_str,
                    reframed_question=model_question,
                    context=context_str,
                    validation_errors="The previous answer was a refusal or policy-based refusal.",
                    previous_answer=answer_text,
                )
                if _looks_like_refusal(answer_text)
                else PAPER_QA_PROMPT.format(
                    question=model_question,
                    context=context_str,
                    history=history_str,
                    snippet_header=snippet_header,
                )
            )
            answer_text = await complete_with_prompt(fallback_prompt)

        if _looks_like_refusal(answer_text) or _looks_like_not_covered(answer_text):
            logger.warning(
                "paper_qa_refusal_retry",
                paper_id=paper_id,
                question=question[:160],
            )
            retry_prompt = PAPER_QA_RETRY_PROMPT.format(
                context=context_str,
                history=history_str,
                reframed_question=model_question,
                validation_errors="The previous answer incorrectly stated the information was not covered, or it was a refusal.",
                previous_answer=answer_text,
            )
            answer_text = await complete_with_prompt(retry_prompt)

        answer_text = _normalize_source_citations(answer_text, sources)
        answer_text, sources = _compact_sources_to_citations(answer_text, sources)

        latency_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "paper_qa_answered",
            paper_id=paper_id,
            latency_ms=latency_ms,
            chunks_used=len(context_chunks),
        )
        return {
            "answer": answer_text,
            "sources": sources,
            "model": answer_model,
            "latency_ms": latency_ms,
        }

    async def ask_stream(
        self,
        paper_id: str,
        question: str,
        history: list[dict[str, str]] | None = None,
        context_snippet: str | None = None,
    ):
        """Streaming RAG QA: embed → recall → rerank → stream LLM answer as SSE."""
        top_k = settings.paper_qa_embed_recall_top_k
        top_n = settings.paper_qa_rerank_top_n
        answer_model = settings.paper_qa_answer_model or settings.llm_model
        model_question = _sanitize_question_for_model(question)

        # 1. Embed question
        q_embeddings = await self.llm.embed([model_question])
        q_vec = q_embeddings[0]

        # 2. Load chunks
        result = await self.db.execute(
            select(PaperChunk)
            .where(PaperChunk.paper_id == paper_id)
            .where(PaperChunk.embedding.isnot(None))
            .where(PaperChunk.is_references == False)  # noqa: E712
            .order_by(PaperChunk.order_index)
        )
        chunks = list(result.scalars().all())

        if not chunks:
            yield f'data: {_json.dumps({"type": "chunk", "content": "Paper index not ready."})}\n\n'
            yield 'data: {"type":"done"}\n\n'
            return

        # 3. Cosine recall
        scored = _cosine_recall(q_vec, chunks, top_k)

        # 4. Rerank
        candidate_texts = [c.content for _, c in scored]
        try:
            reranked = await self.llm.rerank(
                query=model_question,
                documents=candidate_texts,
                top_n=top_n,
            )
        except Exception as e:
            logger.warning("rerank_failed_fallback_stream", error=str(e))
            reranked = [
                {"index": i, "relevance_score": score}
                for i, (score, _) in enumerate(scored[:top_n])
            ]

        # 5. Build context
        context_chunks: list[tuple[float, PaperChunk]] = []
        for item in reranked[:top_n]:
            idx = item.get("index", 0)
            if 0 <= idx < len(scored):
                context_chunks.append((item.get("relevance_score", 0), scored[idx][1]))
        if not context_chunks:
            context_chunks = [(s, c) for s, c in scored[:top_n]]

        context_str = "\n\n".join(
            f"[{i + 1}] (Section: {c.section_title})\n{c.content}"
            for i, (_, c) in enumerate(context_chunks)
        )
        sources = [
            {
                "section_title": c.section_title,
                "normalized_section": c.normalized_section_title,
                "text_snippet": c.content[:300]
                + ("..." if len(c.content) > 300 else ""),
                "score": round(score, 3) if score is not None else None,
            }
            for score, c in context_chunks
        ]

        history_str = (
            _format_chat_history(history or [])
            if _question_requires_history(question)
            else "(none)"
        )
        snippet_header = _build_snippet_header(context_snippet)
        prompt = PAPER_QA_PROMPT.format(
            question=model_question,
            context=context_str,
            history=history_str,
            snippet_header=snippet_header,
        )

        # 6. Stream LLM
        try:
            async for chunk in self.llm.stream_complete(
                prompt=prompt,
                system=PAPER_QA_SYSTEM,
                model=answer_model,
                max_tokens=3000,
                temperature=0.0,
            ):
                yield f'data: {_json.dumps({"type": "chunk", "content": chunk})}\n\n'
        except Exception as e:
            logger.error("paper_qa_stream_error", paper_id=paper_id, error=str(e))
            yield f'data: {_json.dumps({"type": "error", "message": str(e)})}\n\n'
            yield 'data: {"type":"done"}\n\n'
            return

        # 7. Send sources
        yield f'data: {_json.dumps({"type": "sources", "sources": sources})}\n\n'
        yield 'data: {"type":"done"}\n\n'


# ── Helpers ──────────────────────────────────────────────────────────────────


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Fast pure-Python cosine similarity (avoids numpy import for small vectors)."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    return dot / (norm_a * norm_b)


def _cosine_recall(
    q_vec: list[float],
    chunks: list[PaperChunk],
    top_k: int,
) -> list[tuple[float, PaperChunk]]:
    """Score all chunks by cosine similarity and return top_k."""
    scored: list[tuple[float, PaperChunk]] = []
    for chunk in chunks:
        if not chunk.embedding:
            continue
        sim = _cosine_similarity(q_vec, chunk.embedding)
        # Penalty for appendix sections
        if chunk.is_appendix:
            sim *= 0.8
        scored.append((sim, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]


def _format_chat_history(history: list[dict[str, str]]) -> str:
    """Format recent conversation turns for follow-up resolution."""
    turns: list[str] = []
    turn_index = 0
    for turn in history[-6:]:
        question = (turn.get("question") or "").strip()
        answer = _sanitize_history_answer((turn.get("answer") or "").strip())
        if not question or not answer:
            continue
        turn_index += 1
        turns.append(
            f"Turn {turn_index} User: {question}\nTurn {turn_index} Assistant: {answer}"
        )
    return "\n\n".join(turns) if turns else "(none)"


def _sanitize_history_answer(answer: str) -> str:
    """Strip inline citations from prior answers so old source ids don't leak into follow-up turns."""
    cleaned = SECTION_CITATION_RE.sub("", answer)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def _looks_like_refusal(answer: str) -> bool:
    """Detect generic provider refusals so we can retry with a stricter prompt."""
    normalized = " ".join(answer.strip().lower().split())
    if not normalized:
        return True
    return any(marker in normalized for marker in REFUSAL_MARKERS)


def _needs_full_context_fallback(answer: str) -> bool:
    """Retry with all non-reference chunks when reranked context is clearly insufficient."""
    normalized = " ".join(answer.strip().lower().split())
    if not normalized:
        return True
    if _looks_like_refusal(answer):
        return True
    return _looks_like_not_covered(answer)


def _looks_like_not_covered(answer: str) -> bool:
    """Detect overly conservative 'not covered' answers so we can retry on the full paper context."""
    normalized = " ".join(answer.strip().lower().split())
    if not normalized:
        return True
    return any(marker in normalized for marker in NOT_COVERED_MARKERS)


def _normalize_section_alias(value: str) -> str:
    """Normalize section labels so bracket citations can be mapped to numeric source ids."""
    normalized = value.strip().lower().strip("[]")
    normalized = SECTION_PAREN_RE.sub("", normalized)
    normalized = SECTION_NUMBER_PREFIX_RE.sub("", normalized)
    normalized = re.sub(r"\bpart\s+\d+\b", "", normalized)
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip(" .:-")


def _citation_aliases(source: dict) -> set[str]:
    section_title = str(source.get("section_title") or "")
    normalized_section = str(source.get("normalized_section") or "")
    aliases = {
        _normalize_section_alias(section_title),
        _normalize_section_alias(normalized_section),
    }
    aliases = {alias for alias in aliases if alias}

    if section_title:
        aliases.add(_normalize_section_alias(section_title.split(":", 1)[-1]))

    return {alias for alias in aliases if alias}


def _normalize_source_citations(answer: str, sources: list[dict]) -> str:
    """Convert section-name citations like [Introduction] into [1][2] form."""
    alias_to_index: dict[str, int] = {}
    for index, source in enumerate(sources, start=1):
        for alias in _citation_aliases(source):
            alias_to_index.setdefault(alias, index)

    def replace(match: re.Match[str]) -> str:
        raw = match.group(1).strip()
        if not raw or raw.lower() in {"x", " ", "-"}:
            return match.group(0)

        pieces = [
            piece.strip() for piece in re.split(r",|;|/|\band\b", raw) if piece.strip()
        ]
        if not pieces:
            return match.group(0)

        indices: list[int] = []
        for piece in pieces:
            if piece.isdigit():
                index = int(piece)
            else:
                index = alias_to_index.get(_normalize_section_alias(piece))
            if index is None:
                return match.group(0)
            if index not in indices:
                indices.append(index)

        return "".join(f"[{index}]" for index in indices)

    return SECTION_CITATION_RE.sub(replace, answer)


def _compact_sources_to_citations(
    answer: str, sources: list[dict]
) -> tuple[str, list[dict]]:
    """Keep only sources cited in the answer and renumber citations to match visible source order."""
    citation_order: list[int] = []
    for match in NUMERIC_CITATION_RE.finditer(answer):
        index = int(match.group(1))
        if 1 <= index <= len(sources) and index not in citation_order:
            citation_order.append(index)

    if not citation_order:
        return answer, sources

    index_map = {
        old_index: new_index
        for new_index, old_index in enumerate(citation_order, start=1)
    }
    compacted_sources = [sources[index - 1] for index in citation_order]

    def replace(match: re.Match[str]) -> str:
        old_index = int(match.group(1))
        new_index = index_map.get(old_index)
        if new_index is None:
            return match.group(0)
        return f"[{new_index}]"

    compacted_answer = NUMERIC_CITATION_RE.sub(replace, answer)
    return compacted_answer, compacted_sources


def _sanitize_question_for_model(question: str) -> str:
    """Rephrase questions that trigger provider refusals into neutral paper-analysis language."""
    rewritten = question.strip()
    for pattern, replacement in QUESTION_REWRITE_PATTERNS:
        rewritten = pattern.sub(replacement, rewritten)

    rewritten = re.sub(
        r"(权衡或注意事项)(?:\s*(?:和|及|与|、|/)\s*\1)+",
        r"\1",
        rewritten,
    )
    rewritten = re.sub(r"\s{2,}", " ", rewritten)
    return rewritten


def _question_requires_history(question: str) -> bool:
    """Only include chat history for clearly context-dependent follow-up questions."""
    normalized = question.strip()
    if not normalized:
        return False
    return bool(CONTEXT_DEPENDENT_QUESTION_RE.search(normalized))


def _build_snippet_header(context_snippet: str | None) -> str:
    """Format the highlighted-passage block for inclusion in the prompt, or empty string."""
    if not context_snippet or not context_snippet.strip():
        return ""
    truncated = context_snippet.strip()[:800]
    return (
        f"The user has highlighted the following passage from the paper as context for their question:\n\n"
        f'> {truncated}\n\n'
        f"Keep this passage in mind when answering, but still ground your answer in the retrieved passages below.\n\n"
    )
