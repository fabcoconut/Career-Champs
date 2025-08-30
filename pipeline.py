from typing import List, Dict, Any
import json, os
from sources import adzuna, remotive, greenhouse, lever
from scoring import score_jobs
from comp import estimate_comp

CFG = {
    "sources": {"adzuna": True, "remotive": True, "greenhouse": False, "lever": False},
    "greenhouse_boards": [],
    "lever_boards": [],
    "currency": "GBP",
    "col_base_city": "London"
}

def load_config():
    path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(path):
        with open(path,"r") as f:
            data = json.load(f)
            CFG.update(data)
    return CFG

def search_and_rank(cv_text: str, prefs: Dict[str, Any]) -> List[Dict[str, Any]]:
    cfg = load_config()
    query = prefs.get("query") or prefs.get("target_titles") or ""
    where = prefs.get("location","")
    min_salary = prefs.get("min_salary")
    country = prefs.get("country","gb")

    jobs: List[Dict[str, Any]] = []

    if cfg["sources"].get("adzuna"):
        for page in (1,2):
            jobs += adzuna.fetch(query, where=where, min_salary=min_salary,
                                 max_days_old=prefs.get("max_days_old",30),
                                 page=page, country=country)

    if cfg["sources"].get("remotive"):
        jobs += remotive.fetch(query)

    if cfg["sources"].get("greenhouse"):
        for b in cfg.get("greenhouse_boards", []):
            try: jobs += greenhouse.fetch(b, query)
            except Exception: pass

    if cfg["sources"].get("lever"):
        for b in cfg.get("lever_boards", []):
            try: jobs += lever.fetch(b, query)
            except Exception: pass

    # Deduplicate and attach comp estimates
    seen = set()
    dedup = []
    for j in jobs:
        key = j.get("redirect_url") or f"{j.get('source')}:{j.get('id')}"
        if key and key not in seen:
            seen.add(key)
            j["_comp"] = estimate_comp(j, base_city=cfg.get("col_base_city","London"))
            dedup.append(j)

    ranked = score_jobs(cv_text, dedup, prefs)
    return ranked
