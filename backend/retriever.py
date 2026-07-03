"""
retriever.py  v5  —  Pinecone (1024-dim BAAI/bge-large-en-v1.5)
"""

import os, ssl
from pathlib import Path
from typing import List, Optional, Dict
from dotenv import load_dotenv

THIS_DIR = Path(__file__).parent.resolve()
load_dotenv(THIS_DIR / ".env")

EMBED_MODEL = "BAAI/bge-large-en-v1.5"   # 1024 dims — matches Pinecone index
TOP_K       = 6

_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        # SSL fix for corporate networks
        os.environ["PYTHONHTTPSVERIFY"]  = "0"
        os.environ["CURL_CA_BUNDLE"]     = ""
        os.environ["REQUESTS_CA_BUNDLE"] = ""
        try:
            import certifi
            os.environ["SSL_CERT_FILE"] = certifi.where()
        except ImportError:
            pass

        import warnings, urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(EMBED_MODEL)
        dim = _embedder.get_sentence_embedding_dimension()
        print(f"[Retriever] Model loaded: {EMBED_MODEL} (dim={dim})")
    return _embedder


def search(
    query:       str,
    department:  Optional[str] = None,
    policy_type: Optional[str] = None,
    top_k:       int = TOP_K,
) -> List[Dict]:
    import db
    embedder = get_embedder()
    vec      = embedder.encode(
        query, normalize_embeddings=True
    ).tolist()

    print(f"[Retriever] query='{query[:60]}' dept={department} ptype={policy_type}")

    hits = db.similarity_search(
        query_embedding=vec,
        department=department,
        policy_type=policy_type,
        top_k=top_k,
    )

    print(f"[Retriever] → {len(hits)} hits")
    for h in hits[:3]:
        print(f"   [{h['department']}|{h['policy_type']}] "
              f"score={h['score']:.3f} | {h['text'][:60]!r}")
    return hits


class PolicyRetriever:
    def search(self, query, department=None, policy_type=None, top_k=TOP_K):
        return search(query, department, policy_type, top_k)

    def get_count(self):
        import db
        return db.get_chunk_count()


_retriever: Optional[PolicyRetriever] = None

def get_retriever() -> PolicyRetriever:
    global _retriever
    if _retriever is None:
        _retriever = PolicyRetriever()
    return _retriever
