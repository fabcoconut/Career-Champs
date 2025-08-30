import re, io
from pdfminer.high_level import extract_text

def extract_text_from_file(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        data = uploaded_file.read()
        return extract_text(io.BytesIO(data)) or ""
    else:
        return uploaded_file.read().decode("utf-8", errors="ignore")
