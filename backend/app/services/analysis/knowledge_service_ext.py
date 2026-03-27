"""Extended knowledge utilities for quizzes, glossary, and retractions."""

from __future__ import annotations

import random
import re
from collections import Counter, defaultdict
from datetime import date

import structlog
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import GlossaryTerm
from app.models.paper import Paper

logger = structlog.get_logger(__name__)

GENERIC_FIELDS = [
    "computer vision",
    "natural language processing",
    "bioinformatics",
    "robotics",
    "human-computer interaction",
    "data mining",
    "machine learning",
    "distributed systems",
]

GENERIC_TOPICS = [
    "A survey of benchmark datasets and evaluation methods",
    "An optimization framework for large-scale model training",
    "A systems study on efficient resource scheduling",
    "A comparative analysis of multimodal representation learning",
    "A probabilistic framework for scientific data integration",
    "A graph-based method for retrieval and recommendation",
]


class KnowledgeExtService:
    """Knowledge-layer helpers that do not require external models or LLMs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_quiz(self, paper_id: str) -> dict:
        """Generate a small deterministic quiz from paper metadata and abstract."""
        result = await self.db.execute(
            select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
        )
        paper = result.scalar_one_or_none()
        if not paper:
            return {"error": "Paper not found"}

        rng = random.Random(str(paper.id))
        abstract_sentences = self._abstract_sentences(paper.abstract, limit=5)
        keywords = self._keyword_list(paper.keywords)
        title_hint = self._word_window(paper.title, limit=8)
        topic_answer = self._compact_phrase(
            abstract_sentences[0] if abstract_sentences else paper.title,
            limit=12,
        )
        topic_distractors = self._topic_distractors(
            paper.title,
            abstract_sentences,
            keywords,
            correct_answer=topic_answer,
        )

        field_answer = keywords[0] if keywords else self._field_fallback(paper.title)
        field_distractors = self._field_distractors(
            keywords,
            correct_answer=field_answer,
        )

        published_year = paper.published_at.year if paper.published_at else None
        year_answer = str(published_year) if published_year is not None else "Unknown"
        year_distractors = self._year_distractors(published_year)

        questions = [
            self._build_question(
                question_id="q1",
                prompt="What is the main topic of this paper?",
                correct_answer=topic_answer,
                distractors=topic_distractors,
                hint=title_hint,
                rng=rng,
            ),
            self._build_question(
                question_id="q2",
                prompt="Which field does this paper contribute to?",
                correct_answer=field_answer,
                distractors=field_distractors,
                hint=keywords[0] if keywords else title_hint,
                rng=rng,
            ),
            self._build_question(
                question_id="q3",
                prompt="What year was this paper published?",
                correct_answer=year_answer,
                distractors=year_distractors,
                hint=year_answer,
                rng=rng,
            ),
        ]

        logger.info("quiz_generated", paper_id=str(paper.id), question_count=len(questions))
        return {
            "paper_id": str(paper.id),
            "title": paper.title,
            "questions": questions,
        }

    async def get_glossary(self, paper_id: str) -> dict:
        """Combine persisted glossary terms with keyword-derived placeholders."""
        paper_result = await self.db.execute(
            select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
        )
        paper = paper_result.scalar_one_or_none()
        if not paper:
            return {"error": "Paper not found"}

        glossary_result = await self.db.execute(
            select(GlossaryTerm)
            .where(GlossaryTerm.source_paper_id == paper_id)
            .order_by(GlossaryTerm.term.asc())
        )
        stored_terms = glossary_result.scalars().all()
        abstract_text = (paper.abstract or "").casefold()

        grouped_terms: defaultdict[str, list[GlossaryTerm]] = defaultdict(list)
        for entry in stored_terms:
            grouped_terms[entry.term.casefold()].append(entry)

        terms: list[dict] = []
        for normalized_term, entries in grouped_terms.items():
            entry = sorted(
                entries,
                key=lambda item: (
                    item.is_auto_generated,
                    item.definition is None,
                    item.term.casefold(),
                ),
            )[0]
            terms.append(
                {
                    "term": entry.term,
                    "definition": entry.definition,
                    "source": "auto" if entry.is_auto_generated else "user",
                    "in_abstract": normalized_term in abstract_text,
                }
            )

        keyword_terms = self._keyword_list(paper.keywords)
        existing_terms = {term["term"].casefold() for term in terms}
        for keyword in keyword_terms:
            normalized_keyword = keyword.casefold()
            if normalized_keyword in existing_terms:
                continue
            terms.append(
                {
                    "term": keyword,
                    "definition": None,
                    "source": "auto",
                    "in_abstract": normalized_keyword in abstract_text,
                }
            )

        terms.sort(key=lambda item: item["term"].casefold())
        return {
            "paper_id": str(paper.id),
            "terms": terms,
        }

    async def get_retraction_stats(self, min_year: int = 2000) -> dict:
        """Summarize retracted papers by publication year and signal source."""
        cutoff = date(min_year, 1, 1)
        result = await self.db.execute(
            select(
                Paper.published_at,
                Paper.ingestion_status,
                Paper.raw_metadata,
                Paper.source_type,
            ).where(
                Paper.deleted_at.is_(None),
                Paper.published_at.is_not(None),
                Paper.published_at >= cutoff,
                or_(
                    Paper.ingestion_status == "retracted",
                    Paper.raw_metadata.op("?")("retraction"),
                ),
            )
        )

        by_year: Counter[int] = Counter()
        by_source: Counter[str] = Counter()

        for row in result.all():
            if row.ingestion_status != "retracted" and not self._has_retraction_flag(
                row.raw_metadata
            ):
                continue

            if row.published_at:
                by_year[row.published_at.year] += 1
            by_source[self._retraction_source(row)] += 1

        return {
            "total_retracted": sum(by_year.values()),
            "by_year": [
                {"year": year, "count": count}
                for year, count in sorted(by_year.items())
            ],
            "by_source": [
                {"source": source, "count": count}
                for source, count in sorted(
                    by_source.items(),
                    key=lambda item: (-item[1], item[0]),
                )
            ],
        }

    @staticmethod
    def _abstract_sentences(abstract: str | None, limit: int = 5) -> list[str]:
        if not abstract:
            return []
        parts = re.split(r"(?<=[.!?])\s+", " ".join(abstract.split()))
        return [part.strip() for part in parts if part.strip()][:limit]

    @staticmethod
    def _word_window(text: str | None, limit: int = 8) -> str:
        if not text:
            return "No hint available"
        words = text.split()
        return " ".join(words[:limit])

    @staticmethod
    def _compact_phrase(text: str | None, limit: int = 12) -> str:
        if not text:
            return "Unknown topic"
        cleaned = re.sub(r"\s+", " ", text).strip().rstrip(".!?")
        words = cleaned.split()
        if len(words) <= limit:
            return cleaned
        return " ".join(words[:limit]).rstrip(",;:")

    @staticmethod
    def _field_fallback(title: str | None) -> str:
        title_words = [word for word in re.split(r"\W+", title or "") if word]
        if len(title_words) >= 2:
            return f"{title_words[0]} {title_words[1]}".lower()
        if title_words:
            return title_words[0].lower()
        return "interdisciplinary research"

    @classmethod
    def _topic_distractors(
        cls,
        title: str | None,
        abstract_sentences: list[str],
        keywords: list[str],
        correct_answer: str,
    ) -> list[str]:
        candidates = [
            cls._compact_phrase(sentence, limit=12)
            for sentence in abstract_sentences[1:]
        ]
        candidates.extend(keywords[1:])
        candidates.extend(GENERIC_TOPICS)
        candidates.append(cls._compact_phrase(title, limit=8))
        return cls._dedupe_options(candidates, correct_answer)

    @staticmethod
    def _field_distractors(keywords: list[str], correct_answer: str) -> list[str]:
        candidates = keywords[1:] + GENERIC_FIELDS
        return KnowledgeExtService._dedupe_options(candidates, correct_answer)

    @staticmethod
    def _year_distractors(year: int | None) -> list[str]:
        if year is None:
            return ["2019", "2020", "2021"]
        candidates = [
            str(year - 2),
            str(year - 1),
            str(year + 1),
            str(year + 2),
        ]
        return KnowledgeExtService._dedupe_options(candidates, str(year))

    @staticmethod
    def _dedupe_options(candidates: list[str], correct_answer: str) -> list[str]:
        unique: list[str] = []
        seen: set[str] = {correct_answer.casefold()}
        for candidate in candidates:
            if not isinstance(candidate, str):
                continue
            cleaned = candidate.strip()
            if not cleaned:
                continue
            key = cleaned.casefold()
            if key in seen:
                continue
            seen.add(key)
            unique.append(cleaned)
            if len(unique) == 3:
                break
        while len(unique) < 3:
            filler = f"Alternative option {len(unique) + 1}"
            if filler.casefold() in seen:
                break
            unique.append(filler)
            seen.add(filler.casefold())
        return unique

    @staticmethod
    def _build_question(
        question_id: str,
        prompt: str,
        correct_answer: str,
        distractors: list[str],
        hint: str,
        rng: random.Random,
    ) -> dict:
        options = [correct_answer, *distractors[:3]]
        rng.shuffle(options)
        return {
            "id": question_id,
            "question": prompt,
            "options": options,
            "correct_index": options.index(correct_answer),
            "hint": hint,
        }

    @staticmethod
    def _keyword_list(raw_keywords) -> list[str]:
        if raw_keywords is None:
            return []

        if isinstance(raw_keywords, dict):
            if isinstance(raw_keywords.get("keywords"), list):
                items = raw_keywords["keywords"]
            else:
                items = list(raw_keywords.values())
        elif isinstance(raw_keywords, (list, tuple, set)):
            items = list(raw_keywords)
        else:
            return []

        keywords: list[str] = []
        seen: set[str] = set()
        for item in items:
            if isinstance(item, dict):
                value = item.get("keyword") or item.get("name") or item.get("display_name")
            else:
                value = item
            if not isinstance(value, str):
                continue
            cleaned = value.strip()
            normalized = cleaned.casefold()
            if not cleaned or normalized in seen:
                continue
            seen.add(normalized)
            keywords.append(cleaned)
        return keywords

    @staticmethod
    def _has_retraction_flag(raw_metadata: dict | None) -> bool:
        return bool(isinstance(raw_metadata, dict) and "retraction" in raw_metadata)

    @staticmethod
    def _retraction_source(row) -> str:
        raw_metadata = row.raw_metadata if isinstance(row.raw_metadata, dict) else {}
        retraction = raw_metadata.get("retraction")

        if isinstance(retraction, dict):
            for key in ("source", "provider", "origin"):
                value = retraction.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        elif isinstance(retraction, str) and retraction.strip():
            return retraction.strip()

        if row.ingestion_status == "retracted":
            return "ingestion_status"
        if row.source_type:
            return str(row.source_type)
        return "raw_metadata"