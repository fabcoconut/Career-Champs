import streamlit as st
import pandas as pd
from utils import extract_text_from_file
from pipeline import search_and_rank, load_config

st.set_page_config(page_title="Career Champs", layout="wide", page_icon="🧑‍💼")
st.title("Career Champs 🚀")
st.caption("Multi-source, high-paying roles matched to your CV. Auto-tailor + comp intel built-in.")

cfg = load_config()
with st.sidebar:
    st.header("Sources")
    st.json(cfg["sources"], expanded=False)
    st.divider()
    st.write("COL Base City:", cfg.get("col_base_city","London"))
    st.divider()
    st.subheader("Performance")
    fast_mode = st.toggle("⚡ Fast mode (recommended)", value=True, help="Fewer pages + smaller vectorizer for speed")
    max_per_source = st.slider("Max results per source", 20, 200, 60, step=20)
    strict_uk = st.toggle("🇬🇧 Strict UK only (when Market=gb)", value=True)

col1, col2 = st.columns([1,1])
with col1:
    st.subheader("1) Upload your CV")
    up = st.file_uploader("PDF or TXT", type=["pdf","txt","text","md"])
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
    country = st.selectbox("Market", ["gb","us","nl","de","fr","ca"], index=0)
    min_salary = st.number_input("Min salary (annual)", min_value=0, value=60000, step=5000)
    seniority = st.selectbox("Seniority", ["any","junior","mid","senior"], index=2)
    must_have = st.text_input("Must-have keywords", "Python, financial modeling")
    max_days_old = st.slider("Max days old", 3, 60, 30)
    weights = {
        "relevance": st.slider("Weight: Relevance", 0.0, 1.0, 0.45, 0.05),
        "salary": st.slider("Weight: Salary", 0.0, 1.0, 0.25, 0.05),
        "recency": st.slider("Weight: Recency", 0.0, 1.0, 0.15, 0.05),
        "seniority": st.slider("Weight: Seniority", 0.0, 1.0, 0.10, 0.05),
        "keywords": st.slider("Weight: Keywords", 0.0, 1.0, 0.05, 0.05)
    }
    ssum = sum(weights.values()) or 1
    for k in weights: weights[k] = float(weights[k] / ssum)

go = st.button("🔎 Fetch from all sources", type="primary", use_container_width=True)

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
            "max_per_source": int(max_per_source),
            "fast_mode": bool(fast_mode),
            "strict_uk": bool(strict_uk)
        }
        jobs = search_and_rank(cv_text, prefs)

    if not jobs:
        st.warning("No results found. Try broader titles/location or lower min salary.")
    else:
        # Card-style list
        st.success(f"Found {len(jobs)} roles. Top matches first.")
        for i, j in enumerate(jobs[:100]):  # render top 100 for performance
            sc = j.get("_scores",{})
            comp = j.get("_comp",{})
            with st.container(border=True):
                cols = st.columns([0.65, 0.35])
                with cols[0]:
                    st.markdown(f"### {j.get('title','(no title)')}")
                    st.markdown(f"**{j.get('company','Unknown')}** — {j.get('location','')}")
                    st.markdown(f"Score: **{sc.get('final',0):.2f}** · Est £(COL-adj): **{(comp.get('annual_gbp') and round(comp.get('annual_gbp')) or '—')}** · Source: {j.get('source','')}")
                    if j.get('description'):
                        st.caption((j['description'][:260] + "…") if len(j['description'])>260 else j['description'])
                with cols[1]:
                    if j.get("redirect_url"):
                        st.link_button("Open role ↗", j["redirect_url"], use_container_width=True)
                    st.caption(f"Posted: {j.get('created','—')}")
                    st.progress(min(1.0, max(0.0, sc.get('relevance',0))), text="Relevance")

        # CSV download
        import pandas as pd
        rows = []
        for j in jobs:
            sc = j.get("_scores",{})
            comp = j.get("_comp",{})
            rows.append({
                "Score": round(sc.get("final",0),3),
                "Title": j.get("title"),
                "Company": j.get("company"),
                "Location": j.get("location"),
                "Est £ (COL-adj)": round(comp.get("annual_gbp",0)) if comp.get("annual_gbp") else None,
                "Confidence": comp.get("confidence"),
                "Posted": j.get("created"),
                "Source": j.get("source"),
                "URL": j.get("redirect_url")
            })
        df = pd.DataFrame(rows)
        st.download_button("⬇️ Download results (CSV)", df.to_csv(index=False).encode("utf-8"),
                           file_name="career_champs_results.csv", mime="text/csv", use_container_width=True)