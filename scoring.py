from typing import List, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from datetime import datetime, timezone

def _norm(s: str) -> str:
    return re.sub(r'\s+', ' ', (s or "")).strip()

def build_vectorizer():
    return TfidfVectorizer(stop_words="english", ngram_range=(1,2), max_features=40000)

def score_jobs(cv_text: str, jobs: List[Dict[str, Any]], prefs: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not jobs: return []
    docs = [_norm(cv_text)] + [_norm(j.get("description","")) for j in jobs]
    vec = build_vectorizer()
    X = vec.fit_transform(docs)
    sim = cosine_similarity(X[0:1], X[1:]).flatten()

    # salary normalization (from comp estimate)
    arr = np.array([j.get("_comp",{}).get("annual_gbp") for j in jobs], dtype=float)
    if np.all(np.isnan(arr)):
        sal = np.zeros_like(arr)
    else:
        mn, mx = np.nanmin(arr), np.nanmax(arr)
        rng = max(mx - mn, 1.0)
        sal = np.where(np.isnan(arr), 0.2, (arr - mn) / rng)

    # recency
    rec = []
    now = datetime.now(timezone.utc)
    for j in jobs:
        created = j.get("created")
        try:
            dt = datetime.fromisoformat((created or "").replace("Z","+00:00"))
            days = max((now - dt).days, 0)
            rec.append(np.exp(-days/14))
        except Exception:
            rec.append(0.5)
    rec = np.array(rec, dtype=float)

    # seniority
    target = (prefs.get("seniority","any") or "any").lower()
    def bucket(title):
        t = (title or "").lower()
        if any(k in t for k in ["intern","graduate","junior","entry"]): return "junior"
        if any(k in t for k in ["senior","lead","principal","staff","head"]): return "senior"
        return "mid"
    seni = np.array([1.0 if (target=="any" or bucket(j.get("title",""))==target) else 0.3 for j in jobs])

    # keywords boost
    kws = [k.strip().lower() for k in prefs.get("must_have_keywords",[]) if k.strip()]
    kwb = []
    for j in jobs:
        text = (j.get("title","") + " " + j.get("description","")).lower()
        if kws and all(k in text for k in kws):
            kwb.append(1.0)
        elif kws and any(k in text for k in kws):
            kwb.append(0.8)
        else:
            kwb.append(0.6)
    kwb = np.array(kwb, dtype=float)

    w = prefs.get("weights", {"relevance":0.45, "salary":0.25, "recency":0.15, "seniority":0.1, "keywords":0.05})
    ssum = sum(w.values()) or 1.0
    w = {k: v/ssum for k, v in w.items()}
    final = w["relevance"]*sim + w["salary"]*sal + w["recency"]*rec + w["seniority"]*seni + w["keywords"]*kwb

    out = []
    for s, rs, rc, se, kb, j in zip(sim, sal, rec, seni, kwb, jobs):
        jj = dict(j)
        jj["_scores"] = {
            "final": float(w["relevance"]*s + w["salary"]*rs + w["recency"]*rc + w["seniority"]*se + w["keywords"]*kb),
            "relevance": float(s),
            "salary": float(rs),
            "recency": float(rc),
            "seniority": float(se),
            "keywords": float(kb)
        }
        out.append(jj)
    out.sort(key=lambda x: x["_scores"]["final"], reverse=True)
    return out
