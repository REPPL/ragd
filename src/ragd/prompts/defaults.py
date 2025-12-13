"""Default prompt templates for ragd.

This module contains all default prompts used throughout ragd.
These serve as fallbacks when users have not configured custom prompts.

v1.0.5: Configuration Exposure
"""

# =============================================================================
# RAG Response Prompts
# =============================================================================

RAG_ANSWER_SYSTEM = (
    "You are a helpful assistant that answers questions based ONLY on the provided context. "
    "Your responses MUST be grounded - every claim must come directly from the context.\n\n"
    "=== CRITICAL GROUNDING RULES ===\n"
    "1. You may ONLY make claims that are EXPLICITLY stated in the provided context.\n"
    "2. If the context does not contain relevant information, say: "
    "'I don't have information about that in my indexed documents.'\n"
    "3. NEVER infer, extrapolate, or add information beyond what is explicitly written.\n"
    "4. NEVER use your general knowledge to supplement the context.\n\n"
    "=== WHAT HALLUCINATION LOOKS LIKE (AVOID THESE) ===\n"
    "- Reframing source content to fit the question topic (e.g., describing 'heritage preservation' "
    "as 'data sovereignty' when the source never uses that term)\n"
    "- Adding terms like 'data', 'control', 'governance' that are not in the source\n"
    "- Making claims about dates, numbers, or specifics not explicitly in the context\n"
    "- Using phrases like 'typically', 'generally', 'often' to fill knowledge gaps\n"
    "- Saying 'the document discusses X' when X is only tangentially mentioned\n\n"
    "=== CITATION RULES ===\n"
    "1. Cite using ONLY the [1], [2], etc. markers from the context.\n"
    "2. Place citations immediately after each claim: 'Data sovereignty is contested [1].'\n"
    "3. NEVER mention author names or years from source text - use [1] markers instead.\n"
    "4. NEVER create a 'References' or 'Bibliography' section.\n"
    "5. EVERY factual claim MUST have a citation - uncited claims are errors.\n"
    "6. If you cannot cite a claim from the provided context, do not make it.\n\n"
    "When in doubt, say you don't have that information rather than guessing."
)

RAG_ANSWER_USER = """Answer the following question based ONLY on the provided context.

IMPORTANT:
- Cite using ONLY the [1], [2], etc. markers shown below (use [1;2] for multiple)
- DO NOT mention author names or publication years - use [1] markers instead
- DO NOT create a References/Bibliography section
- If the context doesn't contain relevant information, say so

Context:
{context}

Question: {question}

BEFORE RESPONDING: Verify that EVERY claim you make is explicitly stated in the context above.

Answer using [1] or [1;2] citations:"""

RAG_SUMMARISE_SYSTEM = (
    "You are a helpful assistant that summarises information from multiple sources. "
    "Synthesise the key points and cite all sources used. "
    "Be comprehensive yet concise."
)

RAG_SUMMARISE_USER = """Summarise the following content about: {question}

Content from multiple sources:
{context}

Provide a comprehensive summary with source citations."""

RAG_COMPARE_SYSTEM = (
    "You are a helpful assistant that compares and contrasts information from different sources. "
    "Highlight similarities, differences, and any contradictions. "
    "Cite specific sources for each point."
)

RAG_COMPARE_USER = """Compare the following information: {question}

Sources:
{context}

Analyse similarities, differences, and any contradictions. Cite sources for each point."""

RAG_CHAT_SYSTEM = (
    "You are a helpful assistant having a conversation about the user's documents. "
    "Your responses MUST be grounded in the provided context.\n\n"
    "=== CRITICAL GROUNDING RULES ===\n"
    "1. You may ONLY make claims that are EXPLICITLY stated in the provided context.\n"
    "2. If the context does not contain information to answer the question, say: "
    "'I don't have information about that in my indexed documents.'\n"
    "3. NEVER infer, extrapolate, or add information beyond what is explicitly written.\n"
    "4. NEVER use your general knowledge - ONLY the provided context.\n\n"
    "=== WHAT HALLUCINATION LOOKS LIKE (AVOID THESE) ===\n"
    "- Reframing source content to fit the question topic (e.g., describing 'heritage preservation' "
    "as 'data sovereignty' when the source never uses that term)\n"
    "- Adding terms like 'data', 'control', 'governance' that are not in the source\n"
    "- Making claims about dates, numbers, or specifics not explicitly in the context\n"
    "- Using phrases like 'typically', 'generally', 'often' to fill knowledge gaps\n"
    "- Answering questions when context is only tangentially related\n\n"
    "=== CITATION RULES ===\n"
    "1. Cite using ONLY the [1], [2], etc. markers from the context.\n"
    "2. Place citations immediately after each claim: 'The finding was X [1].'\n"
    "3. NEVER mention author names or years from source text.\n"
    "4. NEVER create a 'References' or 'Bibliography' section.\n"
    "5. EVERY factual claim MUST have a citation - uncited claims are errors.\n"
    "6. If you cannot cite a claim from the provided context, do not make it.\n\n"
    "When in doubt, say you don't have that information rather than guessing. "
    "Maintain conversation continuity where relevant."
)

RAG_CHAT_USER = """Previous conversation:
{history}

Retrieved context:
{context}

User: {question}

IMPORTANT:
- Cite using ONLY [1], [2], etc. markers (use [1;2] for multiple)
- DO NOT mention author names or publication years - use [1] markers instead
- DO NOT create a References/Bibliography section
- If the context doesn't contain relevant information, say so

BEFORE RESPONDING: Verify that EVERY claim you make is explicitly stated in the context above.

Answer:"""

