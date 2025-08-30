from typing import List, Dict, Any
import json, os
from concurrent.futures import ThreadPoolExecutor, as_completed
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

GB_CITY_TOKENS = [
    "london","manchester","birmingham","leeds","glasgow","edinburgh","bristol","cardiff",
    "sheffield","liverpool","newcastle","nottingham","leicester","southampton","portsmouth",
    "oxford","cambridge","brighton","reading","milton keynes","belfast","aberdeen","dundee","york"
]
def is_gb_location(loc: str) -> bool:
    if not loc: return False
    l = loc.lower()
    if "ireland" in l or "dublin" in l:  # exclude IE
        return False
    if any(t in l for t in ["united kingdom","uk","england","scotland","wales","northern ireland"]):
        return True
    if any(city in l for city in GB_CITY_TOKENS):
        return True
    # Allow explicit remote-UK
    if "remote" in l and ("uk" in l or "united kingdom" in l):
        return True
    return False

def _fetch_all(cfg, query, where, min_salary, max_days_old, country, pages, max_per_source) -> List[Dict[str, Any]]:
    jobs: List[Dict[str, Any]] = []
    futs = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        if cfg["sources"].get("adzuna"):
            for p in range(1, pages+1):
                futs.append(ex.submit(adzuna.fetch, query, where, min_salary, max_days_old, p, max_per_source, country))
        if cfg["sources"].get("remotive"):
            futs.append(ex.submit(remotive.fetch, query, max_per_source))
        if cfg["sources"].get("greenhouse"):
            for b in cfg.get("greenhouse_boards", []):
                futs.append(ex.submit(greenhouse.fetch, b, query))
        if cfg["sources"].get("lever"):
            for b in cfg.get("lever_boards", []):
                futs.append(ex.submit(lever.fetch, b, query))

        for f in as_completed(futs):
            try:
                jobs += f.result() or []
            except Exception:
                pass
    return jobs[: max_per_source * 6]  # global sanity cap

def search_and_rank(cv_text: str, prefs: Dict[str, Any]) -> List[Dict[str, Any]]:
    cfg = load_config()
    query = prefs.get("query") or prefs.get("target_titles") or ""
    where = prefs.get("location","")
    min_salary = prefs.get("min_salary")
    country = prefs.get("country","gb")
    max_days_old = prefs.get("max_days_old", 30)
    max_per_source = int(prefs.get("max_per_source", 60))
    fast_mode = bool(prefs.get("fast_mode", True))
    strict_uk = bool(prefs.get("strict_uk", True))

    pages = 1 if fast_mode else 2

    jobs = _fetch_all(cfg, query, where, min_salary, max_days_old, country, pages, max_per_source)

    # Deduplicate and attach comp
    seen = set()
    dedup = []
    for j in jobs:
        key = j.get("redirect_url") or f"{j.get('source')}:{j.get('id')}"
        if key and key not in seen:
            seen.add(key)
            j["_comp"] = estimate_comp(j, base_city=cfg.get("col_base_city","London"))
            dedup.append(j)

    # Strict market filter
    if country == "gb" and strict_uk:
        dedup = [j for j in dedup if is_gb_location(j.get("location",""))]

    # Rank
    ranked = score_jobs(cv_text, dedup, prefs)
    return ranked