# 🎥 AI YouTube Video Summarizer

An AI-powered web application that generates structured summaries of YouTube videos using transcripts and Google's Gemini API.

Users simply paste a YouTube video URL, and the application returns:

- 📄 Overall Summary
- ⏱️ Timestamped Key Points
- 🏷️ Topics Covered

---

## 🚀 Features

- AI-generated structured summary using Gemini
- Timestamped key points
- Topics covered
- Transcript chunking for long videos (Map-Reduce Summarization)
- SQLite caching to avoid regenerating summaries
- React frontend with FastAPI backend

---

## 🖥️ Demo

### Home Page

> *(Add screenshot here)*

### Generated Summary

> *(Add screenshot here)*

---

## 🏗️ Project Architecture

```
                User
                  │
                  ▼
         React + Tailwind UI
                  │
              Axios (POST)
                  │
                  ▼
           FastAPI Backend
                  │
      Extract YouTube Video ID
                  │
                  ▼
     Fetch Transcript (YouTube API)
                  │
                  ▼
      Chunk Transcript (Map Phase)
                  │
                  ▼
      Gemini AI Summarization
                  │
                  ▼
     Combine Summaries (Reduce Phase)
                  │
                  ▼
        SQLite Cache Storage
                  │
                  ▼
        JSON Response to React
```

---

# 🛠️ Tech Stack

### Frontend

- React
- Tailwind CSS
- Axios

### Backend

- FastAPI
- Python
- Pydantic

---

# 📂 Project Structure

```
youtube-video-summarizer/
│
├── app/
│   ├── models/
│   ├── services/
│   ├── utils/
│   ├── main.py
│   └── config.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── main.jsx
│
├── database/
│
├── requirements.txt
├── README.md
└── .env.example
```

---

# ⚙️ Installation

## 1. Clone Repository

```bash
git clone https://github.com/<your-username>/youtube-video-summarizer.git

cd youtube-video-summarizer
```

---

## 2. Backend Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
GEMINI_API_KEY=YOUR_API_KEY
MODEL=gemini-2.5-flash
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

Backend runs on:

```
http://127.0.0.1:8000
```

---

## 3. Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend runs on:

```
http://localhost:5173
```

---

# 💡 How It Works

1. User pastes a YouTube URL.
2. FastAPI extracts the video ID.
3. Transcript is fetched using `youtube-transcript-api`.
4. Transcript is split into smaller chunks.
5. Gemini summarizes each chunk.
6. Chunk summaries are combined into a final summary.
7. The summary is cached in SQLite.
8. React displays the results in a structured UI.

---

# 📈 Future Improvements

- Export summary as PDF
- Multi-language transcript support
- YouTube thumbnail preview
- User authentication
- Summary history

---

# 👩‍💻 Author

**Vedashri Deshmukh**

GitHub: https://github.com/Vedashri05

---