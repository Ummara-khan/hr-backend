# 🏭 Company Policy Chatbot

Full-stack RAG chatbot with Pinecone vector DB.

| Layer | Tech | Host |
|-------|------|------|
| Frontend | React 18 | **Vercel** |
| Backend | FastAPI | **Railway** |
| Vector DB | **Pinecone** | pinecone.io |
| LLM | Groq llama3-70b | groq.com (free) |

---

## 🚀 Quick Start

### Step 1 — Install & Ingest

```bash
cd backend

# Copy env and add GROQ_API_KEY
copy .env.example .env        # Windows
# cp .env.example .env        # Mac/Linux

# Install
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Generate policy files (if not present)
python generate_policies.py

# Push all policies to Pinecone
python fix_and_reindex.py

# Run locally
python main.py
# Test: http://localhost:8000/diagnose
```

### Step 2 — Deploy Backend (Railway)

1. Push to GitHub
2. Railway → New Project → Deploy from GitHub → set root to `backend`
3. Add env vars:
   ```
   GROQ_API_KEY   = gsk_...
   GROQ_MODEL     = llama3-70b-8192
   FRONTEND_URL   = https://your-app.vercel.app
   ```

### Step 3 — Deploy Frontend (Vercel)

1. Vercel → New Project → set root to `frontend`
2. Add env var:
   ```
   REACT_APP_API_URL = https://your-backend.railway.app
   ```

---

## 🔑 .env (backend only)

```env
GROQ_API_KEY=gsk_...       # console.groq.com (free)
GROQ_MODEL=llama3-70b-8192
DATA_DIR=../data
FRONTEND_URL=https://your-app.vercel.app
```

> Pinecone API key and host are already configured in `db.py`.

---

## 📡 Endpoints

| Path | Description |
|------|-------------|
| `GET /health` | Health + vector count |
| `GET /diagnose` | Index stats + test search |
| `POST /stream-chat` | Streaming SSE chat |
| `POST /chat` | Non-streaming chat |
| `POST /ingest` | Re-ingest policies |

