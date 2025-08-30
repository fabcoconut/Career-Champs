import pandas as pd
import numpy as np
import os
from typing import Dict, Any, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_bench = pd.read_csv(os.path.join(DATA_DIR, "comp_benchmarks.csv"))
_col = pd.read_csv(os.path.join(DATA_DIR, "col_index.csv")).set_index("city")["index"].to_dict()

CURRENCY_TO_GBP = {"GBP":1.0, "USD":0.78, "EUR":0.85}

def annualize(amount: float, period: str) -> float:
    p = (period or "year").lower()
    if p.startswith("hour"): return amount * 40 * 52
    if p.startswith("day"): return amount * 5 * 52
    if p.startswith("week"): return amount * 52
    if p.startswith("month"): return amount * 12
    return amount

def _infer_currency(job: Dict[str, Any]) -> Optional[str]:
    cur = job.get("currency")
    if cur: return cur
    loc = (job.get("location") or "").lower()
    if any(k in loc for k in ["london","united kingdom","uk"]): return "GBP"
    if any(k in loc for k in ["united states","new york","san francisco"]): return "USD"
    if any(k in loc for k in ["euro","paris","berlin","amsterdam"]): return "EUR"
    return None

def estimate_comp(job: Dict[str, Any], base_city: str="London") -> Dict[str, Any]:
    title = (job.get("title") or "")
    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")
    salary_period = job.get("salary_period")  # "year","month","hour",...
    currency = job.get("currency") or _infer_currency(job) or "GBP"

    est_ann = None
    conf = 0.3

    if salary_min or salary_max:
        center = ( (salary_min or salary_max) + (salary_max or salary_min) ) / 2.0 if (salary_min and salary_max) else (salary_max or salary_min)
        est_ann = annualize(center, salary_period or "year")
        conf = 0.7

    if est_ann is None:
        cand = _bench[_bench["title"].str.lower().str.contains((title or "").split()[0].lower() if title else "", na=False)]
        if cand.empty:
            cand = _bench[_bench["title"].str.lower().str.contains("analyst", na=False)]
        if not cand.empty:
            row = cand.iloc[0]
            est_ann = float(row["mid"])
            currency = row["currency"]
            conf = 0.45

    fx = CURRENCY_TO_GBP.get(currency, 1.0)
    ann_gbp = est_ann * fx if est_ann else None

    base = _col.get(base_city, 100)
    loc_city = (job.get("location") or "Remote").split(",")[0]
    loc_idx = _col.get(loc_city, _col.get("Remote", 95))
    col_adj = (loc_idx / base) if base else 1.0

    return {
        "currency": currency,
        "annual_est_local": est_ann,
        "annual_gbp": ann_gbp * col_adj if ann_gbp else None,
        "col_factor": col_adj,
        "confidence": conf
    }
