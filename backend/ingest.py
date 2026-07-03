"""
ingest.py  v5
- Uses 1024-dim embedding model to match Pinecone index
- Fixes SSL certificate issue on corporate networks
- Reads both .txt and .pdf
"""

import os, sys, ssl, hashlib
from pathlib import Path
from typing import List
from dotenv import load_dotenv

THIS_DIR     = Path(__file__).parent.resolve()
DEFAULT_DATA = (THIS_DIR.parent / "data").resolve()
load_dotenv()

print("=" * 50)
print("Environment Check")
print("GROQ_API_KEY exists:", "GROQ_API_KEY" in os.environ)
print("GROQ_API_KEY length:", len(os.getenv("GROQ_API_KEY", "")))
print("PINECONE_API_KEY exists:", "PINECONE_API_KEY" in os.environ)
print("PINECONE_API_KEY length:", len(os.getenv("PINECONE_API_KEY", "")))
print("=" * 50)

# ── Fix SSL cert verification on corporate networks ────────────────────────
os.environ.setdefault("CURL_CA_BUNDLE", "")
os.environ.setdefault("REQUESTS_CA_BUNDLE", "")
import ssl as _ssl
try:
    _ssl._create_default_https_context = _ssl.create_default_context
except Exception:
    pass

CHUNK_SIZE    = 600
CHUNK_OVERLAP = 120

# 1024-dim model — matches Pinecone index dimension exactly
EMBED_MODEL   = "sentence-transformers/all-mpnet-base-v2"
# all-mpnet-base-v2 outputs 768 dims — let's use a proper 1024 model:
# Actually use BAAI/bge-large-en-v1.5 which is 1024 dims
# OR we use all-mpnet-base-v2 (768) and the user needs to recreate index
# The Pinecone index says 1024, so we MUST use a 1024-dim model
EMBED_MODEL   = "BAAI/bge-large-en-v1.5"   # 1024 dims ✓

DEPARTMENTS   = ["garment", "denim", "corporate"]
POLICY_TYPES  = ["hr", "medical", "leave", "security"]


def _resolve_data(data_dir: str = None) -> Path:
    val = data_dir or os.getenv("DATA_DIR", "")
    if not val:
        return DEFAULT_DATA
    p = Path(val)
    return p.resolve() if p.is_absolute() else (THIS_DIR / p).resolve()


def extract_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_pdf(path: Path) -> str:
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    pages.append(t)
        return "\n\n".join(pages)
    except Exception as e:
        print(f"    [PDF-WARN] {path.name}: {e}")
        return ""


def chunk_text(text: str) -> List[str]:
    chunks, start = [], 0
    text = text.strip()
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        c   = text[start:end].strip()
        if len(c) > 40:
            chunks.append(c)
        if end >= len(text):
            break
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _load_embedder():
    """Load embedding model with SSL workaround for corporate networks."""
    import urllib.request
    # Disable SSL verification for HuggingFace download on corporate networks
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode    = ssl.CERT_NONE

    # Patch urllib to bypass SSL
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ssl_ctx)
    )
    urllib.request.install_opener(opener)

    # Also set env vars that sentence-transformers / requests uses
    os.environ["PYTHONHTTPSVERIFY"]  = "0"
    os.environ["CURL_CA_BUNDLE"]     = ""
    os.environ["REQUESTS_CA_BUNDLE"] = ""

    # Suppress SSL warnings
    import warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()

    from sentence_transformers import SentenceTransformer
    print(f"[Ingest] Loading embedding model: {EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL)
    dim   = model.get_sentence_embedding_dimension()
    print(f"[Ingest] Model loaded — output dimension: {dim}")
    return model


def build_index(data_dir: str = None) -> int:
    import db

    data_path = _resolve_data(data_dir)
    print(f"[Ingest] DATA DIR : {data_path}")
    print(f"[Ingest] DB       : Pinecone  ({db.PINECONE_HOST})")

    if not data_path.exists():
        print(f"[Ingest] ERROR: data directory not found: {data_path}", file=sys.stderr)
        return 0

    db.setup_database()
    embedder  = _load_embedder()
    new_total = 0

    for dept in DEPARTMENTS:
        for ptype in POLICY_TYPES:
            folder = data_path / dept / ptype
            if not folder.exists():
                continue

            for fpath in sorted(folder.glob("*")):
                if fpath.suffix.lower() not in (".txt", ".pdf"):
                    continue

                fhash   = file_hash(fpath)
                file_id = f"{dept}__{ptype}__{fpath.name}"

                if db.file_already_ingested(file_id, fhash):
                    print(f"  SKIP (unchanged): {dept}/{ptype}/{fpath.name}")
                    continue

                print(f"  Ingesting: {dept}/{ptype}/{fpath.name}")

                raw = (extract_pdf(fpath) if fpath.suffix.lower() == ".pdf"
                       else extract_txt(fpath))
                if not raw.strip():
                    print(f"    [WARN] Empty — skipping")
                    continue

                chunks = chunk_text(raw)
                if not chunks:
                    print(f"    [WARN] No usable chunks — skipping")
                    continue

                # Delete old vectors for this file before re-uploading
                db.delete_file_vectors(dept, ptype, fpath.name)

                embeddings = embedder.encode(
                    chunks, show_progress_bar=False, normalize_embeddings=True
                ).tolist()

                db.upsert_chunks(
                    chunks=chunks,
                    embeddings=embeddings,
                    department=dept,
                    policy_type=ptype,
                    source=fpath.name,
                    file_type=fpath.suffix[1:].lower(),
                    file_hash=fhash,
                )
                db.mark_file_ingested(file_id, fhash, len(chunks))
                new_total += len(chunks)
                print(f"    → {len(chunks)} chunks stored")

    total = db.get_chunk_count()
    print(f"[Ingest] Done. Pinecone total: {total} | New this run: {new_total}")
    return total


if __name__ == "__main__":
    build_index()
