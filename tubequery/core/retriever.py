"""
Retriever
=========
Handles the query side of the RAG pipeline:
    question → embed → vector search → relevance filter → LLM answer

Returns a structured Answer object with citations.
"""

from __future__ import annotations

import logging

import config
from models.answer import Answer
from models.source import Source
from services.embedding_service import EmbeddingService
from services.llm_service import LLMService
from services.vector_store import VectorStore

logger = logging.getLogger(__name__)


def ask(
    question: str,
    kb_id: str,
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
    llm_service: LLMService,
    history: list[dict] | None = None,
    source_ids: list[str] | None = None,
) -> Answer:
    """
    Full retrieval pipeline.

    1. Embed the question.
    2. Search vector store for top-k similar chunks.
    3. Filter out low-relevance chunks.
    4. Send question + chunks + history to LLM.
    5. Return Answer with citations.

    Parameters
    ----------
    question : str
        The user's natural-language question.
    kb_id : str
        Knowledge base to search in.
    embedding_service : EmbeddingService
        For question embedding.
    vector_store : VectorStore
        For chunk retrieval.
    llm_service : LLMService
        For answer generation.
    history : list[dict], optional
        Previous conversation turns for multi-turn context.

    Returns
    -------
    Answer
        Structured answer with text, citations, and metadata.
    """
    if history is None:
        history = []

    # Step 1: Embed question
    query_embedding = embedding_service.embed_single(question)

    # Step 2: Retrieve top-k chunks
    results = vector_store.search(
        query_embedding=query_embedding,
        kb_id=kb_id,
        top_k=config.TOP_K,
        source_ids=source_ids,
    )

    # Step 3: Filter by relevance threshold
    relevant_chunks = [
        (chunk, score)
        for chunk, score in results
        if score >= config.MIN_RELEVANCE_SCORE
    ]

    logger.info(
        "Query '%s': %d/%d chunks above relevance threshold (%.2f)",
        question[:60],
        len(relevant_chunks),
        len(results),
        config.MIN_RELEVANCE_SCORE,
    )

    # Step 4 + 5: Generate answer with citations
    return llm_service.answer(
        question=question,
        chunks=relevant_chunks,
        history=history,
    )


def generate_intro(
    source: Source,
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
    llm_service: LLMService,
) -> dict:
    """
    After ingestion, sample chunks spread across the full video and ask
    the LLM to produce:
      - A natural, human-sounding overview paragraph
      - A bullet list of topics covered
      - 4 suggested questions

    Returns
    -------
    dict with keys:
        "intro"     : str        — overview paragraph
        "topics"    : list[str]  — topic bullets
        "questions" : list[str]  — suggested questions
    """
    # ── Sample chunks spread across the whole video ─────────────────
    # Use multiple diverse queries so we get coverage from start to end
    sample_queries = [
        "introduction beginning overview",
        "main concept explanation how it works",
        "examples demonstration practical",
        "conclusion summary key takeaways",
    ]
    all_chunks = []
    for q in sample_queries:
        emb = embedding_service.embed_single(q)
        results = vector_store.search(
            query_embedding=emb,
            kb_id=source.kb_id,
            top_k=5,
            source_id=source.id,
        )
        all_chunks.extend(results)

    if not all_chunks:
        return {
            "intro": f"**{source.title}** has been ingested with {source.chunk_count} chunks.",
            "topics": [],
            "questions": [],
        }

    # Deduplicate and sort by timestamp so context is chronological
    seen_ids: set[str] = set()
    unique_chunks = []
    for chunk, score in all_chunks:
        key = f"{chunk.video_id}_{chunk.chunk_index}"
        if key not in seen_ids:
            seen_ids.add(key)
            unique_chunks.append((chunk, score))

    unique_chunks.sort(key=lambda x: x[0].start_time)

    # Take up to 12 chunks spread across the video
    context = "\n\n---\n\n".join(
        f"[{c.timestamp_label}] {c.text}"
        for c, _ in unique_chunks[:12]
    )

    intro_prompt = f"""You are analysing a YouTube video called "{source.title}".

Here are transcript excerpts from throughout the video (in chronological order):

{context}

Based on these excerpts, provide the following in EXACTLY this format with no extra text:

OVERVIEW:
<Write 3-4 sentences describing what this video is about, who it's for, and what the viewer will learn. Write naturally and conversationally, like you're telling a friend about it.>

TOPICS:
- <topic 1>
- <topic 2>
- <topic 3>
- <topic 4>
- <topic 5>

Q1: <an interesting specific question someone would ask after watching>
Q2: <a practical how-to question based on the content>
Q3: <a deeper conceptual question about the subject>
Q4: <a question about a specific detail or example from the video>"""

    try:
        # Bypass the RAG system prompt by calling the HTTP client directly
        # so the LLM isn't constrained to "only answer from context"
        raw = llm_service.raw_completion(intro_prompt)

        # ── Parse structured response ───────────────────────────────
        intro = ""
        topics: list[str] = []
        questions: list[str] = []

        section = None
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith("OVERVIEW:"):
                section = "overview"
                rest = line[9:].strip()
                if rest:
                    intro = rest
            elif line.startswith("TOPICS:"):
                section = "topics"
            elif line.startswith("Q1:"):
                questions.append(line[3:].strip())
            elif line.startswith("Q2:"):
                questions.append(line[3:].strip())
            elif line.startswith("Q3:"):
                questions.append(line[3:].strip())
            elif line.startswith("Q4:"):
                questions.append(line[3:].strip())
            elif section == "overview" and not intro:
                intro = line
            elif section == "overview" and intro and not line.startswith("-") and not line.startswith("Q"):
                intro += " " + line
            elif section == "topics" and line.startswith("-"):
                topic = line.lstrip("- ").strip()
                if topic:
                    topics.append(topic)

        if not intro:
            intro = f"**{source.title}** has been ingested and is ready to query."

        return {"intro": intro, "topics": topics, "questions": questions}

    except Exception as exc:
        logger.warning("Could not generate intro: %s", exc)
        return {
            "intro": f"**{source.title}** has been ingested with {source.chunk_count} chunks.",
            "topics": [],
            "questions": [],
        }
