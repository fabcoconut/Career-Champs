import requests
from typing import List, Dict, Any

def fetch(board: str, query: str) -> List[Dict[str, Any]]:
    url = f"https://api.lever.co/v0/postings/{board}?mode=json"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    out = []
    q = (query or "").lower()
    for j in data:
        title = j.get("text") or ""
        if q and q not in title.lower():
            continue
        loc = j.get("categories",{}).get("location","")
        out.append({
            "id": j.get("id"),
            "title": title,
            "company": board,
            "location": loc,
            "created": j.get("createdAt"),
            "category": j.get("categories",{}).get("team"),
            "redirect_url": j.get("hostedUrl"),
            "description": j.get("descriptionPlain") or "",
            "salary_min": None,
            "salary_max": None,
            "source": "Lever",
            "country": None,
            "currency": None,
            "salary_period": None
        })
    return out
