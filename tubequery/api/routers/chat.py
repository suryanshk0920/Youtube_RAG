"""
Chat Router
===========
POST /chat        — ask a question, get full answer
POST /chat/stream — ask a question, stream tokens via SSE
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from api.dependencies import get_embedding_service, get_llm_service, get_vector_store
from api.schemas import ChatRequest, ChatResponse, CitationOut
from core.retriever import ask
import config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    embedding_service=Depends(get_embedding_service),
    vector_store=Depends(get_vector_store),
    llm_service=Depends(get_llm_service),
):
    """Ask a question against an ingested knowledge base."""
    try:
        history = [{"role": m.role, "content": m.content} for m in body.history]
        answer = ask(
            question=body.question,
            kb_id=body.kb_id,
            embedding_service=embedding_service,
            vector_store=vector_store,
            llm_service=llm_service,
            history=history,
            source_ids=body.source_ids,
        )
        return ChatResponse(
            answer=answer.text,
            citations=[
                CitationOut(
                    video_title=c.video_title,
                    video_id=c.video_id,
                    timestamp_label=c.timestamp_label,
                    youtube_url=c.youtube_url,
                    excerpt=c.excerpt,
                )
                for c in answer.citations
            ],
            found_relevant_content=answer.found_relevant_content,
        )
    except Exception as e:
        logger.exception("Chat failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
def chat_stream(
    body: ChatRequest,
    embedding_service=Depends(get_embedding_service),
    vector_store=Depends(get_vector_store),
    llm_service=Depends(get_llm_service),
):
    """
    Stream answer tokens via Server-Sent Events.

    Event types:
      data: {"type": "token",    "content": "..."}   — text delta
      data: {"type": "citation", "content": {...}}    — citation object
      data: {"type": "done"}                          — stream complete
      data: {"type": "error",    "content": "..."}    — error message
    """
    def event_stream():
        try:
            history = [{"role": m.role, "content": m.content} for m in body.history]

            # Retrieve relevant chunks first (non-streaming)
            from services.embedding_service import EmbeddingService
            query_embedding = embedding_service.embed_single(body.question)
            results = vector_store.search(
                query_embedding=query_embedding,
                kb_id=body.kb_id,
                top_k=config.TOP_K,
                source_ids=body.source_ids,
            )
            relevant_chunks = [
                (chunk, score) for chunk, score in results
                if score >= config.MIN_RELEVANCE_SCORE
            ]

            if not relevant_chunks:
                yield f"data: {json.dumps({'type': 'token', 'content': 'I could not find relevant information in the ingested videos.'})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return

            # Stream tokens
            full_text = ""
            for token in llm_service.stream_answer(
                question=body.question,
                chunks=relevant_chunks,
                history=history,
            ):
                full_text += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # After streaming, build citations from the full response
            import re
            from services.llm_service import _filter_citations
            clean_text = re.sub(r"\n*SOURCES:\s*\n(?:\s*-[^\n]*\n?)*", "", full_text, flags=re.IGNORECASE).strip()
            citations = _filter_citations(clean_text, relevant_chunks)
            for c in citations:
                yield f"data: {json.dumps({'type': 'citation', 'content': {'video_title': c.video_title, 'video_id': c.video_id, 'timestamp_label': c.timestamp_label, 'youtube_url': c.youtube_url, 'excerpt': c.excerpt}})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.exception("Stream chat failed")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disables Nginx buffering on Fly.io/Railway
        },
    )
