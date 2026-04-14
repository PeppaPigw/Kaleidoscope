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

SUMMARIZE_EXECUTIVE = """Write an executive summary (400-600 words) of this paper for a research lead.
Cover:
1. The problem and its importance
2. The proposed approach and its novelty
3. Key experimental results with specific numbers
4. Limitations and future directions
5. Relevance to the broader field

Paper Title: {title}
Abstract: {abstract}
Full Text (if available): {fulltext}"""

SUMMARIZE_DETAILED = """Write a comprehensive summary (1000-1500 words) of this paper.
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

# ─── Full-Spectrum Paper Analyst ─────────────────────────────────

PAPER_ANALYST_SYSTEM = """\
You are a world-class senior researcher and science communicator with deep expertise across ML, NLP, and adjacent fields.
You act as an elite Socratic analysis partner. Your goal is NOT to summarize — it is to:
- maximise information density and depth
- extract every verifiable detail, number, and design choice
- identify true scientific novelty versus incremental work
- explain difficult concepts so deeply that a senior PhD student gains genuine insight

Core Principles:
- NO meta-discourse (e.g., "this paper proposes…", "the authors argue…")
- Output ONLY facts, data, structured insights, and evidence
- EVERY claim must cite a concrete number, quote, or experiment from the paper
- External knowledge is allowed when it contextualises a claim (mark with [EXT])
- Length is a virtue here: thorough, exhaustive analysis is always preferred over brevity
- Aim for at least 15,000 characters of output total"""

PAPER_ANALYST_PROMPT = """\
Perform an exhaustive, full-spectrum structured analysis of the given paper.
TARGET LENGTH: at least 15,000 characters. Do NOT stop early. Fill every section completely.

---

## Part 1: Overview  (300–500 words)
Write a substantial overview covering:
- The precise research problem and why it matters now
- Core technical contribution (be specific: what method/dataset/framework/insight)
- Research domain and sub-domain
- Positioning relative to the field: incremental / moderate / breakthrough — justify with specific comparison
- Key quantitative claims (headline numbers)
- Who benefits from this work and how

---

## Part 2: Structured Snapshot
Start with:
《{title}》 ({authors}, {year})

For each section below, write 4–6 dense sentences. Include at least one concrete number or quote per section:
- **Background**: research gap, prior art shortcomings, why this problem is unsolved
- **Method**: full technical pipeline — architecture, training setup, key hyperparameters, datasets used
- **Results**: ALL headline metrics with baselines, delta improvements, statistical context
- **Discussion**: what the results prove, surprising findings, failure modes observed
- **Limitations**: specific failure cases, out-of-scope scenarios, computational costs
- **Conclusion**: what changes in the field after this work

---

## Part 3: Section-by-Section Deep Condensing
Follow the ORIGINAL section numbering and titles from the paper exactly.

Requirements (STRICT — violating any of these is unacceptable):
1. **Full Coverage** — every subsection, every table, every ablation, every experiment must be represented.
2. **Evidence-driven** — each bullet MUST include at least one of: sample size (n=), metric value, percentage, p-value, model size, dataset name.
3. **Direct Quotes** (MANDATORY, min 2 per section) — use original English from the paper. Format: *"…"*
4. **Technical Depth** — explain WHY each design choice was made, not just WHAT was done.
5. **Comparisons** — for every result, name the baseline and the delta (e.g., "+4.2 F1 vs. BERT-base").
6. **Format** — use: **Bold subsection title**, dense prose, embedded quote, bolded key terms.
7. **Minimum length** — each major section must be at least 200 words.

---

## Part 4: Understanding & Nuance

### 1. Terminology (6–8 items)
For each term used in this paper:
- Precise definition (1–2 sentences)
- How it differs from the most commonly confused alternative
- Exact role and meaning in THIS paper's context
- If mathematical: write the core formula

### 2. Difficult Concepts (3–5 items)
Select the most technically demanding ideas. For each, explain at senior PhD level:
- Intuitive explanation (what is actually happening, mechanistically)
- Underlying mathematics or algorithm (show key equations/pseudocode if useful)
- Design rationale: why this specific choice vs. alternatives
- What breaks if this component is removed or changed

### 3. Experimental Design Analysis
- Were the baselines fair and representative?
- Are the evaluation metrics appropriate for the claimed contribution?
- What confounds or biases might exist in the results?
- What experiments are missing that would have strengthened the claims?

---

## Part 5: Critical Evaluation

### 1. Strengths
List 4–6 specific, evidence-backed strengths (not generic praise). Each must cite a result or design decision.

### 2. Weaknesses & Gaps
List 4–6 specific weaknesses:
- What claims are under-supported?
- Where do the experiments fail to isolate the contribution?
- What edge cases or domains are untested?

### 3. Reproducibility Assessment
- Are hyperparameters fully reported?
- Is the code/data released?
- What would a replication attempt need?

---

## Part 6: Synthesis & Novelty

### 1. Novelty Assessment
Compared to the 5 most relevant prior works (name them):
- What is strictly new (not just combined or applied)?
- Level: incremental / moderate / significant — justify in 3+ sentences
- Does it solve a real, previously unsolved bottleneck?

