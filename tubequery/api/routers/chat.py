"""
Chat Router
===========
POST /chat — ask a question against a knowledge base
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_embedding_service, get_llm_service, get_vector_store
from api.schemas import ChatRequest, ChatResponse, CitationOut

from core.retriever import ask

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    embedding_service=Depends(get_embedding_service),
    vector_store=Depends(get_vector_store),
    llm_service=Depends(get_llm_service),
):
    """
    Ask a question against an ingested knowledge base.
    Pass conversation history for multi-turn context.
    """
    try:
        history = [{"role": m.role, "content": m.content} for m in body.history]

        answer = ask(
            question=body.question,
            kb_id=body.kb_id,
            embedding_service=embedding_service,
            vector_store=vector_store,
            llm_service=llm_service,
            history=history,
        )

        citations = [
            CitationOut(
                video_title=c.video_title,
                video_id=c.video_id,
                timestamp_label=c.timestamp_label,
                youtube_url=c.youtube_url,
                excerpt=c.excerpt,
            )
            for c in answer.citations
        ]

        return ChatResponse(
            answer=answer.text,
            citations=citations,
            found_relevant_content=answer.found_relevant_content,
        )
    except Exception as e:
        logger.exception("Chat failed")
        raise HTTPException(status_code=500, detail=str(e))
