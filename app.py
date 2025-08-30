import json
import pandas as pd
import streamlit as st
from utils import extract_text_from_file
from pipeline import search_and_rank, load_config

# ---------- App setup ----------
st.set_page_config(page_title="Career Champs", layout="wide", page_icon="🧑‍💼")
st.title("Career Champs 🚀")
st.caption("Multi-source, high-paying roles matched to your CV. Auto-tailor + comp intel built-in.")

# ---------- Caching ----------
@st.cache_data(ttl=300, show_spinner=False)
def cached_search(cv_text: str, prefs_json: str):
    """
    Cache the heavy search across sources + ranking for 5 minutes.
    We pass a JSON string (stable, hashable) so cache keys are deterministic.
    """
    prefs = json.loads(prefs_json)
    return search_and_rank(cv_text, prefs)

# ---------- Sidebar ----------
cfg = load_config()
with st.sidebar:
    st.header("Sources")
    st.json(cfg["sources"], expanded=False)
    st.divider()
    st.write("COL Base City:", cfg.get("col_base_city", "London"))
    st.divider()
    st.subheader("Performance")
    fast_mode = st.toggle("⚡ Fast mode (recommended)", value=True, help="Fewer pages + smaller vectorizer for speed")
    max_per_source = st.slider("Max results per source", 20, 200, 60, step=20)
    strict_uk = st.toggle("🇬🇧 Strict UK only (when Market=gb)", value=True)

# ---------- Main: inputs ----------
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1) Upload your CV")
    up = st.file_uploader("PDF or TXT", type=["pdf", "txt", "text", "md"])
    cv_text = ""
    if up:
        try:
            cv_text = extract_text_from_file(up)
        except Exception as e:
            st.error(f"Read error: {e}")
    cv_text = st.text_area("Extracted CV (editable):", value=cv_text, height=220)

with col2:
    st.subheader("2) Preferences")
    target_titles = st.text_input("Target roles", "Investment Analyst, Private Equity Analyst, Strategy Analyst")
    location = st.text_input("Location", "London or Remote")
    country = st.selectbox("Market", ["gb", "us", "nl", "de", "fr", "ca"], index=0)
    min_salary = st.number_input("Min salary (annual)", min_value=0, value=60000, step=5000)
    seniority = st.selectbox("Seniority", ["any", "junior", "mid", "senior"], index=2)
    must_have = st.text_input("Must-have keywords", "Python, financial modeling")
    max_days_old = st.slider("Max days old", 3, 60, 30)

    # Ranking weights
    weights = {
        "relevance": st.slider("Weight: Relevance", 0.0, 1.0, 0.45, 0.05),
        "salary": st.slider("Weight: Salary", 0.0, 1.0, 0.25, 0.05),
        "recency": st.slider("Weight: Recency", 0.0, 1.0, 0.15, 0.05),
        "seniority": st.slider("Weight: Seniority", 0.0, 1.0, 0.10, 0.05),
        "keywords": st.slider("Weight: Keywords", 0.0, 1.0, 0.05, 0.05),
    }
    ssum = sum(weights.values()) or 1
    for k in weights:
        weights[k] = float(weights[k] / ssum)

go = st.button("🔎 Fetch from all sources", type="primary", use_container_width=True)

# ---------- Run search ----------
if go:
    with st.spinner("Aggregating roles across sources..."):
        prefs = {
            "target_titles": target_titles,
            "query": target_titles,
            "location": location,
            "country": country,
            "min_salary": int(min_salary) if min_salary else None,
            "seniority": seniority,
            "must_have_keywords": [k.strip() for k in must_have.split(",") if k.strip()],
            "max_days_old": int(max_days_old),
            "weights": weights,
            # performance & filtering
            "max_per_source": int(max_per_source),
            "fast_mode": bool(fast_mode),
            "strict_uk": bool(strict_uk),
        }
        # Use a stable JSON string for the cache key
        prefs_json = json.dumps(prefs, sort_keys=True)
        jobs = cached_search(cv_text, prefs_json)

    if not jobs:
        st.warning("No results found. Try broader titles/location or lower min salary.")
    else:
        st.success(f"Found {len(jobs)} roles. Top matches first.")

        # ---------- Card-style results ----------
        for i, j in enumerate(jobs[:100]):  # render top 100 for performance
            sc = j.get("_scores", {})
            comp = j.get("_comp", {})
            with st.container(border=True):
                cols = st.columns([0.65, 0.35])
                with cols[0]:
                    st.markdown(f"### {j.get('title', '(no title)')}")
                    st.markdown(f"**{j.get('company', 'Unknown')}** — {j.get('location', '')}")
                    est = comp.get("annual_gbp")
                    est_txt = f"{round(est):,}" if est else "—"
                    st.markdown(
                        f"Score: **{sc.get('final', 0):.2f}** · Est £(COL-adj): **{est_txt}** · Source: {j.get('source', '')}"
                    )
                    if j.get("description"):
                        desc = j["description"]
                        st.caption((desc[:260] + "…") if len(desc) > 260 else desc)
                with cols[1]:
                    if j.get("redirect_url"):
                        st.link_button("Open role ↗", j["redirect_url"], use_container_width=True)
                    st.caption(f"Posted: {j.get('created', '—')}")
                    st.progress(min(1.0, max(0.0, sc.get("relevance", 0))), text="Relevance")

        # ---------- CSV download ----------
        rows = []
        for j in jobs:
            sc = j.get("_scores", {})
            comp = j.get("_comp", {})
            rows.append(
                {
                    "Score": round(sc.get("final", 0), 3),
                    "Title": j.get("title"),
                    "Company": j.get("company"),
                    "Location": j.get("location"),
                    "Est £ (COL-adj)": round(comp.get("annual_gbp", 0)) if comp.get("annual_gbp") else None,
                    "Confidence": comp.get("confidence"),
                    "Posted": j.get("created"),
                    "Source": j.get("source"),
                    "URL": j.get("redirect_url"),
                }
            )
        df = pd.DataFrame(rows)
        st.download_button(
            "⬇️ Download results (CSV)",
            df.to_csv(index=False).encode("utf-8"),
            file_name="career_champs_results.csv",
            mime="text/csv",
            use_container_width=True,
        )