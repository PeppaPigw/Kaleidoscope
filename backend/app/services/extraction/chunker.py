"""Text chunking for RAG — split full-text into paragraphs/sections for retrieval."""

import re

import structlog

logger = structlog.get_logger(__name__)


class TextChunker:
    """
    Split paper text into chunks suitable for embedding and retrieval.

    Supports two modes:
    1. Section-based chunking (for GROBID-parsed papers with sections)
    2. Paragraph-based chunking (for raw text)
    """

    def __init__(
        self,
        max_chunk_size: int = 512,
        overlap: int = 64,
        min_chunk_size: int = 50,
    ):
        self.max_chunk_size = max_chunk_size  # in tokens (~words)
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size

    def chunk_paper(
        self, paper_id: str, text: str, sections: list[dict] | None = None
    ) -> list[dict]:
        """
        Chunk a paper's text into passages for embedding.

        Returns list of chunks with metadata:
        [{"paper_id": ..., "chunk_index": ..., "section": ..., "text": ..., "word_count": ...}]
        """
        if sections:
            return self._chunk_by_sections(paper_id, sections)
        return self._chunk_by_paragraphs(paper_id, text)

    def _chunk_by_sections(self, paper_id: str, sections: list[dict]) -> list[dict]:
        """Chunk using GROBID-parsed sections."""
        chunks = []
        index = 0

        for section in sections:
            section_name = section.get("heading", "Unknown")
            section_text = section.get("text", "")

            if not section_text or len(section_text.split()) < self.min_chunk_size:
                continue

            # Split long sections into sub-chunks
            words = section_text.split()
            if len(words) <= self.max_chunk_size:
                chunks.append({
                    "paper_id": paper_id,
                    "chunk_index": index,
                    "section": section_name,
                    "text": section_text,
                    "word_count": len(words),
                })
                index += 1
            else:
                # Sliding window with overlap
                for start in range(0, len(words), self.max_chunk_size - self.overlap):
                    end = min(start + self.max_chunk_size, len(words))
                    chunk_words = words[start:end]
                    if len(chunk_words) < self.min_chunk_size:
                        break
                    chunks.append({
                        "paper_id": paper_id,
                        "chunk_index": index,
                        "section": section_name,
                        "text": " ".join(chunk_words),
                        "word_count": len(chunk_words),
                    })
                    index += 1

        logger.info("chunked_by_sections", paper_id=paper_id,
                     chunks=len(chunks), sections=len(sections))
        return chunks

    def _chunk_by_paragraphs(self, paper_id: str, text: str) -> list[dict]:
        """
        Chunk by splitting on paragraph boundaries.

        Falls back to fixed-size sliding window if paragraphs are too long.
        """
        # Split on double newlines (paragraph breaks)
        paragraphs = re.split(r"\n\s*\n", text)

        chunks = []
        index = 0
        current_text = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_words = para.split()

            # If adding this paragraph exceeds max, flush current
            if current_text and (len(current_text.split()) + len(para_words)) > self.max_chunk_size:
                chunks.append({
                    "paper_id": paper_id,
                    "chunk_index": index,
                    "section": None,
                    "text": current_text,
                    "word_count": len(current_text.split()),
                })
                index += 1
                # Keep overlap
                overlap_words = current_text.split()[-self.overlap:]
                current_text = " ".join(overlap_words) + " " + para
            else:
                current_text = (current_text + "\n\n" + para).strip()

        # Flush remaining
        if current_text and len(current_text.split()) >= self.min_chunk_size:
            chunks.append({
                "paper_id": paper_id,
                "chunk_index": index,
                "section": None,
                "text": current_text,
                "word_count": len(current_text.split()),
            })

        logger.info("chunked_by_paragraphs", paper_id=paper_id, chunks=len(chunks))
        return chunks

    @staticmethod
    def prepare_paper_text(paper) -> str:
        """
        Assemble the best available full-text from a paper's various sources.

        Priority:
        1. Parsed sections (from GROBID — stored as {heading, paragraphs: [str]})
        2. Extracted fulltext (from LaTeX)
        3. TEI XML → plain text strip
        4. Abstract only
        """
        raw = paper.raw_metadata or {}

        # 1. Parsed sections — GROBID stores {heading, number, paragraphs}
        if raw.get("parsed_sections"):
            parts = []
            for s in raw["parsed_sections"]:
                heading = s.get("heading", "Section")
                # GROBID sections use "paragraphs" (list[str]), not "text"
                paragraphs = s.get("paragraphs", [])
                text = s.get("text", "")  # Fallback if someone stored flat text
                section_text = "\n".join(paragraphs) if paragraphs else text
                if section_text:
                    parts.append(f"## {heading}\n{section_text}")
            if parts:
                return "\n\n".join(parts)

        # 2. Extracted fulltext (LaTeX)
        if raw.get("extracted_fulltext"):
            return raw["extracted_fulltext"]

        # 3. TEI XML → strip tags
        if paper.grobid_tei:
            import re
            return re.sub(r"<[^>]+>", " ", paper.grobid_tei)

        # 4. Fallback to abstract
        return paper.abstract or ""

    @staticmethod
    def get_sections_for_chunking(paper) -> list[dict] | None:
        """
        Extract structured sections suitable for _chunk_by_sections().

        Returns list of {heading, text} dicts, or None if no sections available.
        """
        raw = paper.raw_metadata or {}
        parsed = raw.get("parsed_sections", [])
        if not parsed:
            return None

        sections = []
        for s in parsed:
            paragraphs = s.get("paragraphs", [])
            text = "\n".join(paragraphs) if paragraphs else s.get("text", "")
            if text:
                sections.append({
                    "heading": s.get("heading", "Unknown"),
                    "text": text,
                })
        return sections if sections else None

