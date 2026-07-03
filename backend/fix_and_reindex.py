#!/usr/bin/env python3
"""
fix_and_reindex.py  v3
Clears Pinecone index and re-ingests all policy files.
Run: python fix_and_reindex.py
"""

import os, sys, ssl
from pathlib import Path
from dotenv import load_dotenv

THIS_DIR = Path(__file__).parent.resolve()
load_dotenv(THIS_DIR / ".env")

# ── SSL fix (corporate / Windows networks) ─────────────────────────────────
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

print("=" * 60)
print("  POLICY CHATBOT — PINECONE REINDEX")
print("=" * 60)

# Check GROQ key
if not os.getenv("GROQ_API_KEY", "").strip():
    print("\n❌  GROQ_API_KEY missing in .env")
    print("   Get free key at: https://console.groq.com")
    sys.exit(1)

import db

# Step 1: connect
print("\n[1/5] Connecting to Pinecone…")
try:
    db.setup_database()
    print("  ✓ Connected")
except Exception as e:
    print(f"\n❌  Pinecone failed: {e}")
    sys.exit(1)

# Step 2: clear
print("\n[2/5] Clearing Pinecone index…")
try:
    db.get_index().delete(delete_all=True)
    tracker = THIS_DIR / "ingested_files.json"
    if tracker.exists():
        tracker.unlink()
    print("  ✓ Index cleared")
except Exception as e:
    print(f"  ⚠  Could not clear (ok if empty): {e}")

# Step 3: find files
print("\n[3/5] Locating policy files…")
from ingest import _resolve_data
data_path = _resolve_data()
txt_count = len(list(data_path.rglob("*.txt")))
pdf_count = len(list(data_path.rglob("*.pdf")))
print(f"  Found {txt_count} .txt + {pdf_count} .pdf files")

if txt_count == 0 and pdf_count == 0:
    print(f"\n❌  No policy files in: {data_path}")
    print("   Run: python generate_policies.py")
    sys.exit(1)

# Step 4: ingest
print("\n[4/5] Ingesting all files into Pinecone…")
from ingest import build_index
total = build_index()

if total == 0:
    print("\n❌  0 vectors stored. Check your data files.")
    sys.exit(1)
print(f"  ✓ {total} vectors in Pinecone")

# Step 5: test search
print("\n[5/5] Test search: 'maternity leave garment'…")
import time; time.sleep(3)   # let Pinecone index settle

from retriever import search
hits = search("maternity leave garment", top_k=3)

if not hits:
    print("  ⚠  0 hits (Pinecone may still indexing — wait 10s and check /diagnose)")
else:
    print(f"  ✓ {len(hits)} hits:")
    for h in hits:
        print(f"    [{h['department'].upper()}|{h['policy_type'].upper()}]"
              f" score={h['score']:.3f}  {h['text'][:80]!r}")

print(f"\n{'=' * 60}")
print("  ✅  Done! Start the server:  python main.py")
print(f"{'=' * 60}\n")
