import os
import streamlit as st
from dotenv import load_dotenv

def get_secret(key: str, default: str = "") -> str:
    """
    Read a value from Streamlit Cloud secrets if present,
    otherwise fall back to a local .env file for dev.
    """
    try:
        # Prefer Streamlit Cloud secrets
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        # In case st.secrets access fails in non-Streamlit contexts
        pass

    # Local dev fallback
    load_dotenv()
    return os.getenv(key, default)
