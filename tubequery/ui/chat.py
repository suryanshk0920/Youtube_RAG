"""
Chat Component
==============
"""

from __future__ import annotations

import streamlit as st

from core.retriever import ask


def _strip_sources_block(text: str) -> str:
    """Remove the SOURCES: section from LLM answer text — we render it ourselves."""
    import re
    return re.sub(r"\n*SOURCES:\s*\n(?:\s*-[^\n]*\n?)*", "", text, flags=re.IGNORECASE).strip()


def _process_question(question: str, services: dict) -> None:
    """Run the full ask pipeline and append results to chat history."""
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching & generating answer..."):
            answer = ask(
                question=question,
                kb_id=st.session_state.active_kb_id,
                embedding_service=services["embedding"],
                vector_store=services["vector_store"],
                llm_service=services["llm"],
                history=st.session_state.chat_history,
            )

        chunk_count = services["vector_store"].count(st.session_state.active_kb_id)
        if chunk_count == 0:
            st.warning("⚠️ No chunks in this KB. Ingest a video first.")
        elif not answer.found_relevant_content:
            st.info(f"ℹ️ {chunk_count} chunks indexed but none matched. Try rephrasing.")

        st.markdown(_strip_sources_block(answer.text))
        if answer.citations:
            _render_citations(answer.citations)

    st.session_state.chat_history.append({"role": "user", "content": question})
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": _strip_sources_block(answer.text),
        "citations": [
            {
                "video_title": c.video_title,
                "video_id": c.video_id,
                "timestamp_label": c.timestamp_label,
                "youtube_url": c.youtube_url,
                "excerpt": c.excerpt,
            }
            for c in (answer.citations or [])
        ],
    })


def render_chat(services: dict) -> None:
    """Render the chat panel with history, input, and citations."""

    st.markdown(
        """
        <div style="margin-bottom: 1rem;">
            <h2 style="
                margin: 0; font-weight: 700;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            ">💬 Chat</h2>
            <p style="margin: 0.25rem 0 0 0; font-size: 0.85rem; opacity: 0.6;">
                Ask anything about your ingested videos
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Render existing chat history ────────────────────────────────
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("citations"):
                _render_citations(message["citations"])

    # ── Intro card (shown whenever pending, clears chat for fresh start) ──
    pending_intro = st.session_state.get("pending_intro")
    if pending_intro:
        with st.chat_message("assistant"):
            st.markdown(f"🎬 **About this video**\n\n{pending_intro['intro']}")

            topics = pending_intro.get("topics", [])
            if topics:
                st.markdown("**Topics covered:**")
                for topic in topics:
                    st.markdown(f"• {topic}")

            questions = pending_intro.get("questions", [])
            if questions:
                st.markdown("**Suggested questions:**")
                cols = st.columns(len(questions))
                for i, q in enumerate(questions):
                    with cols[i]:
                        if st.button(q, key=f"sq_{i}", use_container_width=True):
                            st.session_state.pending_intro = None
                            _process_question(q, services)
                            st.rerun()
                        return

    # ── Chat input ──────────────────────────────────────────────────
    question = st.chat_input("Ask anything about your ingested videos...")
    if question:
        st.session_state.pending_intro = None
        _process_question(question, services)
        st.rerun()

    # ── Clear chat ──────────────────────────────────────────────────
    if st.session_state.chat_history:
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("🗑️ Clear conversation", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.pending_intro = None
            st.rerun()


def _render_citations(citations) -> None:
    if not citations:
        return
    # Show only the primary citation (first/best match)
    c = citations[0]
    if isinstance(c, dict):
        title, label, url = c["video_title"], c["timestamp_label"], c["youtube_url"]
    else:
        title, label, url = c.video_title, c.timestamp_label, c.youtube_url
    st.markdown(f"[📍 {title} @ {label}]({url})")
