"""
LLM Service
============
Abstract interface for large-language-model answer generation,
plus a concrete Gemini implementation.

The system prompt constrains the model to only answer from
provided transcript context and always cite sources.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from google import genai
from google.genai import types

import config
from models.answer import Answer, Citation
from models.chunk import Chunk

logger = logging.getLogger(__name__)

# ── System Prompt ───────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are a helpful assistant that answers questions based ONLY on the
provided video transcript excerpts. You must:

1. Only use information from the provided context excerpts.
2. If the context does not contain enough information to answer,
   say: "I could not find relevant information in the ingested videos."
3. Always end your answer with a SOURCES section listing ONLY the
   specific excerpts you actually used, using this exact format:
   SOURCES:
   - [Video Title] at [MM:SS]
4. Never make up information not present in the excerpts.
5. Keep answers clear and concise.
6. Only cite sources you genuinely drew information from — do not list
   every excerpt provided, only the ones that contributed to your answer.
"""


def _filter_citations(
    answer_text: str,
    chunks: list[tuple[Chunk, float]],
) -> list[Citation]:
    """
    Parse the SOURCES section from the LLM answer and return only
    citations that match chunks the model actually referenced.

    Falls back to the single highest-scoring chunk if parsing fails.
    """
    import re

    # Extract the SOURCES block
    sources_match = re.search(r"SOURCES:\s*\n((?:\s*-[^\n]+\n?)+)", answer_text, re.IGNORECASE)

    matched: list[Citation] = []

    if sources_match:
        sources_block = sources_match.group(1)
        for line in sources_block.splitlines():
            line = line.strip().lstrip("- ").strip()
            if not line:
                continue
            # Match by title only (first 20 chars, case-insensitive) — timestamp matching
            # is unreliable because LLMs reformat timestamps
            for chunk, score in chunks:
                title_fragment = chunk.video_title.lower()[:20]
                if title_fragment and title_fragment in line.lower():
                    matched.append(Citation(
                        video_title=chunk.video_title,
                        video_id=chunk.video_id,
                        timestamp_label=chunk.timestamp_label,
                        youtube_url=chunk.youtube_url,
                        excerpt=chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                    ))
                    break
                # Also try matching by timestamp alone if title match fails
                if chunk.timestamp_label in line:
                    matched.append(Citation(
                        video_title=chunk.video_title,
                        video_id=chunk.video_id,
                        timestamp_label=chunk.timestamp_label,
                        youtube_url=chunk.youtube_url,
                        excerpt=chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                    ))
                    break

    # Deduplicate by video_id + timestamp
    seen: set[str] = set()
    unique: list[Citation] = []
    for c in matched:
        key = f"{c.video_id}_{c.timestamp_label}"
        if key not in seen:
            seen.add(key)
            unique.append(c)

    # Fallback: if nothing matched, use the top-scoring chunk
    if not unique and chunks:
        best_chunk, _ = max(chunks, key=lambda x: x[1])
        unique.append(Citation(
            video_title=best_chunk.video_title,
            video_id=best_chunk.video_id,
            timestamp_label=best_chunk.timestamp_label,
            youtube_url=best_chunk.youtube_url,
            excerpt=best_chunk.text[:200] + "..." if len(best_chunk.text) > 200 else best_chunk.text,
        ))

    return unique


# ── Interface ───────────────────────────────────────────────────────
    # Fallback: if parsing found nothing, use only the top-scoring chunk
    if not unique and chunks:
        best = max(chunks, key=lambda x: x[1])
        chunk, _ = best
        unique.append(Citation(
            video_title=chunk.video_title,
            video_id=chunk.video_id,
            timestamp_label=chunk.timestamp_label,
            youtube_url=chunk.youtube_url,
            excerpt=chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
        ))

    return unique


# ── Interface ───────────────────────────────────────────────────────
class LLMService(ABC):
    """Base class for all LLM implementations."""

    @abstractmethod
    def answer(
        self,
        question: str,
        chunks: list[tuple[Chunk, float]],
        history: list[dict],
    ) -> Answer:
        """Generate an answer from the question, relevant chunks, and history."""

    def raw_completion(self, prompt: str) -> str:
        """
        Send a plain prompt with no RAG system constraints.
        Used for summarisation tasks like generate_intro.
        Default implementation falls back to answer() with empty chunks.
        Override in subclasses for a cleaner call.
        """
        result = self.answer(question=prompt, chunks=[], history=[])
        return result.text


