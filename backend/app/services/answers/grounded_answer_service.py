"""Grounded answer synthesis from supplied evidence packs."""

from __future__ import annotations

import re
from typing import Any, Literal

AnswerStyle = Literal["concise", "detailed"]


class GroundedAnswerService:
    """Build cited non-streaming JSON answers from already-retrieved evidence."""

    def build_answer(
        self,
        question: str,
        evidence_pack: dict[str, Any] | None = None,
        evidence: list[dict[str, Any]] | None = None,
        style: AnswerStyle = "concise",
        max_sources: int = 8,
        max_answer_chars: int = 4000,
    ) -> dict[str, Any]:
        """Return a cited answer and grounding diagnostics."""
        sources = self._normalize_sources(evidence_pack, evidence or [], max_sources)
        if not sources:
            return {
                "answer": "This cannot be answered from the provided evidence.",
                "citations": [],
                "diagnostics": {
                    "grounded": False,
                    "grounding_score": 0.0,
                    "source_count": 0,
                    "cited_source_count": 0,
                    "answer_sentence_count": 1,
                    "unsupported_sentence_count": 1,
                },
                "warnings": ["No evidence sources were provided."],
            }

        answer = self._compose_answer(question, sources, style, max_answer_chars)
        citations = [self._citation_for_source(source) for source in sources]
        diagnostics = self._diagnostics(answer, sources)
        return {
            "answer": answer,
            "citations": citations,
            "diagnostics": diagnostics,
            "warnings": [],
        }

    def _normalize_sources(
        self,
        evidence_pack: dict[str, Any] | None,
        evidence: list[dict[str, Any]],
        max_sources: int,
    ) -> list[dict[str, Any]]:
        raw_sources: list[dict[str, Any]] = []
        if evidence:
            raw_sources.extend(evidence)
        if evidence_pack:
            for key in ("evidence", "chunks", "sources"):
                values = evidence_pack.get(key)
                if isinstance(values, list):
                    raw_sources.extend(item for item in values if isinstance(item, dict))

        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for index, source in enumerate(raw_sources, 1):
            content = str(
                source.get("content")
                or source.get("text")
                or source.get("snippet")
                or ""
            ).strip()
            if not content:
                continue
            source_id = str(source.get("id") or source.get("chunk_id") or index)
            if source_id in seen:
                continue
            seen.add(source_id)
            normalized.append(
                {
                    "id": source_id,
                    "anchor": str(source.get("citation_key") or f"E{len(normalized) + 1}"),
                    "paper_id": source.get("paper_id"),
                    "paper_title": source.get("paper_title") or source.get("title"),
                    "section_title": source.get("section_title") or source.get("section"),
                    "content": content,
                    "score": source.get("score") or source.get("similarity"),
                    "source": source.get("source") or "provided_evidence",
                }
            )
            if len(normalized) >= max_sources:
                break
        return normalized

    def _compose_answer(
        self,
        question: str,
        sources: list[dict[str, Any]],
        style: AnswerStyle,
        max_answer_chars: int,
    ) -> str:
        lead = f"Answer grounded in {len(sources)} provided source(s)"
        if question.strip():
            lead += f" for: {question.strip()}"
        lead += ":"

        sentences = [lead]
        source_limit = len(sources) if style == "detailed" else min(len(sources), 4)
        for source in sources[:source_limit]:
            snippet = self._best_sentence(source["content"])
            location = self._source_location(source)
            sentence = f"{snippet} [{source['anchor']}]"
            if location:
                sentence += f" ({location})"
            sentences.append(sentence)

        answer = " ".join(sentences)
        if len(answer) <= max_answer_chars:
            return answer
        return answer[: max(max_answer_chars - 1, 0)].rstrip() + "…"

    @staticmethod
    def _best_sentence(content: str) -> str:
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?。！？])\s+", content)
            if sentence.strip()
        ]
        if not sentences:
            return content[:400]
        best = max(sentences[:5], key=len)
        if len(best) > 500:
            return best[:499].rstrip() + "…"
        return best

    @staticmethod
    def _source_location(source: dict[str, Any]) -> str:
        parts = [source.get("paper_title"), source.get("section_title")]
        return ", ".join(str(part) for part in parts if part)

    @staticmethod
    def _citation_for_source(source: dict[str, Any]) -> dict[str, Any]:
        return {
            "anchor": source["anchor"],
            "id": source["id"],
            "paper_id": source.get("paper_id"),
            "paper_title": source.get("paper_title"),
            "section_title": source.get("section_title"),
            "score": source.get("score"),
            "source": source.get("source"),
        }

    @staticmethod
    def _diagnostics(answer: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?。！？])\s+", answer)
            if sentence.strip()
        ]
        cited_anchors = {
            source["anchor"]
            for source in sources
            if f"[{source['anchor']}]" in answer
        }
        unsupported = [
            sentence
            for sentence in sentences
            if not sentence.startswith("Answer grounded in")
            and not re.search(r"\[[A-Za-z]\d+\]", sentence)
        ]
        answer_sentence_count = len(sentences) or 1
        unsupported_count = len(unsupported)
        grounding_score = max(
            0.0,
            1.0 - (unsupported_count / answer_sentence_count),
        )
        return {
            "grounded": bool(sources) and grounding_score >= 0.7,
            "grounding_score": round(grounding_score, 3),
            "source_count": len(sources),
            "cited_source_count": len(cited_anchors),
            "answer_sentence_count": answer_sentence_count,
            "unsupported_sentence_count": unsupported_count,
        }
