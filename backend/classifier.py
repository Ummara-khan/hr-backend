"""
classifier.py  — v3
Keyword-first detection. Falls back to Groq LLM only for truly ambiguous queries.
Returns {"department": str|None, "policy_type": str|None}
None means → search ALL (no filter applied).
"""

import os, re, json
from typing import Optional, Dict
from groq import Groq

# ── Keyword maps ────────────────────────────────────────────────────────────
# More keywords = better coverage, especially for short/casual queries

DEPT_KEYWORDS = {
    "garment":   [
        "garment","stitching","sewing","tailoring","cutting","pattern","fabric",
        "knit","knitting","apparel","production floor","sewing machine","needle",
    ],
    "denim":     [
        "denim","jeans","washing","laser","sandblast","sandblasting","chemical",
        "bleach","dyeing","dye","denim department","wash recipe","formula",
        "indigo","finishing","spray","ozone",
    ],
    "corporate": [
        "corporate","head office","admin","executive","director","manager",
        "ceo","cfo","coo","hr director","board","c-suite","office staff",
        "headquarters","hq","corporate department",
    ],
}

POLICY_KEYWORDS = {
    "hr": [
        "working hours","shift","overtime","uniform","dress code",
        "performance","appraisal","promotion","grade","salary","increment",
        "bonus","recruit","onboard","probation","training","disciplin",
        "grievance","resign","termination","exit","notice period",
        "attendance","punctuality","code of conduct","compensation",
        "wfh","work from home","remote work","car allowance","fuel",
        "travel policy","mobile allowance","skill premium","transport",
        "canteen","meal allowance","induction","joining","grading",
        "employee of","long service","benefits","increment","kpi",
        "office hours","office timing","office time","reporting time",
        "what time","when do","how many hours","work hours","duty hours",
        "late arrival","grace period","biometric","punch","timekeeping",
    ],
    "medical": [
        "medical","health","doctor","hospital","clinic","medicine","pharmacy",
        "reimburse","reimbursement","claim","treatment","dental","vision",
        "spectacle","glasses","maternity","paternity","pregnancy","nursing",
        "wellness","checkup","check-up","insurance","coverage","panel",
        "disability","rehab","mental health","counsel","counselling",
        "telehealth","telemedicine","illness","sick","disease","injury",
        "ehs","chemical exposure","occupational","ambulance","first aid",
        "aku","aga khan","city hospital","al-khidmat","panel hospital",
        "how much coverage","medical limit","annual limit","lab","test",
        "prescription","blood","surgery","operation","inpatient","outpatient",
        "discharge","specialist","referral","health checkup","annual checkup",
    ],
    "leave": [
        "leave","vacation","annual leave","casual leave","earned leave",
        "sick leave","holiday","absence","absent","off day","time off",
        "hajj","umrah","bereavement","death","maternity leave",
        "paternity leave","unpaid","encash","carry forward","accumulate",
        "leave balance","study leave","sabbatical","comp off","compensatory",
        "days off","public holiday","eid","how many days","day off",
        "days leave","weeks leave","leave entitlement","leave policy",
        "days of leave","leave application","take leave","apply leave",
        "paid leave","unpaid leave","lop","loss of pay","substitute",
    ],
    "security": [
        "security","access","badge","id card","cctv","camera","visitor",
        "gate pass","vehicle","parking","material movement","theft",
        "surveillance","password","cyber","data","encryption","vpn",
        "phishing","incident","emergency","fire","evacuation","alarm",
        "chemical store","prohibited","information security","zone",
        "restricted","fraud","breach","hot work","permit","whistleblower",
        "phone number","contact number","contact","who to call","call",
        "emergency number","helpline","ext","extension","email address",
        "contact details","reach out","get in touch","report",
    ],
}


def _keyword_detect(query: str) -> Dict[str, Optional[str]]:
    q = query.lower()

    # Department detection
    dept, best_d_score = None, 0
    for d, kws in DEPT_KEYWORDS.items():
        score = sum(1 for kw in kws if kw in q)
        if score > best_d_score:
            best_d_score, dept = score, d
    if best_d_score == 0:
        dept = None

    # Policy type detection
    ptype, best_p_score = None, 0
    for p, kws in POLICY_KEYWORDS.items():
        score = sum(1 for kw in kws if kw in q)
        if score > best_p_score:
            best_p_score, ptype = score, p
    if best_p_score == 0:
        ptype = None

    return {"department": dept, "policy_type": ptype}


def _llm_detect(query: str) -> Dict[str, Optional[str]]:
    """Only called when keyword detection finds nothing at all."""
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        return {"department": None, "policy_type": None}
    try:
        client = Groq(api_key=key)
        model  = os.getenv("GROQ_MODEL", "llama3-70b-8192")
        prompt = f"""Classify this HR chatbot query for a textile company. Reply ONLY in JSON.

Query: "{query}"

JSON format:
{{"department": "<garment|denim|corporate|null>", "policy_type": "<hr|medical|leave|security|null>"}}

- department: only set if the query clearly mentions one specific department
- policy_type: best match; null if unclear
- Use JSON null (not the string "null") when uncertain"""

        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=60,
        )
        text = re.sub(r"```json|```", "", r.choices[0].message.content.strip()).strip()
        obj  = json.loads(text)
        return {
            "department":  obj.get("department")  if obj.get("department")  in ["garment","denim","corporate"] else None,
            "policy_type": obj.get("policy_type") if obj.get("policy_type") in ["hr","medical","leave","security"] else None,
        }
    except Exception:
        return {"department": None, "policy_type": None}


def detect(query: str) -> Dict[str, Optional[str]]:
    """
    Public API.
    Returns {"department": str|None, "policy_type": str|None}.
    None means no filter → search across everything.
    """
    result = _keyword_detect(query)

    # If we got a policy_type from keywords, trust it.
    # Only call LLM if BOTH are None (completely ambiguous).
    if result["department"] is None and result["policy_type"] is None:
        llm = _llm_detect(query)
        return llm

    return _patch(query, result)

# ── Additional edge case patches ─────────────────────────────────────────────
# These run after the main keyword detection to fix known ambiguities

def _patch(query: str, result: Dict) -> Dict:
    q = query.lower()
    # "spill", "hazmat", "contamination" → security (denim context already set by dept keywords)
    if any(w in q for w in ["spill","hazmat","contamination","toxic","fume","gas leak"]):
        result["policy_type"] = "security"
    # "hr manager", "hr officer", "hr contact" → hr (not corporate dept)
    if re.search(r'\bhr\b', q) and any(w in q for w in ["manager","officer","contact","who is","name"]):
        result["policy_type"] = "hr"
        if result["department"] == "corporate" and "corporate" not in q:
            result["department"] = None   # reset wrongly inferred dept
    return result
