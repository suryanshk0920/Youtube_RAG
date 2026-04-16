"""
Sidebar Component
=================
Knowledge base switcher. Lets the user create named knowledge bases
(e.g. Health, Tech, Finance) and switch between them. Each KB is
fully isolated — switching clears the chat history.
"""

from __future__ import annotations

import streamlit as st

# Pre-defined knowledge base categories
DEFAULT_KBS: list[str] = ["default", "health", "tech", "finance"]


def render_sidebar(services: dict) -> None:
    """Render the sidebar with KB selector, stats, and branding."""

    # ── Branding ────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center; padding: 0.5rem 0 1rem 0;">
            <span style="font-size: 2.5rem;">🎬</span>
            <h1 style="
                margin: 0.25rem 0 0 0;
                font-size: 1.75rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 800;
            ">TubeQuery</h1>
            <p style="
                margin: 0;
                font-size: 0.85rem;
                opacity: 0.6;
            ">YouTube RAG Assistant</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Knowledge Base Selector ─────────────────────────────────────
    st.markdown("##### 📚 Knowledge Base")

    # Custom KB input
    new_kb = st.text_input(
        "Create new KB",
        placeholder="e.g. cooking, science...",
        label_visibility="collapsed",
    )
    if new_kb and new_kb.strip():
        kb_name = new_kb.strip().lower().replace(" ", "_")
        if kb_name not in DEFAULT_KBS:
            if "custom_kbs" not in st.session_state:
                st.session_state.custom_kbs = []
            if kb_name not in st.session_state.custom_kbs:
                st.session_state.custom_kbs.append(kb_name)
                st.toast(f"Created KB: **{kb_name}**", icon="✅")

    # Merge default + custom KBs
    custom_kbs = st.session_state.get("custom_kbs", [])
    kb_options = DEFAULT_KBS + [k for k in custom_kbs if k not in DEFAULT_KBS]

    current_index = (
        kb_options.index(st.session_state.active_kb_id)
        if st.session_state.active_kb_id in kb_options
        else 0
    )

    selected = st.selectbox(
        "Active KB",
        options=kb_options,
        index=current_index,
        format_func=lambda x: f"📁 {x.replace('_', ' ').title()}",
    )

    if selected != st.session_state.active_kb_id:
        st.session_state.active_kb_id = selected
        st.session_state.chat_history = []
        st.rerun()

    # ── Stats ───────────────────────────────────────────────────────
    chunk_count = services["vector_store"].count(
        st.session_state.active_kb_id
    )

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #667eea22, #764ba222);
            border-radius: 10px;
            padding: 1rem;
            margin: 0.75rem 0;
            text-align: center;
            border: 1px solid rgba(102, 126, 234, 0.2);
        ">
            <div style="font-size: 1.75rem; font-weight: 700; color: #667eea;">
                {chunk_count:,}
            </div>
            <div style="font-size: 0.8rem; opacity: 0.7;">chunks indexed</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Tips ────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            padding: 0.75rem;
            font-size: 0.8rem;
            opacity: 0.65;
            line-height: 1.5;
        ">
            💡 <b>Tips</b><br/>
            • Each KB is isolated — switch KBs to search different content.<br/>
            • Paste a playlist URL to ingest multiple videos at once.<br/>
            • Questions use multi-turn context for follow-ups.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Danger Zone ─────────────────────────────────────────────────
    with st.expander("⚠️ Reset Data", expanded=False):
        st.caption("Wipes all vectors and source records for a clean start.")
        if st.button("🗑️ Reset All Data", use_container_width=True, type="primary"):
            import shutil, os, json
            # Close ChromaDB client first so files are released
            try:
                services["vector_store"]._client.reset()
            except Exception:
                pass
            # Wipe chromadb folder
            chroma_path = __import__("config").CHROMA_DIR
            if os.path.exists(chroma_path):
                shutil.rmtree(chroma_path, ignore_errors=True)
            # Wipe sources.json
            sources_path = __import__("config").SOURCES_FILE
            if os.path.exists(sources_path):
                os.remove(sources_path)
            # Clear session state
            st.session_state.sources = []
            st.session_state.chat_history = []
            st.session_state.pending_intro = None
            st.toast("All data wiped. Ready for fresh ingestion.", icon="✅")
            st.rerun()
