"""
llm.py  v3
- Detects empty context and returns a clear diagnostic message instead of
  hallucinating "I don't have information"
- Streaming + non-streaming
"""

import os
from typing import List, Dict, Optional, Generator
from groq import Groq

SYSTEM_TEMPLATE = """You are a Company Policy Assistant for a textile company (departments: Garment, Denim, Corporate).

RETRIEVED POLICY CONTEXT:
{context}

SOURCES: {sources}
DEPARTMENTS IN CONTEXT: {departments}
POLICY AREAS IN CONTEXT: {policy_types}

INSTRUCTIONS:
- Answer ONLY from the policy context above. Do NOT say you lack information if the context contains the answer.
- Be specific: quote exact numbers (days, amounts, phone numbers, extensions) directly from the context.
- When the context lists phone numbers or contacts, reproduce them clearly in a numbered list.
- If multiple departments have different rules, compare them explicitly.
- At the end of your answer always show:

---
**What would you like to do next?**
1. 📋 More details on this topic
2. ❓ Ask another question
3. 🔄 Ask about a specific department
4. 🆕 Start a new conversation
5. 🚪 Exit"""

NO_CONTEXT_MSG = """⚠️ **No policy content was retrieved for your question.**

This usually means one of:
1. The vector database (ChromaDB) is empty or not built yet
2. The `DATA_DIR` path in your `.env` is incorrect
3. The `CHROMA_PERSIST_DIR` path is incorrect

**To fix — run this in your terminal:**
```bash
cd backend
python ingest.py
```
Then restart the server. If you need help, contact your system administrator.

---
**What would you like to do next?**
1. ❓ Ask another question
2. 🆕 Start a new conversation"""


def build_context(hits: List[Dict]):
    if not hits:
        return "", [], [], []
    parts, sources, depts, ptypes = [], [], [], []
    for i, h in enumerate(hits, 1):
        dept  = h.get("department", "").upper()
        ptype = h.get("policy_type", "").upper()
        src   = h.get("source", "")
        parts.append(
            f"[Excerpt {i} | {dept} — {ptype} Policy | Source: {src} | Relevance: {h.get('score',0)}]\n"
            f"{h['text']}"
        )
        if src   not in sources: sources.append(src)
        if dept  not in depts:   depts.append(dept)
        if ptype not in ptypes:  ptypes.append(ptype)
    return "\n\n---\n\n".join(parts), sources, depts, ptypes


class PolicyLLM:
    def __init__(self):
        key = os.getenv("GROQ_API_KEY", "")
        if not key:
            raise ValueError("GROQ_API_KEY not set in .env")
        self.client = Groq(api_key=key)
        self.model  = os.getenv("GROQ_MODEL", "llama3-70b-8192")

    def _msgs(self, user_message, history, hits):
        ctx, sources, depts, ptypes = build_context(hits)
        system = SYSTEM_TEMPLATE.format(
            context=ctx,
            sources=", ".join(sources) or "none",
            departments=", ".join(depts) or "none",
            policy_types=", ".join(ptypes) or "none",
        )
        msgs = [{"role": "system", "content": system}]
        msgs.extend(history[-12:])          # last 6 turns
        msgs.append({"role": "user", "content": user_message})
        return msgs, sources, depts, ptypes

    def chat(self, user_message, history, hits) -> Dict:
        if not hits:
            return {"answer": NO_CONTEXT_MSG, "sources": [], "departments": [], "policy_types": []}
        msgs, sources, depts, ptypes = self._msgs(user_message, history, hits)
        r = self.client.chat.completions.create(
            model=self.model, messages=msgs, temperature=0.1, max_tokens=1200)
        return {"answer": r.choices[0].message.content.strip(),
                "sources": sources, "departments": depts, "policy_types": ptypes}

    def stream_chat(self, user_message, history, hits) -> Generator:
        if not hits:
            # yield the diagnostic message as a single token block
            yield ("token", NO_CONTEXT_MSG)
            yield ("meta", {"sources": [], "departments": [], "policy_types": []})
            return
        msgs, sources, depts, ptypes = self._msgs(user_message, history, hits)
        stream = self.client.chat.completions.create(
            model=self.model, messages=msgs, temperature=0.1, max_tokens=1200, stream=True)
        meta = {"sources": sources, "departments": depts, "policy_types": ptypes}
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield ("token", delta)
        yield ("meta", meta)


_llm: Optional[PolicyLLM] = None
def get_llm() -> PolicyLLM:
    global _llm
    if _llm is None:
        _llm = PolicyLLM()
    return _llm
