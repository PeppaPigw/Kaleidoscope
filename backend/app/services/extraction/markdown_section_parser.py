"""Robust Markdown section parser for academic papers.

Handles H1 misidentification: some parsers (e.g. MinerU) promote H2 headings to
H1, so a paper ends up with 20+ H1s instead of the canonical 6–10 top-level
sections. This module detects that and corrects the heading levels before
splitting into sections.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ── Canonical top-level section names ────────────────────────────────────────

CANONICAL_TOP_LEVEL: frozenset[str] = frozenset(
    {
        "abstract",
        "introduction",
        "related work",
        "background",
        "literature review",
        "preliminaries",
        "notation",
        "method",
        "methods",
        "methodology",
        "approach",
        "model",
        "framework",
        "proposed method",
        "proposed approach",
        "our method",
        "our approach",
        "experiments",
        "experiment",
        "evaluation",
        "experimental setup",
        "experimental results",
        "experimental evaluation",
        "results",
        "results and discussion",
        "results and analysis",
        "discussion",
        "analysis",
        "ablation",
        "ablation study",
        "ablation studies",
        "conclusion",
        "conclusions",
        "concluding remarks",
        "summary",
        "limitations",
        "limitation",
        "ethical considerations",
        "broader impact",
        "appendix",
        "appendices",
        "supplementary",
        "supplementary material",
        "supplemental material",
        "references",
        "bibliography",
        "acknowledgments",
        "acknowledgements",
        "acknowledgment",
        "acknowledgement",
        "conflict of interest",
        "data availability",
        "code availability",
        "reproducibility",
    }
)

# Subsection number pattern: "3.1", "A.1", "3.1.2" etc.
_SUBSECTION_RE = re.compile(r"^[A-Z0-9]+\.\d+")

# Whole heading line pattern
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


# ── Data structures ──────────────────────────────────────────────────────────


@dataclass
class ParsedSection:
    title: str
    normalized_title: str  # lowercase, stripped
    level: int  # corrected heading level (1 = top-level)
    content: str
    order_index: int
    is_appendix: bool = False
    is_references: bool = False
    token_estimate: int = field(init=False)

    def __post_init__(self) -> None:
        self.token_estimate = len(self.content.split())


# ── Helpers ──────────────────────────────────────────────────────────────────


def _normalize(title: str) -> str:
    """Lowercase, strip markdown formatting and punctuation."""
    t = title.strip()
    # Remove bold/italic markers
    t = re.sub(r"[*_`]", "", t)
    # Remove trailing punctuation
    t = t.rstrip(".:;,")
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t


def _is_canonical(normalized: str) -> bool:
    """Check if a normalized heading matches any canonical section name."""
    if normalized in CANONICAL_TOP_LEVEL:
        return True
    # Partial match: "3 experiments" → strip leading number
    stripped = re.sub(r"^\d+\.?\s*", "", normalized).strip()
    return stripped in CANONICAL_TOP_LEVEL


def _is_subsection_numbered(title: str) -> bool:
    """Check if heading looks like 'A.1 ...', '3.1 ...', '3.1.2 ...'"""
    t = title.strip()
    return bool(_SUBSECTION_RE.match(t))


def _needs_h1_correction(headings: list[tuple[int, str]]) -> bool:
    """
    Return True if H1s appear to include misidentified H2s.

    Heuristics:
    - More than 8 H1 headings total, OR
    - H1s include sub-section numbered headings like "3.1 ..."
    """
    h1s = [(lvl, t) for lvl, t in headings if lvl == 1]
    if len(h1s) <= 8:
        return False

    # Check for subsection numbers among H1s
    has_subsection_h1 = any(_is_subsection_numbered(t) for _, t in h1s)
    if has_subsection_h1:
        return True

    # Check canonical ratio
    canonical_count = sum(1 for _, t in h1s if _is_canonical(_normalize(t)))
    ratio = canonical_count / len(h1s) if h1s else 1.0
    return ratio < 0.5


def _correct_headings(
    headings: list[tuple[int, str]],
) -> list[tuple[int, str]]:
    """
    Reassign heading levels so that canonical top-level sections become H1
    and everything else is demoted by one level.
    """
    result: list[tuple[int, str]] = []
    for lvl, title in headings:
        if lvl == 1:
            norm = _normalize(title)
            if _is_canonical(norm) and not _is_subsection_numbered(title):
                result.append((1, title))
            else:
                result.append((2, title))
        else:
            # H2+ stay as-is (already sub-sections)
            result.append((lvl, title))
    return result


# ── Main parser ──────────────────────────────────────────────────────────────


def parse_markdown_sections(markdown: str) -> list[ParsedSection]:
    """
    Parse a paper's markdown into section-level chunks.

    - Applies H1 misidentification correction.
    - Skips empty sections.
    - Marks references and appendix sections.
    - Splits sections >1500 tokens with a sliding window (512 tokens, 64 overlap).
    """
    if not markdown or not markdown.strip():
        return []

    # Find all headings
    raw_headings = [
        (len(m.group(1)), m.group(2).strip()) for m in _HEADING_RE.finditer(markdown)
    ]

    if not raw_headings:
        return _fallback_paragraph_chunks(markdown)

    # Correct H1 misidentification
    if _needs_h1_correction(raw_headings):
        corrected_headings = _correct_headings(raw_headings)
    else:
        corrected_headings = raw_headings

    # Build a corrected markdown (replace heading markers)
    corrected_md = _apply_heading_corrections(
        markdown, raw_headings, corrected_headings
    )

    # Split on H1 boundaries
    sections = _split_on_h1(corrected_md)

    # Convert to ParsedSection objects
    result: list[ParsedSection] = []
    order = 0
    in_appendix = False

    for title, content in sections:
        norm = _normalize(title)

        # Detect appendix transition
        if norm in {
            "appendix",
            "appendices",
            "supplementary",
            "supplementary material",
            "supplemental material",
        }:
            in_appendix = True

        is_refs = norm in {"references", "bibliography"}
        is_app = in_appendix and not is_refs

        if not content.strip():
            continue

        # Split long sections
        sub_chunks = _split_long_section(
            title=title,
            norm=norm,
            content=content,
            level=1,
            is_appendix=is_app,
            is_references=is_refs,
            start_order=order,
        )
        result.extend(sub_chunks)
        order += len(sub_chunks)

    return result


# ── Internal helpers ─────────────────────────────────────────────────────────


def _apply_heading_corrections(
    markdown: str,
    raw: list[tuple[int, str]],
    corrected: list[tuple[int, str]],
) -> str:
    """Rewrite heading lines in markdown according to corrected levels."""
    if raw == corrected:
        return markdown

    lines = markdown.split("\n")
    # Build mapping: (original heading text) → corrected level
    # Walk lines and replace heading markers
    out_lines: list[str] = []
    raw_q = list(zip(raw, corrected, strict=False))
    rq_idx = 0

    for line in lines:
        if rq_idx < len(raw_q):
            (r_lvl, r_title), (c_lvl, _c_title) = raw_q[rq_idx]
            stripped = line.strip()
            expected = "#" * r_lvl + " " + r_title
            if stripped == expected or line.rstrip() == expected:
                if r_lvl != c_lvl:
                    out_lines.append("#" * c_lvl + " " + r_title)
                else:
                    out_lines.append(line)
                rq_idx += 1
                continue
        out_lines.append(line)

    return "\n".join(out_lines)


def _split_on_h1(markdown: str) -> list[tuple[str, str]]:
    """Split markdown into (heading_title, body_content) pairs on H1 boundaries."""
    h1_pattern = re.compile(r"^# (.+)$", re.MULTILINE)
    matches = list(h1_pattern.finditer(markdown))

    if not matches:
        return []

    sections: list[tuple[str, str]] = []

    # Text before first H1 (if any) — treat as preamble, skip if too short
    preamble = markdown[: matches[0].start()].strip()
    if preamble and len(preamble.split()) > 20:
        sections.append(("Preamble", preamble))

    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        body = markdown[start:end].strip()
        sections.append((title, body))

    return sections


def _split_long_section(
    title: str,
    norm: str,
    content: str,
    level: int,
    is_appendix: bool,
    is_references: bool,
    start_order: int,
    max_tokens: int = 1500,
    window: int = 512,
    overlap: int = 64,
) -> list[ParsedSection]:
    """Split a section into sub-chunks if it exceeds max_tokens."""
    words = content.split()
    token_count = len(words)

    if token_count <= max_tokens:
        return [
            ParsedSection(
                title=title,
                normalized_title=norm,
                level=level,
                content=content,
                order_index=start_order,
                is_appendix=is_appendix,
                is_references=is_references,
            )
        ]

    # Sliding window chunking
    chunks: list[ParsedSection] = []
    pos = 0
    sub_idx = 0
    while pos < token_count:
        chunk_words = words[pos : pos + window]
        chunk_text = " ".join(chunk_words)
        chunks.append(
            ParsedSection(
                title=f"{title} (part {sub_idx + 1})",
                normalized_title=norm,
                level=level,
                content=chunk_text,
                order_index=start_order + sub_idx,
                is_appendix=is_appendix,
                is_references=is_references,
            )
        )
        sub_idx += 1
        pos += window - overlap
        if pos + overlap >= token_count:
            break

    return chunks


def _fallback_paragraph_chunks(markdown: str) -> list[ParsedSection]:
    """Fallback: split by paragraphs when no headings are found."""
    paragraphs = re.split(r"\n{2,}", markdown.strip())
    chunks: list[ParsedSection] = []
    for i, para in enumerate(paragraphs):
        para = para.strip()
        if len(para.split()) < 20:
            continue
        chunks.append(
            ParsedSection(
                title=f"Section {i + 1}",
                normalized_title=f"section {i + 1}",
                level=1,
                content=para,
                order_index=i,
            )
        )
    return chunks
