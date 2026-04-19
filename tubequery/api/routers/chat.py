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

from api.auth import get_current_user, get_supabase
from api.db_orm import log_usage, upsert_user
from api.dependencies import get_embedding_service, get_llm_service, get_vector_store
from api.schemas import ChatRequest, ChatResponse, CitationOut
from core.retriever import ask
from utils.security import sanitize_input, SECURITY_HEADERS
from services.subscription_service_redis import RedisSubscriptionService
import config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user: dict = Depends(get_current_user),
    db=Depends(get_supabase),
    embedding_service=Depends(get_embedding_service),
    vector_store=Depends(get_vector_store),
    llm_service=Depends(get_llm_service),
):
    """Ask a question against an ingested knowledge base."""
    try:
        # Check question limit before processing
        subscription_service = RedisSubscriptionService(db)
        can_ask, limit_details = await subscription_service.check_question_limit(user["uid"])
        
        if not can_ask:
            raise HTTPException(
                status_code=429, 
                detail={
                    "message": limit_details.get("upgrade_message", {}).get("message", "Daily question limit reached"),
                    "upgrade_required": True,
                    "limit_details": limit_details
                }
            )
        
        # Additional security validation (Pydantic already validates)
        sanitize_input(body.question)
        
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
        log_usage(db, user["uid"], "chat", metadata={"question": body.question[:100]})
        
        # Update daily usage count (Redis-based)
        try:
            subscription_service = RedisSubscriptionService(db)
            await subscription_service.increment_usage_redis(user["uid"], "chat")
            logger.info(f"Successfully incremented chat usage for user {user['uid']}")
        except Exception as e:
            logger.error(f"Failed to update daily usage for user {user['uid']}: {e}")
            # Also log the full traceback for debugging
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
        
        response = ChatResponse(
            answer=answer.text,
            citations=[CitationOut(video_title=c.video_title, video_id=c.video_id, timestamp_label=c.timestamp_label, youtube_url=c.youtube_url, excerpt=c.excerpt) for c in answer.citations],
            found_relevant_content=answer.found_relevant_content,
        )
        
        # Add security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
            
        return response
        
    except ValueError as e:
        logger.warning(f"Invalid input from user {user['uid']}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chat failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    user: dict = Depends(get_current_user),
    db=Depends(get_supabase),
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
    async def event_stream():
        try:
            # Check question limit before processing
            subscription_service = RedisSubscriptionService(db)
            can_ask, limit_details = await subscription_service.check_question_limit(user["uid"])
            
            if not can_ask:
                error_msg = limit_details.get("upgrade_message", {}).get("message", "Daily question limit reached")
                yield f"data: {json.dumps({'type': 'error', 'content': error_msg, 'upgrade_required': True, 'limit_details': limit_details})}\n\n"
                return

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
            logger.info("Chat search: kb=%s source_ids=%s results=%d", body.kb_id, body.source_ids, len(results))
            relevant_chunks = [
                (chunk, score) for chunk, score in results
                if score >= config.MIN_RELEVANCE_SCORE
            ]
            logger.info("After relevance filter (threshold=%.2f): %d chunks. Scores: %s",
                        config.MIN_RELEVANCE_SCORE, len(relevant_chunks),
                        [round(s, 3) for _, s in results[:5]])

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
                # Escape the token as JSON to handle newlines/special chars safely
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            logger.info("Stream complete. Full response length: %d chars. First 200: %s", len(full_text), full_text[:200])

            # After streaming, build citations from the full response
            # Pass full_text WITH the SOURCES block so _filter_citations can parse it
            import re
            from services.llm_service import _filter_citations
            citations = _filter_citations(full_text, relevant_chunks)
            for c in citations:
                yield f"data: {json.dumps({'type': 'citation', 'content': {'video_title': c.video_title, 'video_id': c.video_id, 'timestamp_label': c.timestamp_label, 'youtube_url': c.youtube_url, 'excerpt': c.excerpt}})}\n\n"

            log_usage(db, user["uid"], "chat", metadata={"question": body.question[:100]})
            
            # Update daily usage count (Redis-based)
            try:
                subscription_service = RedisSubscriptionService(db)
                await subscription_service.increment_usage_redis(user["uid"], "chat")
                logger.info(f"Successfully incremented chat usage for user {user['uid']}")
            except Exception as e:
                logger.error(f"Failed to update daily usage for user {user['uid']}: {e}")
                # Also log the full traceback for debugging
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
            
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
