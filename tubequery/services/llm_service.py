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
You are an expert assistant that answers questions based ONLY on the provided video transcript excerpts.

RULES:
1. Only use information from the provided context excerpts.
2. If the context does not contain enough information, say: "I could not find relevant information in the ingested videos."
3. Never make up information not present in the excerpts.
4. Only cite sources you genuinely drew from.

FORMATTING:
- Do NOT start with "Answer:" — just begin your response directly.
- Start with a 1-2 sentence direct answer.
- Use bullet points to break down details.
- Use **bold** for key terms.
- Aim for 150-300 words.
- End with a SOURCES section. Use EXACTLY this format, no brackets, no pipes:
  SOURCES:
  - Video Title at MM:SS
  - Video Title at MM:SS
"""


def _filter_citations(
    answer_text: str,
    chunks: list[tuple[Chunk, float]],
) -> list[Citation]:
    """
    Build citations. Tries SOURCES block parsing first, always falls back
    to top-scoring chunk so there is always at least one citation.
    """
    import re

    def make_citation(chunk: Chunk) -> Citation:
        return Citation(
            video_title=chunk.video_title,
            video_id=chunk.video_id,
            timestamp_label=chunk.timestamp_label,
            youtube_url=chunk.youtube_url,
            excerpt=chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
        )

    sources_match = re.search(r"SOURCES:\s*\n((?:\s*-[^\n]+\n?)+)", answer_text, re.IGNORECASE)
    matched: list[Citation] = []

    if sources_match:
        for line in sources_match.group(1).splitlines():
            line = line.strip().lstrip("- ").strip().strip("[]")
            if not line:
                continue
            for chunk, _ in chunks:
                ts = chunk.timestamp_label  # e.g. "1:39"
                title_frag = chunk.video_title.lower()[:20]
                line_lower = line.lower()
                # Timestamp match is most specific — try it first
                if ts and ts in line:
                    matched.append(make_citation(chunk))
                    break
                # Fall back to title fragment
                if title_frag and title_frag in line_lower:
                    matched.append(make_citation(chunk))
                    break

    # Deduplicate
    seen: set[str] = set()
    unique: list[Citation] = []
    for c in matched:
        key = f"{c.video_id}_{c.timestamp_label}"
        if key not in seen:
            seen.add(key)
            unique.append(c)

    # Always return at least the top-scoring chunk
    if not unique and chunks:
        unique.append(make_citation(max(chunks, key=lambda x: x[1])[0]))

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

    def stream_answer(
        self,
        question: str,
        chunks: list[tuple[Chunk, float]],
        history: list[dict],
    ):
        """
        Stream answer tokens as a generator of strings.
        Default falls back to yielding the full answer at once.
        Override in subclasses for real token streaming.
        """
        answer = self.answer(question=question, chunks=chunks, history=history)
        yield answer.text


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

    def stream_answer(
        self,
        question: str,
        chunks: list[tuple[Chunk, float]],
        history: list[dict],
    ):
        """
        Get full answer from OpenRouter (blocking), then yield it word by word.
        This avoids SSE parsing issues with partial TCP chunks.
        """
        if not chunks:
            yield "I could not find relevant information in the ingested videos."
            return

        context = "\n\n---\n\n".join(
            f"[{c.video_title} | {c.timestamp_label}]\n{c.text}"
            for c, _ in chunks
        )
        prompt = f"Context from videos:\n\n{context}\n\nQuestion: {question}"

        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        for turn in history[-config.CONVERSATION_HISTORY_TURNS:]:
            role = "assistant" if turn["role"] == "assistant" else "user"
            msg: dict = {"role": role, "content": turn.get("content", "")}
            if role == "assistant" and turn.get("reasoning_details"):
                msg["reasoning_details"] = turn["reasoning_details"]
            messages.append(msg)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": config.OPENROUTER_MODEL,
            "messages": messages,
        }

        # Blocking call — get full response
        response = self._http.post(
            self._API_URL, headers=self._headers, json=payload
        )
        response.raise_for_status()
        full_text = response.json()["choices"][0]["message"].get("content", "")

        # Yield word by word for streaming effect in the UI
        import re
        tokens = re.split(r'(\s+)', full_text)
        for token in tokens:
            if token:
                yield token

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
