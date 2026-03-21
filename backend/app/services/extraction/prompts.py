"""Prompt templates for LLM-powered extraction and analysis."""

# ─── Summarization ───────────────────────────────────────────────

SUMMARIZE_SYSTEM = """You are an expert academic paper summarizer.
Produce clear, accurate summaries that preserve technical precision.
Always cite specific findings with numbers when available.
Do NOT hallucinate or add claims not present in the paper."""

SUMMARIZE_TWEET = """Summarize this paper in 1-2 sentences, suitable for a tweet.
Be concise but informative. Include the key contribution.

Paper Title: {title}
Abstract: {abstract}
Full Text (if available): {fulltext}"""

SUMMARIZE_ABSTRACT = """Write a structured summary of this paper with these sections:
- **Background**: What problem does this address?
- **Method**: What approach is proposed?
- **Results**: What are the key findings?
- **Conclusion**: What is the significance?

Keep each section to 2-3 sentences. Total ~300 words.

Paper Title: {title}
Abstract: {abstract}
Full Text (if available): {fulltext}"""

SUMMARIZE_EXECUTIVE = """Write an executive summary (600-800 words) of this paper for a research lead.
Cover:
1. The problem and its importance
2. The proposed approach and its novelty
3. Key experimental results with specific numbers
4. Limitations and future directions
5. Relevance to the broader field

Paper Title: {title}
Abstract: {abstract}
Full Text (if available): {fulltext}"""

SUMMARIZE_DETAILED = """Write a comprehensive summary (1500-2000 words) of this paper.
Include:
1. Introduction and motivation
2. Related work context
3. Detailed methodology
4. Complete experimental setup and results
5. Analysis and discussion
6. Limitations
7. Conclusions and future work

Paper Title: {title}
Abstract: {abstract}
Full Text (if available): {fulltext}"""

# ─── Structured Extraction ───────────────────────────────────────

EXTRACT_SYSTEM = """You are an expert academic paper analyzer.
Extract structured information accurately from the paper.
Return a valid JSON object. Only include information explicitly stated in the paper.
Mark uncertain extractions with "confidence": "low"."""

EXTRACT_HIGHLIGHTS = """Extract the key highlights, contributions, and limitations from this paper.
Return JSON with this structure:
{{
  "highlights": ["highlight 1", "highlight 2", ...],
  "contributions": ["contribution 1", ...],
  "limitations": ["limitation 1", ...],
  "future_work": ["direction 1", ...],
  "novelty_claim": "One sentence describing what's new"
}}

Paper Title: {title}
Abstract: {abstract}
Full Text: {fulltext}"""

EXTRACT_METHODS = """Extract the methods, datasets, and metrics from this paper.
Return JSON:
{{
  "methods": [{{"name": "...", "description": "...", "is_novel": true/false}}],
  "datasets": [{{"name": "...", "size": "...", "domain": "..."}}],
  "metrics": [{{"name": "...", "value": "...", "is_main_result": true/false}}],
  "baselines": ["baseline 1", "baseline 2", ...],
  "implementation_details": {{
    "framework": "...",
    "hardware": "...",
    "training_time": "...",
    "code_available": true/false
  }}
}}

Paper Title: {title}
Abstract: {abstract}
Full Text: {fulltext}"""

# ─── QA ──────────────────────────────────────────────────────────

QA_SYSTEM = """You are a helpful research assistant answering questions about academic papers.
Base your answers ONLY on the provided context passages.
If the answer is not in the context, say "I cannot find this information in the provided passages."
Always cite which passage(s) support your answer using [1], [2], etc."""

QA_PROMPT = """Answer the following question based on the context passages from the paper.

Question: {question}

Context:
{context}

Instructions:
- Answer using information from the context passages only
- Cite passage numbers [1], [2], etc.
- If uncertain, express uncertainty
- Be concise but complete"""

QA_MULTI_DOC_SYSTEM = """You are a research assistant answering questions across multiple papers.
Synthesize information from all provided papers.
Cite each paper by its title or ID when referencing specific information.
Compare and contrast findings across papers when relevant."""

QA_MULTI_DOC_PROMPT = """Answer the following question using information from multiple papers.

Question: {question}

Papers and their relevant passages:
{papers_context}

Instructions:
- Synthesize information across papers
- Note agreements and disagreements between papers
- Cite paper titles/IDs for each claim
- Be comprehensive but concise"""
