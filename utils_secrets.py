import os
import streamlit as st
from dotenv import load_dotenv

def get_secret(key: str, default: str = "") -> str:
    """
    Prefer Streamlit Cloud secrets; fallback to .env for local dev.
    """
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    load_dotenv()
    return os.getenv(key, default)