RAG_REFINE_SYSTEM = (
    "You are improving a previous answer with additional context. "
    "Enhance the answer while maintaining accuracy and citations."
)

RAG_REFINE_USER = """Previous answer:
{previous_answer}

Additional context:
{context}

Question: {question}

Provide an improved answer incorporating the additional context."""

# =============================================================================
# Agentic RAG Prompts
# =============================================================================

RELEVANCE_EVAL_PROMPT = """Rate the relevance of the retrieved context to the query on a scale of 0 to 1.

Query: {query}

Retrieved Context:
{context}

Consider:
- Does the context contain information relevant to answering the query?
- Is the context topically related?
- Would this context help generate a useful response?

Respond with ONLY a number between 0 and 1, like: 0.75"""

QUERY_REWRITE_PROMPT = """The search query returned poor results. Rewrite it to be more specific and targeted.

Original Query: {query}

The retrieval returned content about: {summary}

This doesn't seem relevant. Generate a better search query that:
- Is more specific
- Uses different keywords
- Targets the user's actual information need

Respond with ONLY the rewritten query, nothing else."""

FAITHFULNESS_EVAL_PROMPT = """Evaluate if this response is faithful to the source context.

Response: {response}

Source Context:
{context}

Consider:
- Does the response only contain information from the context?
- Are there any hallucinated or made-up facts?
- Is the response accurate to what the sources say?

Respond with ONLY a number between 0 and 1, like: 0.85"""

REFINE_RESPONSE_PROMPT = """The previous answer may contain information not in the sources.
Please rewrite it to ONLY include information from the provided context.

Previous Answer: {answer}

Source Context:
{context}

Question: {question}

Provide a revised answer that strictly uses only information from the sources:"""

# =============================================================================
# Metadata Extraction Prompts
# =============================================================================

SUMMARY_PROMPT = """Summarise this document in 2-3 sentences. Focus on the main topic, key findings, and purpose.

Document:
{text}

Summary:"""

CLASSIFICATION_PROMPT = """Classify this document into one of the following categories:
- report: Formal reports, analysis documents, research papers
- article: News articles, blog posts, opinion pieces
- documentation: Technical documentation, manuals, guides
- correspondence: Emails, letters, memos
- legal: Contracts, agreements, legal documents
- financial: Invoices, budgets, financial statements
- academic: Theses, dissertations, academic papers
- other: Documents that don't fit other categories

Respond with ONLY the category name (lowercase, single word).

Document:
{text}

Category:"""

CONTEXT_GENERATION_PROMPT = """Given this document excerpt, write a brief context statement (1-2 sentences) that explains what this text is about and where it comes from. Be specific and factual.

Document: {title}
Type: {file_type}

Text:
{chunk_content}

Context:"""

# =============================================================================
# Evaluation Prompts
# =============================================================================

EVALUATION_FAITHFULNESS_PROMPT = """You are evaluating whether an answer is grounded in the provided context.

Context:
{context}

Question: {question}

Answer: {answer}

Rate how faithfully the answer is grounded in the context on a scale from 0 to 1:
- 1.0: Every claim in the answer is directly supported by the context
- 0.5: Some claims are supported, but others are not found in context
- 0.0: The answer contains claims that contradict or are not in context

Respond with ONLY a single number between 0 and 1, nothing else."""

EVALUATION_RELEVANCY_PROMPT = """You are evaluating whether an answer addresses the question.

Question: {question}

Answer: {answer}

Rate how well the answer addresses the question on a scale from 0 to 1:
- 1.0: The answer directly and completely addresses the question
- 0.5: The answer partially addresses the question
- 0.0: The answer does not address the question at all

Respond with ONLY a single number between 0 and 1, nothing else."""

# =============================================================================
# Default Prompts Dictionary (for export)
# =============================================================================

DEFAULT_PROMPTS: dict[str, dict[str, str]] = {
    "rag": {
        "answer": f"# System Prompt\n{RAG_ANSWER_SYSTEM}\n\n# User Prompt\n{RAG_ANSWER_USER}",
        "summarise": f"# System Prompt\n{RAG_SUMMARISE_SYSTEM}\n\n# User Prompt\n{RAG_SUMMARISE_USER}",
        "compare": f"# System Prompt\n{RAG_COMPARE_SYSTEM}\n\n# User Prompt\n{RAG_COMPARE_USER}",
        "chat": f"# System Prompt\n{RAG_CHAT_SYSTEM}\n\n# User Prompt\n{RAG_CHAT_USER}",
        "refine": f"# System Prompt\n{RAG_REFINE_SYSTEM}\n\n# User Prompt\n{RAG_REFINE_USER}",
    },
    "agentic": {
        "relevance_eval": RELEVANCE_EVAL_PROMPT,
        "query_rewrite": QUERY_REWRITE_PROMPT,
        "faithfulness_eval": FAITHFULNESS_EVAL_PROMPT,
        "refine_response": REFINE_RESPONSE_PROMPT,
    },
    "metadata": {
        "summary": SUMMARY_PROMPT,
        "classification": CLASSIFICATION_PROMPT,
        "context_generation": CONTEXT_GENERATION_PROMPT,
    },
    "evaluation": {
        "faithfulness": EVALUATION_FAITHFULNESS_PROMPT,
        "answer_relevancy": EVALUATION_RELEVANCY_PROMPT,
    },
}
