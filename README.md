# TubeQuery — Developer Setup Guide

TubeQuery is a YouTube RAG (Retrieval-Augmented Generation) platform. Users add YouTube videos, and the system lets them have AI-powered conversations with the content — with precise timestamp citations.

**Stack**: Next.js (frontend) + FastAPI (backend) + ChromaDB (vectors) + Supabase (database) + Firebase (auth) + Upstash Redis (rate limiting)

---

## Prerequisites

Before you start, make sure you have:

- **Python 3.11+** — `python --version`
- **Node.js 18+** — `node --version`
- **Git** — `git --version`
- Accounts on: [Supabase](https://supabase.com), [Firebase](https://firebase.google.com), [Upstash](https://upstash.com), [Google AI Studio](https://aistudio.google.com) or [OpenRouter](https://openrouter.ai), [Google Cloud Console](https://console.cloud.google.com)

---

## Project Structure

```
YouTube_RAG/
├── tubequery/          ← Python FastAPI backend
│   ├── api/            ← Route handlers, auth, schemas
│   ├── core/           ← RAG pipeline (ingestion, retrieval, chunking)
│   ├── services/       ← LLM, embeddings, vector store, Redis
│   ├── middleware/      ← Rate limiting
│   ├── models/         ← Data models
│   ├── migrations/     ← SQL migration files
│   ├── config.py       ← All configuration (reads from .env)
│   ├── requirements.txt
│   └── .env            ← Backend secrets (never commit)
│
└── tubequery-ui/       ← Next.js frontend
    ├── app/            ← Pages (Next.js App Router)
    ├── components/     ← React components
    ├── context/        ← Auth context
    ├── lib/            ← API client
    ├── types/          ← TypeScript types
    └── .env.local      ← Frontend secrets (never commit)
```

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/suryanshk0920/Youtube_RAG.git
cd YouTube_RAG
```

---

## Step 2: Set Up External Services

You need to configure 5 external services before running anything locally. Do these first.

### 2a. Supabase (Database)

1. Go to [supabase.com](https://supabase.com) → New project
2. Note down:
   - **Project URL**: `https://xxxx.supabase.co`
   - **Anon Key**: found in Settings → API
   - **Service Role Key**: found in Settings → API (keep this secret)
3. Go to **SQL Editor** and run the full schema:
   - Open `tubequery/migrations/setup_proper_schema.sql`
   - Paste the entire file into the SQL Editor and run it
   - This creates all tables, indexes, and helper functions

### 2b. Firebase (Authentication)

1. Go to [Firebase Console](https://console.firebase.google.com) → New project
2. Enable **Authentication** → Sign-in method → Enable **Google** and **Email/Password**
3. Get your **Web App config**:
   - Project Settings → General → Your apps → Add app (Web)
   - Copy the config object (you'll need `apiKey`, `authDomain`, `projectId`, `appId`)
4. Get your **Service Account** (for backend):
   - Project Settings → Service Accounts → Generate New Private Key
   - Download the JSON file → save it as `tubequery/firebase-service-account.json`
   - ⚠️ Never commit this file — it's already in `.gitignore`

### 2c. Upstash Redis (Rate Limiting)

1. Go to [upstash.com](https://upstash.com) → Create Database
2. Choose **Redis** → Region closest to you → Free tier is fine
3. Note down:
   - **UPSTASH_REDIS_URL**: `rediss://...` (from REST API section)
   - **UPSTASH_REDIS_TOKEN**: the token shown in the dashboard
   - **UPSTASH_REDIS_REST_URL**: the REST URL (starts with `https://`)

### 2d. LLM API — Choose One

**Option A: OpenRouter (recommended, has free models)**
1. Go to [openrouter.ai](https://openrouter.ai) → Get API key
2. Free models available: set `OPENROUTER_MODEL=openrouter/auto`

**Option B: Google Gemini**
1. Go to [aistudio.google.com](https://aistudio.google.com) → Get API key
2. Free tier: 15 requests/minute

### 2e. YouTube Data API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → Enable **YouTube Data API v3**
3. Credentials → Create API Key
4. Note down the key

---

## Step 3: Configure the Backend

```bash
cd tubequery
cp .env.example .env
```

Edit `.env` with your values:

```bash
# ── LLM ─────────────────────────────────────────────────────────────
# Choose one provider:
LLM_PROVIDER=openrouter          # or "gemini"

OPENROUTER_API_KEY=sk-or-...     # from openrouter.ai
OPENROUTER_MODEL=openrouter/auto # or a specific model like "anthropic/claude-3-haiku"

GEMINI_API_KEY=AIza...           # from aistudio.google.com (only if using gemini)

# ── YouTube ──────────────────────────────────────────────────────────
YOUTUBE_API_KEY=AIza...          # from Google Cloud Console

# ── Supabase ─────────────────────────────────────────────────────────
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # service role key (NOT anon key)

# ── Redis (Upstash) ──────────────────────────────────────────────────
UPSTASH_REDIS_URL=rediss://...
UPSTASH_REDIS_TOKEN=your_token
UPSTASH_REDIS_REST_URL=https://...

# ── Firebase ─────────────────────────────────────────────────────────
# Option A: point to the JSON file (recommended)
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json

# Option B: paste the JSON as a single line with \n for newlines
# FIREBASE_SERVICE_ACCOUNT={"type":"service_account","project_id":"..."}

# ── Storage paths (defaults are fine) ───────────────────────────────
DATA_DIR=./data
CHROMA_DIR=./data/chromadb
```

---

## Step 4: Run the Backend

```bash
# From the tubequery/ directory

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Install dependencies (takes 2-5 minutes — torch is large)
pip install -r requirements.txt

# Start the API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
✅ Redis service initialized successfully
📁 Data directories created
🎉 TubeQuery API startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Verify it's working:
```bash
curl http://localhost:8000/health
# → {"status":"ok","version":"1.0.0"}

curl http://localhost:8000/docs
# → Opens Swagger UI in browser
```

---

## Step 5: Configure the Frontend

```bash
cd tubequery-ui
cp .env.example .env.local
```

Edit `.env.local`:

```bash
# Backend URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Firebase Web Config (from Firebase Console → Project Settings → General → Your apps)
NEXT_PUBLIC_FIREBASE_API_KEY=AIza...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_APP_ID=1:xxx:web:xxx
```

---

## Step 6: Run the Frontend

```bash
# From the tubequery-ui/ directory

npm install

npm run dev
```

You should see:
```
▲ Next.js 14.x.x
- Local: http://localhost:3000
- Ready in 2.1s
```

Open [http://localhost:3000](http://localhost:3000) — you should see the TubeQuery interface.

---

## Step 7: Verify the Full Flow

1. **Sign in** with Google (Firebase auth)
2. **Add a video** — paste any YouTube URL like `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
3. **Wait** for processing (~15-30 seconds for a 5-minute video)
4. **Ask a question** about the video
5. **Verify** you get a response with a timestamp citation

If all 5 steps work, your local setup is complete.

---

## Common Issues

### Backend won't start

**`ModuleNotFoundError`**
```bash
# Make sure your virtual environment is activated
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # macOS/Linux

# Then reinstall
pip install -r requirements.txt
```

**`RuntimeError: Firebase service account not configured`**
- Check that `firebase-service-account.json` exists in `tubequery/`
- Or that `FIREBASE_SERVICE_ACCOUNT_PATH` in `.env` points to the correct file

**`RuntimeError: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set`**
- Check your `.env` file has both values
- Make sure you're using the **Service Role Key**, not the Anon Key

**`ValueError: GEMINI_API_KEY is not set`**
- If using Gemini: add `GEMINI_API_KEY` to `.env`
- If using OpenRouter: make sure `LLM_PROVIDER=openrouter` in `.env`

### Frontend won't start

**`npm install` fails**
```bash
# Try clearing cache
npm cache clean --force
npm install
```

**Sign in doesn't work**
- Check all `NEXT_PUBLIC_FIREBASE_*` variables are set in `.env.local`
- Verify Google sign-in is enabled in Firebase Console → Authentication

**API calls fail (CORS or network error)**
- Make sure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local`

### Video ingestion fails

**`Could not retrieve transcript`**
- Some videos have transcripts disabled — try a different video
- Educational/tech videos usually work well

**`Playlist ingestion blocked`**
- Playlist ingestion is a Pro-only feature
- Test with a single video URL first

---

## Environment Variables Reference

### Backend (`tubequery/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_PROVIDER` | Yes | `openrouter` or `gemini` |
| `OPENROUTER_API_KEY` | If using OpenRouter | API key from openrouter.ai |
| `OPENROUTER_MODEL` | No | Default: `openrouter/auto` |
| `GEMINI_API_KEY` | If using Gemini | API key from aistudio.google.com |
| `YOUTUBE_API_KEY` | Yes | YouTube Data API v3 key |
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key |
| `UPSTASH_REDIS_URL` | Yes | Upstash Redis connection URL |
| `UPSTASH_REDIS_TOKEN` | Yes | Upstash Redis auth token |
| `UPSTASH_REDIS_REST_URL` | Yes | Upstash REST API URL |
| `FIREBASE_SERVICE_ACCOUNT_PATH` | Yes* | Path to Firebase JSON file |
| `FIREBASE_SERVICE_ACCOUNT` | Yes* | Firebase JSON as string (alternative) |
| `DATA_DIR` | No | Default: `./data` |
| `CHROMA_DIR` | No | Default: `./data/chromadb` |

*One of the two Firebase options is required.

### Frontend (`tubequery-ui/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend URL (default: `http://localhost:8000`) |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Yes | Firebase web API key |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Yes | Firebase auth domain |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | Yes | Firebase project ID |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | Yes | Firebase app ID |

---

## Database Schema

The schema is in `tubequery/migrations/setup_proper_schema.sql`. Run it once in Supabase SQL Editor.

Key tables:
- `user_profiles` — user accounts (uid from Firebase)
- `knowledge_bases` — each user's video libraries
- `sources` — individual videos/playlists added by users
- `chat_sessions` — conversation history per video
- `user_subscriptions` — free/pro plan tracking
- `daily_usage` — usage counters that reset at midnight UTC
- `usage_logs` — permanent audit log

---

## Architecture Overview

```
User → Next.js (Vercel) → FastAPI (Render/local)
                               ↓
                    ┌──────────┴──────────┐
                    │                     │
               Supabase              ChromaDB
               (users, sessions,     (video embeddings,
                subscriptions)        vector search)
                    │
               Upstash Redis
               (rate limiting,
                usage tracking)
                    │
            ┌───────┴────────┐
            │                │
       OpenRouter/Gemini   YouTube API
       (LLM responses)     (transcripts)
```

**Request flow for a chat message:**
1. Frontend sends question + auth token to `POST /chat/stream`
2. Backend verifies Firebase JWT
3. Rate limit check via Redis (~5ms)
4. Question embedded via MiniLM model (~50ms)
5. Vector search in ChromaDB for relevant chunks (~20ms)
6. Chunks + question sent to LLM (OpenRouter/Gemini) (~1-3s)
7. Response streamed back via Server-Sent Events
8. Usage counter incremented in Redis

---

## Running Tests

```bash
# From tubequery/ directory (with venv activated)

# Test URL security validation
python test_url_security.py

# Test playlist API restrictions
python test_playlist_api.py

# Test playlist restriction enforcement
python test_playlist_restriction.py
```

---

## Upgrading a User to Pro (for testing)

```bash
# From tubequery/ directory (with venv activated)
python upgrade_user_simple.py
```

Follow the prompts to enter a user's email and upgrade them to Pro. This lets you test playlist ingestion and other Pro features.

---

## Key Configuration Values

From `config.py` — these control RAG behavior:

| Setting | Value | Description |
|---------|-------|-------------|
| `CHUNK_SIZE` | 80 words | Size of each transcript chunk |
| `CHUNK_OVERLAP` | 15 words | Overlap between chunks |
| `TOP_K` | 8 | Chunks retrieved per query |
| `MIN_RELEVANCE_SCORE` | 0.0 | Minimum similarity score (0 = accept all) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Local sentence-transformers model |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model version |
| `CONVERSATION_HISTORY_TURNS` | 10 | How many past messages sent to LLM |

---

## Deployment

See `PRODUCTION_DEPLOYMENT_GUIDE.md` for full deployment instructions.

**Quick summary:**
- **Backend**: Deploy to Render (Starter plan, $7/month — free tier runs out of memory)
- **Frontend**: Deploy to Vercel (free tier is fine)
- **Database**: Supabase (free tier is fine for early stage)
- **Redis**: Upstash (free tier is fine)
- **Firebase**: Free tier is fine

**Critical for production:**
- Use Render's **Secret Files** to upload `firebase-service-account.json`
- Set `FIREBASE_SERVICE_ACCOUNT_PATH=/etc/secrets/firebase-service-account.json`
- Never commit the Firebase service account JSON to Git

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test locally using the steps above
5. Push and open a pull request

---

## Need Help?

- Check the `ARCHITECTURE.md` for a deep dive into how the system works
- Check `PRODUCTION_DEPLOYMENT_GUIDE.md` for deployment issues
- Check `HOSTING_AND_PRICING_GUIDE.md` for cost and hosting options
