"""
Ingestion UI Component
======================
URL input panel with:
- Text input for YouTube URLs
- Ingest button with live progress bar
- List of ingested sources with summary/remove buttons
"""

from __future__ import annotations

import logging

import streamlit as st

from core.ingestion import ingest_url
from core.retriever import generate_intro
from core.source_store import delete_source_record, load_sources, save_source

logger = logging.getLogger(__name__)


def _trigger_summary(source, services: dict) -> None:
    """Generate intro for a source and store it, clearing chat history."""
    with st.spinner("✨ Generating summary..."):
        intro_data = generate_intro(
            source=source,
            embedding_service=services["embedding"],
            vector_store=services["vector_store"],
            llm_service=services["llm"],
        )
    logger.info(
        "Intro generated — intro: %s | topics: %s | questions: %s",
        bool(intro_data.get("intro")),
        intro_data.get("topics"),
        intro_data.get("questions"),
    )
    st.session_state.pending_intro = intro_data
    st.session_state.chat_history = []
    st.rerun()


def render_ingestion(services: dict) -> None:
    """Render the ingestion panel — URL input, progress, and source list."""

    # ── Header ──────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="margin-bottom: 1rem;">
            <h2 style="
                margin: 0; font-weight: 700;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            ">📥 Add Content</h2>
            <p style="margin: 0.25rem 0 0 0; font-size: 0.85rem; opacity: 0.6;">
                Paste a YouTube URL to ingest
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── URL Input ───────────────────────────────────────────────────
    url = st.text_input(
        "YouTube URL",
        placeholder="Paste a video, playlist, or channel URL...",
        label_visibility="collapsed",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("🎬 Single video")
    with col2:
        st.caption("📋 Playlist")
    with col3:
        st.caption("📺 Channel")

    # ── Ingest Button ───────────────────────────────────────────────
    if st.button("🚀 Ingest", type="primary", disabled=not url, use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()

        def on_progress(current: int, total: int, message: str) -> None:
            pct = int((current / max(total, 1)) * 100)
            progress_bar.progress(pct)
            status_text.text(f"{message} ({current}/{total})")

        try:
            source = ingest_url(
                url=url,
                kb_id=st.session_state.active_kb_id,
                embedding_service=services["embedding"],
                vector_store=services["vector_store"],
                progress_callback=on_progress,
            )
            save_source(source)
            st.session_state.sources = load_sources(st.session_state.active_kb_id)
            st.success(f"✅ Done! {source.chunk_count} chunks from {source.video_count} video(s).")
            _trigger_summary(source, services)  # auto-generates and reruns

        except ValueError as exc:
            st.error(f"❌ Invalid URL: {exc}")
        except NotImplementedError as exc:
            st.warning(f"⚠️ {exc}")
        except Exception as exc:
            st.error(f"❌ Ingestion failed: {exc}")

    # ── Ingested Sources List ───────────────────────────────────────
    sources = [
        s for s in st.session_state.get("sources", [])
        if s.kb_id == st.session_state.active_kb_id
    ]

    if sources:
        st.divider()
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:0.5rem;">
                <span style="font-weight:600; font-size:0.9rem;">📚 Ingested Sources</span>
                <span style="
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white; padding: 0.15rem 0.6rem;
                    border-radius: 12px; font-size: 0.75rem; font-weight: 600;
                ">{len(sources)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for source in sources:
            with st.expander(f"🎥 {source.title}", expanded=False):
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Videos", source.video_count)
                with c2:
                    st.metric("Chunks", source.chunk_count)

                status_colors = {
                    "complete": "#28a745",
                    "processing": "#ffc107",
                    "failed": "#dc3545",
                    "pending": "#6c757d",
                }
                color = status_colors.get(source.status.value, "#6c757d")
                st.markdown(
                    f'<span style="color:{color}; font-size:0.8rem;">● {source.status.value.upper()}</span>',
                    unsafe_allow_html=True,
                )

                st.markdown("<br/>", unsafe_allow_html=True)

                # ── Summary button ──────────────────────────────────
                if st.button(
                    "✨ Show Summary",
                    key=f"summary_{source.id}",
                    use_container_width=True,
                ):
                    _trigger_summary(source, services)

                # ── Remove button ───────────────────────────────────
                if st.button(
                    "🗑️ Remove",
                    key=f"del_{source.id}",
                    use_container_width=True,
                ):
                    services["vector_store"].delete_source(source.id, source.kb_id)
                    delete_source_record(source.id)
                    st.session_state.sources = load_sources(st.session_state.active_kb_id)
                    if st.session_state.get("pending_intro"):
                        st.session_state.pending_intro = None
                    st.rerun()
    else:
        st.markdown(
            """
            <div style="text-align:center; padding:2rem 1rem; opacity:0.5; font-size:0.9rem;">
                <div style="font-size:2.5rem; margin-bottom:0.5rem;">📭</div>
                No content ingested yet.<br/>Paste a YouTube URL above to get started!
            </div>
            """,
            unsafe_allow_html=True,
        )
