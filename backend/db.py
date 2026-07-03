"""
db.py  v7  —  Pinecone  (dimension=1024, model=all-mpnet-base-v2)
Index dimension is 1024 so we use a 1024-dim embedding model.
Works over HTTPS — no firewall issues.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict
from dotenv import load_dotenv

THIS_DIR = Path(__file__).parent.resolve()
load_dotenv(THIS_DIR / ".env")

PINECONE_API_KEY = "pcsk_33d4g5_Bq89VQAaeUVMv7HLj41NRU8fkvuJSxJnUStYiuVv42BEkJvNvgQhwsvkxt68vjq"
PINECONE_HOST    = "https://hrpolicy-chatbot-3tzsh4r.svc.aped-4627-b74a.pinecone.io"
EMBED_DIM        = 1024   # must match Pinecone index dimension

_index = None


def get_index():
    global _index
    if _index is None:
        from pinecone import Pinecone
        pc     = Pinecone(api_key=PINECONE_API_KEY)
        _index = pc.Index(host=PINECONE_HOST)
        stats  = _index.describe_index_stats()
        total  = stats.get("total_vector_count", 0)
        dim    = stats.get("dimension", EMBED_DIM)
        print(f"[DB] Pinecone connected — {total} vectors, dimension={dim}")
    return _index


# ── File tracker (local JSON — skip unchanged files) ───────────────────────

TRACKER_FILE = THIS_DIR / "ingested_files.json"


def _load_tracker() -> dict:
    if TRACKER_FILE.exists():
        import json
        try:
            return json.loads(TRACKER_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_tracker(data: dict):
    import json
    TRACKER_FILE.write_text(json.dumps(data, indent=2))


def file_already_ingested(file_id: str, file_hash: str) -> bool:
    return _load_tracker().get(file_id, {}).get("hash") == file_hash


def mark_file_ingested(file_id: str, file_hash: str, chunk_count: int):
    tracker = _load_tracker()
    tracker[file_id] = {"hash": file_hash, "chunks": chunk_count}
    _save_tracker(tracker)


def get_chunk_count() -> int:
    try:
        stats = get_index().describe_index_stats()
        return stats.get("total_vector_count", 0)
    except Exception as e:
        print(f"[DB] Could not get count: {e}")
        return 0


# ── Delete stale vectors for a file ───────────────────────────────────────

def delete_file_vectors(department: str, policy_type: str, source: str):
    """Delete all vectors that belong to a specific file."""
    try:
        get_index().delete(filter={
            "$and": [
                {"department":  {"$eq": department}},
                {"policy_type": {"$eq": policy_type}},
                {"source":      {"$eq": source}},
            ]
        })
    except Exception as e:
        print(f"    [DB] Delete warning (ok on first run): {e}")


# ── Upsert chunks ──────────────────────────────────────────────────────────

def upsert_chunks(
    chunks:      List[str],
    embeddings:  List[List[float]],
    department:  str,
    policy_type: str,
    source:      str,
    file_type:   str,
    file_hash:   str,
):
    idx            = get_index()
    file_id_prefix = f"{department}__{policy_type}__{source}__"

    vectors = []
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        vectors.append({
            "id":     f"{file_id_prefix}{i}",
            "values": emb,
            "metadata": {
                "content":     chunk[:1500],
                "department":  department,
                "policy_type": policy_type,
                "source":      source,
                "file_type":   file_type,
                "chunk_index": i,
                "file_hash":   file_hash,
            }
        })

    # Batch upsert 100 at a time
    BATCH = 100
    for start in range(0, len(vectors), BATCH):
        idx.upsert(vectors=vectors[start:start + BATCH])

    print(f"    [DB] Upserted {len(vectors)} vectors → Pinecone")


# ── Similarity search ──────────────────────────────────────────────────────

def similarity_search(
    query_embedding: List[float],
    department:      Optional[str] = None,
    policy_type:     Optional[str] = None,
    top_k:           int = 6,
) -> List[Dict]:
    idx = get_index()

    # Build metadata filter
    if department and policy_type:
        filter_dict = {"$and": [
            {"department":  {"$eq": department}},
            {"policy_type": {"$eq": policy_type}},
        ]}
    elif department:
        filter_dict = {"department":  {"$eq": department}}
    elif policy_type:
        filter_dict = {"policy_type": {"$eq": policy_type}}
    else:
        filter_dict = None

    kwargs = {
        "vector":           query_embedding,
        "top_k":            top_k,
        "include_metadata": True,
    }
    if filter_dict:
        kwargs["filter"] = filter_dict

    res  = idx.query(**kwargs)
    hits = []
    for match in res.get("matches", []):
        meta = match.get("metadata", {})
        hits.append({
            "text":        meta.get("content", ""),
            "department":  meta.get("department", ""),
            "policy_type": meta.get("policy_type", ""),
            "source":      meta.get("source", ""),
            "file_type":   meta.get("file_type", ""),
            "score":       float(match.get("score", 0)),
        })
    return hits


def setup_database():
    """Verify Pinecone connection — no schema setup needed."""
    print("[DB] Verifying Pinecone connection…")
    idx   = get_index()
    stats = idx.describe_index_stats()
    dim   = stats.get("dimension", EMBED_DIM)
    count = stats.get("total_vector_count", 0)
    print(f"[DB] ✓ Index ready — {count} vectors, dimension={dim}")
    if dim != EMBED_DIM:
        raise ValueError(
            f"[DB] Dimension mismatch! Index={dim} but EMBED_DIM={EMBED_DIM}. "
            f"Update EMBED_DIM in db.py to match your Pinecone index."
        )