# ── Gemini Implementation ──────────────────────────────────────────
class GeminiLLMService(LLMService):
    """
    Google Gemini implementation.

    - Uses ``gemini-1.5-flash`` by default (configurable).
    - Maintains conversational context via ``history``.
    - Returns structured ``Answer`` with citations.
    """

    def __init__(self) -> None:
        if not config.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Add it to your .env file or environment variables."
            )
        self._client = genai.Client(api_key=config.GEMINI_API_KEY)
        logger.info("Gemini LLM service initialised (%s).", config.GEMINI_MODEL)

    def answer(
        self,
        question: str,
        chunks: list[tuple[Chunk, float]],
        history: list[dict],
    ) -> Answer:
        # No relevant chunks → short-circuit
        if not chunks:
            return Answer(
                text="I could not find relevant information in the ingested videos.",
                citations=[],
                found_relevant_content=False,
            )

        # Build context string from retrieved chunks
        context_parts: list[str] = []
        for chunk, score in chunks:
            context_parts.append(
                f"[{chunk.video_title} | {chunk.timestamp_label}]\n{chunk.text}"
            )
        context = "\n\n---\n\n".join(context_parts)

        # Build conversation history for the new SDK
        gemini_history: list[types.Content] = []
        for turn in history[-config.CONVERSATION_HISTORY_TURNS:]:
            role = turn["role"]  # "user" or "assistant" → "model"
            if role == "assistant":
                role = "model"
            gemini_history.append(
                types.Content(role=role, parts=[types.Part(text=turn["content"])])
            )

        prompt = f"Context from videos:\n\n{context}\n\nQuestion: {question}"

        # Generate answer using the new SDK
        response = self._client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=gemini_history + [types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            ),
        )
        answer_text: str = response.text

        return Answer(
            text=answer_text,
            citations=_filter_citations(answer_text, chunks),
            raw_chunks=chunks,
        )


# ── Future implementations ─────────────────────────────────────────
# class ClaudeLLMService(LLMService): ...
# class OpenAILLMService(LLMService): ...


# ── OpenRouter Implementation ──────────────────────────────────────
class OpenRouterLLMService(LLMService):
    """
    OpenRouter implementation — routes to any model via OpenAI-compatible API.

    - Supports reasoning models (passes reasoning_details back for multi-turn).
    - Uses ``config.OPENROUTER_MODEL`` (default: ``openrouter/auto``).
    - Set OPENROUTER_MODEL=openrouter/free in .env for the free tier.
    """

    _API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self) -> None:
        import httpx
        if not config.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY is not set. "
                "Add it to your .env file."
            )
        self._http = httpx.Client(timeout=60.0)
        self._headers = {
            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        logger.info("OpenRouter LLM service initialised (%s).", config.OPENROUTER_MODEL)

    def raw_completion(self, prompt: str) -> str:
        """Direct completion with no RAG system prompt — for summarisation."""
        payload = {
            "model": config.OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = self._http.post(
            self._API_URL, headers=self._headers, json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"].get("content") or ""

    def answer(
        self,
        question: str,
        chunks: list[tuple[Chunk, float]],
        history: list[dict],
    ) -> Answer:
        if not chunks:
            return Answer(
                text="I could not find relevant information in the ingested videos.",
                citations=[],
                found_relevant_content=False,
            )

        # Build context
        context = "\n\n---\n\n".join(
            f"[{c.video_title} | {c.timestamp_label}]\n{c.text}"
            for c, _ in chunks
        )
        prompt = f"Context from videos:\n\n{context}\n\nQuestion: {question}"

        # Build messages: system + history + current question
        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

        for turn in history[-config.CONVERSATION_HISTORY_TURNS:]:
            role = "assistant" if turn["role"] == "assistant" else "user"
            msg: dict = {"role": role, "content": turn.get("content", "")}
            # Preserve reasoning_details for multi-turn reasoning continuity
            if role == "assistant" and turn.get("reasoning_details"):
                msg["reasoning_details"] = turn["reasoning_details"]
            messages.append(msg)

        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": config.OPENROUTER_MODEL,
            "messages": messages,
            "reasoning": {"enabled": True},
        }

        response = self._http.post(
            self._API_URL, headers=self._headers, json=payload
        )
        response.raise_for_status()
        data = response.json()
        msg_out = data["choices"][0]["message"]
        answer_text: str = msg_out.get("content") or ""

        return Answer(
            text=answer_text,
            citations=_filter_citations(answer_text, chunks),
            raw_chunks=chunks,
        )