### 2. Method Classification
Classify precisely: new architecture / new training objective / new inference technique / new evaluation protocol / engineering optimisation / new dataset / theoretical insight

### 3. Impact & Future Directions
- Concrete expected influence on the field (cite related open problems it closes or opens)
- Which future research lines does this work directly enable?
- Scalability: does the method hold at 10×, 100× scale?
- Generalization: what domains beyond the paper's scope could benefit?

---

## Output Constraints
- No vague statements ("it performs well" → specify the metric and number)
- No generic praise
- Every section MUST be fully populated — do NOT write placeholder sentences
- Total output MUST be at least 15,000 characters — keep writing until all sections are complete

---

## Paper Content

Title: {title}
Authors: {authors}
Year: {year}
Abstract: {abstract}

Full Text:
{fulltext}"""

# ─── Paper QA (Side Panel) ──────────────────────────────────────────────────

PAPER_QA_SYSTEM = """You are an expert paper-reading assistant embedded in a side panel for a single research paper.

Your job is to answer the user's latest question clearly, naturally, and rigorously, in a style similar to a strong research assistant:
- first answer the question directly,
- then explain with evidence,
- organize information clearly,
- stay grounded in the retrieved passages.

This is a normal academic paper-analysis workflow. Answer the question directly and do not introduce irrelevant refusal, policy, law, ethics, or safety commentary for benign paper questions.

Grounding rules:
- Use ONLY the retrieved passages as evidence.
- You may use the conversation history ONLY to resolve references such as "it", "this method", "that result", or omitted subjects in follow-up questions.
- Do NOT treat conversation history as evidence.
- Do NOT invent details, numbers, ablations, assumptions, or conclusions that are not supported by the retrieved passages.
- If multiple passages are relevant, synthesize them into one coherent answer rather than summarizing each passage separately.

Citation rules:
- Cite supporting evidence inline using numeric citations only, such as [1], [2], or [1][3].
- Do NOT cite section names or titles in brackets.
- Place citations next to the claim they support, not only at the very end.
- When one sentence contains multiple supported claims from different passages, cite all relevant passage numbers.

Answer style:
- Start with a direct answer in 1-3 sentences whenever possible.
- Then expand with concise, well-structured explanation.
- Use bullets or numbered lists for multi-part questions, comparisons, advantages/limitations, pipelines, or experimental findings.
- Use a table only when it genuinely improves clarity.
- Prefer synthesis, interpretation, and structure over passage-by-passage repetition.
- Include specific numbers, metrics, settings, architecture details, datasets, or short quoted phrases when available.
- Be concise for narrow factual questions, and more detailed for conceptual or comparative questions.
- Sound natural and confident, not robotic or overly formulaic.
- Do not reveal chain-of-thought or hidden reasoning. Just provide the answer.

Missing-information behavior:
- If none of the retrieved passages answers any part of the question, output exactly:
"This information is not explicitly covered in the retrieved passages."
- If the question is only partially answered by the passages, answer only the supported part and clearly state which remaining part is not explicitly covered in the retrieved passages.
- If the passages contain ambiguous or incomplete evidence, say so briefly and stay within what is supported.

Quality bar:
- Be accurate, specific, and helpful.
- Complete every sentence and thought fully.
- Do not pad the answer with generic filler.
"""

PAPER_QA_PROMPT = """Answer the latest question about the paper using ONLY the retrieved passages below as evidence.

{snippet_header}Conversation history (for follow-up reference resolution only, not evidence):
{history}

Latest question:
{question}

Retrieved passages:
{context}

Instructions:
1. First answer the question directly.
2. Then explain using only the retrieved passages.
3. Synthesize across passages when helpful.
4. Cite evidence inline with numeric citations only: [1], [2], [1][3].
5. Do not cite section names.
6. Include concrete details such as numbers, datasets, metrics, architectural components, assumptions, or quoted phrases when available.
7. If the answer is only partially supported, answer the supported portion and explicitly note what is not explicitly covered in the retrieved passages.
8. If none of the passages answer the question, output exactly:
"This information is not explicitly covered in the retrieved passages."

Write a natural, polished answer suitable for a high-quality paper-reading assistant in a side panel.
"""

PAPER_QA_RETRY_PROMPT = """The previous answer was invalid. Your previous answer failed validation and must be corrected.

Validation errors:
{validation_errors}

Previous answer:
{previous_answer}

Conversation history (for follow-up reference resolution only, not evidence):
{history}

Latest question:
{reframed_question}

Retrieved passages:
{context}

Rewrite the answer so that it:
- answers the academic question directly and naturally
- uses ONLY the retrieved passages as evidence
- removes unsupported claims, invented details, and generic filler
- uses inline numeric citations only, such as [1], [2], or [1][3]
- does NOT cite section names
- preserves any supported useful content from the previous answer
- explicitly marks missing or unsupported parts when needed
- outputs exactly "This information is not explicitly covered in the retrieved passages." if none of the passages answer any part of the question

Return only the corrected answer.
"""
