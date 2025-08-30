import requests
from typing import List, Dict, Any

def fetch(board: str, query: str) -> List[Dict[str, Any]]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    out = []
    q = (query or "").lower()
    for j in data.get("jobs", []):
        title = j.get("title") or ""
        if q and q not in title.lower():
            continue
        loc = (j.get("location") or {}).get("name","")
        out.append({
            "id": j.get("id"),
            "title": title,
            "company": board,
            "location": loc,
            "created": j.get("updated_at"),
            "category": None,
            "redirect_url": j.get("absolute_url"),
            "description": "",
            "salary_min": None,
            "salary_max": None,
            "source": "Greenhouse",
            "country": None,
            "currency": None,
            "salary_period": None
        })
    return out
