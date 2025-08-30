# Career Champs v2.1

Personalized, high-paying job board powered by your CV.  
Now with multi-source feeds, auto-tailored CV bullets & cover letters, and compensation intelligence.

## Local Dev
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## Streamlit Cloud Deploy
1. Push this repo to GitHub.  
2. Create a new app on share.streamlit.io → set `app.py` as entry.  
3. Add secrets in **Settings → Secrets**:
```toml
ADZUNA_APP_ID = "your_app_id"
ADZUNA_APP_KEY = "your_app_key"
DEFAULT_COUNTRY = "gb"
OPENAI_API_KEY = "sk-..."   # optional
```
