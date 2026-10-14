import re
import hashlib
from urllib.parse import urlsplit, urlunsplit

def canonical_url(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))

def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[\W_]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def company_title_fingerprint(company: str, title: str) -> str:
    """Detects cross-source duplicates where the same job is listed on multiple job boards."""
    c_norm = normalize_text(company)
    t_norm = normalize_text(title)
    raw = f"cross|{c_norm}|{t_norm}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def fingerprint(source: str, source_job_id: str, title: str, company: str, url: str) -> str:
    if source_job_id and source_job_id != "None":
        raw = f"{source}|{source_job_id}"
    elif url:
        raw = f"{source}|{canonical_url(url)}"
    else:
        raw = f"{source}|{normalize_text(company)}|{normalize_text(title)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
