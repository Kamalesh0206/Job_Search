import hashlib
from urllib.parse import urlsplit, urlunsplit

def canonical_url(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))

def fingerprint(source: str, source_job_id: str, title: str, company: str, url: str) -> str:
    if source_job_id:
        raw = f"{source}|{source_job_id}"
    elif url:
        raw = f"{source}|{canonical_url(url)}"
    else:
        raw = f"{source}|{title.lower().strip()}|{company.lower().strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
