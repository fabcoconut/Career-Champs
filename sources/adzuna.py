import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from utils_secrets import get_secret

APP_ID = get_secret("ADZUNA_APP_ID")
APP_KEY = get_secret("ADZUNA_APP_KEY")
DEFAULT_COUNTRY = get_secret("DEFAULT_COUNTRY", "gb")
BASE = "https://api.adzuna.com/v1/api/jobs"

def fetch(what: str, where: str="", min_salary: Optional[int]=None, max_days_old: int=21,
          page: int=1, results_per_page: int=50, country: str=DEFAULT_COUNTRY) -> List[Dict[str, Any]]:
    if not (APP_ID and APP_KEY):
        return []
    params = {"app_id": APP_ID, "app_key": APP_KEY, "results_per_page": results_per_page,
              "content-type":"application/json", "what": what}
    if where: params["where"] = where
    if min_salary: params["salary_min"] = min_salary
    if max_days_old: params["max_days_old"] = max_days_old
    url = f"{BASE}/{country}/search/{page}?{urlencode(params)}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    out = []
    for it in data.get("results", []):
        out.append({
            "id": it.get("id"),
            "title": it.get("title"),
            "company": (it.get("company") or {}).get("display_name"),
            "location": (it.get("location") or {}).get("display_name"),
            "created": it.get("created"),
            "category": (it.get("category") or {}).get("label"),
            "redirect_url": it.get("redirect_url"),
            "description": it.get("description"),
            "salary_min": it.get("salary_min"),
            "salary_max": it.get("salary_max"),
            "source": "Adzuna",
            "country": country,
            "currency": "GBP" if country=="gb" else None,
            "salary_period": "year"
        })
    return out
