# TubeQuery 🎬

**Ask questions about any YouTube video using AI.**

Paste a YouTube URL, ingest the transcript, and chat with the content. Get answers with timestamped citations that link directly to the exact moment in the video.

---

## What it does

- Ingest any YouTube video, playlist, or channel
- Ask natural language questions about the content
- Get answers grounded in the transcript with clickable timestamp links
- Maintain multi-turn conversations with follow-up questions
- Organise content into separate knowledge bases (e.g. Tech, Health, Finance)
- Auto-generates a summary and suggested questions after each ingestion

## Tech stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Embeddings | `all-MiniLM-L6-v2` (runs locally) |
| Vector store | ChromaDB (runs locally) |
| LLM | OpenRouter (any model) or Google Gemini |
| Transcripts | `youtube-transcript-api` |

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/suryanshk0920/Youtube_RAG.git
cd Youtube_RAG/tubequery
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> First run downloads the MiniLM embedding model (~90MB) to `~/.cache/huggingface/`.

### 3. Configure API keys

Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

Open `.env` and set:

```env
# Required for answering questions
OPENROUTER_API_KEY=your_key_here       # https://openrouter.ai/keys

# Required for playlist ingestion only
YOUTUBE_API_KEY=your_key_here          # https://console.cloud.google.com

# Optional — defaults shown
OPENROUTER_MODEL=openrouter/auto
LLM_PROVIDER=openrouter
DATA_DIR=./data
CHROMA_DIR=./data/chromadb
```

> Single video ingestion works without a YouTube API key. You only need it for playlists.

### 4. Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## How to use

### Ingest a video

1. Paste a YouTube URL into the **Add Content** panel on the right
2. Click **🚀 Ingest**
3. Wait for the transcript to be fetched, chunked, and embedded
4. A summary and suggested questions appear automatically in the chat

### Ask questions

- Type any question in the chat input
- The app retrieves the most relevant transcript chunks and generates an answer
- A timestamped link appears below the answer — click it to jump to that moment in the video

### Knowledge bases

- Use the sidebar to switch between knowledge bases
- Each KB is fully isolated — ingest different topics into different KBs
- Create a custom KB by typing a name in the sidebar input

### Reset data

Use the **⚠️ Reset Data** expander at the bottom of the sidebar to wipe all vectors and source records cleanly.

---

## Project structure

```
tubequery/
├── app.py                      # Streamlit entry point
├── config.py                   # All settings and constants
├── requirements.txt
│
├── core/                       # Pipeline logic
│   ├── youtube.py              # URL parsing + transcript fetching
│   ├── chunker.py              # Transcript → overlapping chunks
│   ├── ingestion.py            # Full ingestion orchestrator
│   ├── retriever.py            # Question → answer pipeline + intro generation
│   └── source_store.py         # JSON metadata persistence
│
├── services/                   # Swappable interfaces
│   ├── embedding_service.py    # MiniLM (local)
│   ├── vector_store.py         # ChromaDB (local)
│   └── llm_service.py          # OpenRouter / Gemini
│
├── models/                     # Data classes
│   ├── chunk.py
│   ├── source.py
│   └── answer.py
│
└── ui/                         # Streamlit components
    ├── sidebar.py
    ├── chat.py
    └── ingestion_ui.py
```

## Swapping components

Every service sits behind an abstract interface. To swap a component, create a new class inheriting the base and update `app.py`:

| Component | Current | Interface |
|---|---|---|
| Embeddings | MiniLM (local) | `EmbeddingService` |
| Vector store | ChromaDB (local) | `VectorStore` |
| LLM | OpenRouter | `LLMService` |

---
