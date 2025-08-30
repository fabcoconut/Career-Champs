import requests
from typing import List, Dict, Any
API = "https://remotive.com/api/remote-jobs"

def fetch(query: str, limit: int=200) -> List[Dict[str, Any]]:
    r = requests.get(API, params={"search": query}, timeout=20)
    r.raise_for_status()
    data = r.json()
    out = []
    for it in data.get("jobs", [])[:limit]:
        out.append({
            "id": it.get("id"),
            "title": it.get("title"),
            "company": it.get("company_name"),
            "location": it.get("candidate_required_location") or "Remote",
            "created": it.get("publication_date"),
            "category": it.get("category"),
            "redirect_url": it.get("url"),
            "description": it.get("description"),
            "salary_min": None,
            "salary_max": None,
            "source": "Remotive",
            "country": None,
            "currency": None,
            "salary_period": None
        })
    return out
