"""
TubeQuery — Main Application Entry Point
==========================================
Run with:  ``streamlit run app.py``

Initialises all services (cached across reruns), sets up session
state, applies custom theming, and composes the UI from components.
"""

import logging
import os

import streamlit as st

import config
from core.source_store import load_sources
from services.embedding_service import MiniLMEmbeddingService
from services.llm_service import GeminiLLMService, OpenRouterLLMService
from services.vector_store import ChromaVectorStore
from ui.chat import render_chat
from ui.ingestion_ui import render_ingestion
from ui.sidebar import render_sidebar

# ── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Page Config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="TubeQuery — YouTube RAG Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS Theme ────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Import Google Font ──────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Root Variables ──────────────────────────────────────── */
    :root {
        --accent-primary: #667eea;
        --accent-secondary: #764ba2;
        --surface-elevated: rgba(255, 255, 255, 0.03);
        --border-subtle: rgba(255, 255, 255, 0.06);
        --radius-lg: 12px;
        --radius-md: 8px;
    }

    /* ── Global Typography ───────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* ── Main Container ──────────────────────────────────────── */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1400px;
    }

    /* ── Sidebar Styling ─────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg,
            rgba(102, 126, 234, 0.05) 0%,
            rgba(118, 75, 162, 0.05) 100%
        );
        border-right: 1px solid var(--border-subtle);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        font-size: 0.9rem;
    }

    /* ── Chat Messages ───────────────────────────────────────── */
    [data-testid="stChatMessage"] {
        border-radius: var(--radius-lg) !important;
        border: 1px solid var(--border-subtle) !important;
        padding: 1rem !important;
        margin-bottom: 0.75rem !important;
        backdrop-filter: blur(10px);
    }

    /* ── Buttons ──────────────────────────────────────────────── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.25) !important;
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }

    .stButton > button {
        border-radius: var(--radius-md) !important;
        transition: all 0.2s ease !important;
    }

    /* ── Text Input ──────────────────────────────────────────── */
    .stTextInput > div > div > input {
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--border-subtle) !important;
        transition: border-color 0.2s ease !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15) !important;
    }

    /* ── Select Box ──────────────────────────────────────────── */
    .stSelectbox > div > div {
        border-radius: var(--radius-md) !important;
    }

    /* ── Expander ────────────────────────────────────────────── */
    .streamlit-expanderHeader {
        border-radius: var(--radius-md) !important;
        font-weight: 500 !important;
    }

    /* ── Progress Bar ────────────────────────────────────────── */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary)) !important;
        border-radius: 4px !important;
    }

    /* ── Divider ─────────────────────────────────────────────── */
    hr {
        border-color: var(--border-subtle) !important;
        opacity: 0.5 !important;
    }

    /* ── Metrics ─────────────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: var(--surface-elevated);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 0.75rem;
    }

    [data-testid="stMetricValue"] {
        font-weight: 700 !important;
        color: var(--accent-primary) !important;
    }

    /* ── Chat Input ──────────────────────────────────────────── */
    [data-testid="stChatInput"] textarea {
        border-radius: var(--radius-lg) !important;
    }

    /* ── Smooth Animations ───────────────────────────────────── */
    .stButton > button,
    .stTextInput > div > div > input,
    [data-testid="stChatMessage"],
    .streamlit-expanderHeader {
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    /* ── Scrollbar ───────────────────────────────────────────── */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(102, 126, 234, 0.3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(102, 126, 234, 0.5);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Create Data Directories ────────────────────────────────────────
os.makedirs(config.CHROMA_DIR, exist_ok=True)
os.makedirs(config.DATA_DIR, exist_ok=True)


# ── Initialise Services (cached across Streamlit reruns) ───────────
@st.cache_resource
def _init_services() -> dict:
    """Load all services once and cache them for the session."""
    logger.info("Initialising TubeQuery services...")
    llm = OpenRouterLLMService() if config.LLM_PROVIDER == "openrouter" else GeminiLLMService()
    return {
        "embedding": MiniLMEmbeddingService(),
        "vector_store": ChromaVectorStore(),
        "llm": llm,
    }


services = _init_services()

# ── Session State Defaults ─────────────────────────────────────────
if "active_kb_id" not in st.session_state:
    st.session_state.active_kb_id = "default"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "sources" not in st.session_state:
    st.session_state.sources = load_sources()
if "pending_intro" not in st.session_state:
    st.session_state.pending_intro = None
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ── Layout ──────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar(services)

col_chat, col_ingest = st.columns([2, 1], gap="large")

with col_chat:
    render_chat(services)

with col_ingest:
    render_ingestion(services)
