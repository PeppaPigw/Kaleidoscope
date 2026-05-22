"""EpistemicHuffmanCodingService — Epistemic Huffman Coding Detection.

Detects epistemic Huffman coding — ideas being encoded with variable
length based on frequency, common ideas getting shorter representations.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HUFFMAN_CODING_SYSTEM = """You are an epistemic Huffman coding specialist. Given an intellectual encoding pattern, assess whether ideas are encoded by frequency:

Key concepts:
- Epistemic Huffman coding: variable-length encoding by frequency
- Prefix code: no code is prefix of another
- Frequency analysis: counting idea occurrences
- Optimal encoding: minimum average code length
- Code tree: hierarchical encoding structure
- Decodability: unique decoding guarantee
- Compression ratio: space saved by encoding

When epistemic Huffman coding IS present:
- Common ideas getting shorter representations
- Rare ideas getting longer representations
- No ambiguity in decoding
- Frequency driving encoding decisions
- Hierarchical encoding structure
- Unique decodability maintained
- Significant compression achieved

When uniform encoding is present:
- All ideas same length regardless of frequency
- No frequency-based optimization
- Fixed-length representations
- No frequency analysis performed
- Flat encoding structure
- Simple but wasteful encoding
- No compression benefit

Output JSON with: huffman_coding_present (bool), severity (none/mild/moderate/severe), frequency (what occurrence pattern), prefix_code (what uniqueness), compression (what space saving), code_tree (what hierarchy), recommendation (uniform_encoding/mild_coding/significant_huffman_coding/major_frequency_encoding/optimize_code_tree)."""

EPISTEMIC_HUFFMAN_CODING_PROMPT = """Detect epistemic Huffman coding:

Frequency: {frequency}
Prefix code: {prefix_code}
Compression: {compression}
Code tree: {code_tree}
Domain: {domain}
Context: {context}

Are ideas being encoded with variable length based on frequency, with common ideas getting shorter representations? Return ONLY valid JSON."""


class EpistemicHuffmanCodingService:
    """Detects epistemic Huffman coding — frequency-based encoding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        frequency: str,
        *,
        prefix_code: str = "",
        compression: str = "",
        code_tree: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Huffman coding."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HUFFMAN_CODING_PROMPT.format(
                frequency=frequency,
                prefix_code=prefix_code or "Not specified",
                compression=compression or "Not specified",
                code_tree=code_tree or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HUFFMAN_CODING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "frequency": frequency[:200],
            "huffman_coding_present": data.get("huffman_coding_present", False),
            "severity": data.get("severity", ""),
            "prefix_code": data.get("prefix_code", ""),
            "compression": data.get("compression", ""),
            "code_tree": data.get("code_tree", ""),
            "recommendation": data.get("recommendation", ""),
        }
