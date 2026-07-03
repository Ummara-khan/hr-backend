"""
main.py  v5  —  FastAPI + Pinecone + Groq
Deploy backend on Railway. Frontend on Vercel.
"""

import os, json, asyncio
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv

THIS_DIR = Path(__file__).parent.resolve()
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ingest    import build_index
from retriever import get_retriever
from classifier import detect
from llm        import get_llm
import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Startup] Connecting to Pinecone & checking index…")
    loop  = asyncio.get_event_loop()
    count = await loop.run_in_executor(None, db.get_chunk_count)
    if count == 0:
        print("[Startup] Index empty — running ingestion…")
        await loop.run_in_executor(None, build_index)
    else:
        print(f"[Startup] Pinecone index has {count} vectors — skipping ingest.")
    print("[Startup] Ready.")
    yield


origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    os.getenv("FRONTEND_URL", ""),
    "*",
]

app = FastAPI(title="Company Policy Chatbot", version="5.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ──────────────────────────────────────────────────────

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message:     str
    history:     List[Message] = []
    department:  Optional[str] = None
    policy_type: Optional[str] = None

class ChatResponse(BaseModel):
    answer:               str
    sources:              List[str]
    departments:          List[str]
    policy_types:         List[str]
    detected_department:  Optional[str]
    detected_policy_type: Optional[str]
    hits_count:           int


# ── Core RAG ────────────────────────────────────────────────────

def run_rag(req: ChatRequest):
    detected = detect(req.message)
    dept     = req.department  or detected["department"]
    ptype    = req.policy_type or detected["policy_type"]
    retriever = get_retriever()
    hits      = retriever.search(req.message, department=dept, policy_type=ptype, top_k=6)
    history   = [{"role": m.role, "content": m.content} for m in req.history]
    return hits, history, dept, ptype


# ── Routes ──────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "Company Policy Chatbot API v5 (Pinecone)"}


@app.get("/health")
def health():
    try:
        count = db.get_chunk_count()
        return {
            "status": "ok",
            "vector_db": "pinecone",
            "vectors":   count,
            "model":     os.getenv("GROQ_MODEL", "llama3-70b-8192"),
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/diagnose")
def diagnose():
    """Debug: shows index stats + runs a test search."""
    try:
        count = db.get_chunk_count()
        from retriever import search
        hits  = search("maternity leave garment", top_k=3)
        return {
            "vector_db":    "pinecone",
            "total_vectors": count,
            "index_host":   db.PINECONE_HOST,
            "test_search_results": [
                {
                    "department":  h["department"],
                    "policy_type": h["policy_type"],
                    "score":       h["score"],
                    "source":      h["source"],
                    "preview":     h["text"][:120],
                }
                for h in hits
            ],
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    hits, history, dept, ptype = run_rag(req)
    result = get_llm().chat(req.message, history, hits)
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        departments=result["departments"],
        policy_types=result["policy_types"],
        detected_department=dept,
        detected_policy_type=ptype,
        hits_count=len(hits),
    )


@app.post("/stream-chat")
async def stream_chat(req: ChatRequest):
    hits, history, dept, ptype = run_rag(req)
    llm = get_llm()

    async def gen():
        loop   = asyncio.get_event_loop()
        tokens = await loop.run_in_executor(
            None, lambda: list(llm.stream_chat(req.message, history, hits))
        )
        for kind, val in tokens:
            if kind == "token":
                yield f"data: {json.dumps({'token': val})}\n\n"
            else:
                yield f"data: {json.dumps({'done': True, **val, 'detected_department': dept, 'detected_policy_type': ptype, 'hits_count': len(hits)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.post("/ingest")
async def ingest():
    loop  = asyncio.get_event_loop()
    count = await loop.run_in_executor(None, build_index)
    return {"status": "done", "total_vectors": count}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
