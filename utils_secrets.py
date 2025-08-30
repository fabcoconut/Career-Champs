import os, streamlit as st
from dotenv import load_dotenv
def get_secret(key: str, default: str = '') -> str:
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    load_dotenv()
    return os.getenv(key, default)
