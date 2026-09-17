# 🎥 AI YouTube Video Summarizer

An AI-powered web app that turns any YouTube video into a structured, queryable knowledge base — not just a summary. Paste a link, pick a summary style, and get a timestamped breakdown you can chat with and search by meaning, all saved to your personal history.

Built as a placement portfolio project to demonstrate production-style backend design (async job processing, JWT auth, RAG) on top of a real LLM pipeline — not just "call an API and print the response."

---

## ✨ Features

- **Adaptive summaries** — Choose Beginner, Technical, Quick Revision, or Interview Prep, and the prompt *and* the output schema adapt. Interview Prep adds a dedicated list of likely interview questions.
- **Chat with the Video** — Ask questions in plain language and get answers grounded strictly in the transcript, with clickable timestamp citations back to the exact moment. Uses RAG: the transcript is chunked, embedded, and only the relevant chunks are fed to the model — not the whole transcript.
- **Semantic search** — Search the transcript by meaning, not keywords, using cosine similarity over embeddings with no LLM call involved.
- **Asynchronous processing** — A background pipeline updates status as it runs, and the frontend polls and shows live progress.
- **Accounts + history** — Sign up, log in, and every video you summarize is saved to "My Videos," searchable and reopenable at any time.
- **Caching** — A (video, summary style) pair is only ever generated once; repeat requests are served from SQLite instantly and don't re-spend API quota.

---

## 🏗️ Architecture

```
                        ┌─────────────┐
                        │   React     │
                        │  Frontend   │
                        └──────┬──────┘
                               │ JWT-authenticated REST
                        ┌──────▼──────┐
                        │   FastAPI   │
                        └──────┬──────┘
                               │
        ┌──────────────┬──────┼──────────────┬───────────────┐
        ▼              ▼      ▼              ▼               ▼
   Auth (JWT +    Background   Gemini      Gemini        SQLite
   password       job runner   (generate)  (embed)       - users
   hashing)       (async                                 - videos/jobs
                  pipeline)                               - summaries cache
                                                            - chunk embeddings
```

**Processing pipeline** (runs in the background after `POST /videos` returns):

```
queued → transcribing → indexing → chunking → summarizing → complete
                                                           ↘ failed (with error)
```

Transcript indexing (chunk + embed) happens once per video and is shared across every summary style; summarization happens once per (video, style) pair and is cached independently.

---

## 🧩 Tech Stack

**Backend:** FastAPI, Google Gemini (`gemini-2.5-flash` for generation, `gemini-embedding-001` for embeddings), `youtube-transcript-api`, SQLite, JWT (`python-jose`) + `passlib[bcrypt]` for auth, NumPy for vector similarity.

**Frontend:** React (Vite), Tailwind CSS, Axios, `lucide-react`.

**No vector database.** Search is scoped to one video at a time (a few hundred chunks), so brute-force cosine similarity over a NumPy matrix is faster than a network round-trip to a hosted vector DB would be. Embeddings are stored as raw `float32` blobs directly in SQLite.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- A [Gemini API key](https://ai.google.dev/gemini-api/docs/api-key)

### Backend

```bash
git clone https://github.com/Vedashri05/youtube-summarizer.git
cd youtube-summarizer

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file in the project root (see `.env.example`):

```
GEMINI_API_KEY=your_gemini_api_key
MODEL=gemini-2.5-flash
EMBEDDING_MODEL=gemini-embedding-001
JWT_SECRET_KEY=a-long-random-string
```

Generate a real secret rather than using a placeholder:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Run the API from the project root (the SQLite path is relative, so this matters):
```bash
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`, sign up, and paste a YouTube link.

---

## ⚠️ Known Limitations

- **Free-tier Gemini quotas are small.** Generation (`gemini-2.5-flash`) is capped at 20 requests/day on the free tier, and embeddings are capped per-minute. Summarizing one video uses several generation calls (one per transcript chunk, plus a merge step); testing repeatedly can exhaust the daily quota. The app retries transient rate limits automatically but cannot bypass a daily cap.
- **Transcript quality depends on YouTube's auto-captions.** Videos without manually-written captions can have ASR errors (mis-heard technical terms), which limits how clean chat/search results read — this is a data quality ceiling, not a bug in the retrieval logic.
- **SQLite, not a hosted database.** Fine for a single-instance portfolio deployment; would need to move to Postgres for concurrent multi-instance production use.
