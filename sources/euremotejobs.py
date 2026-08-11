import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from models import Job

BASE = "https://euremotejobs.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    )
}

def _text(node):
    return node.get_text(" ", strip=True) if node else ""

def _extract_job_links(html):
    soup = BeautifulSoup(html, "html.parser")
    found = []
    for a in soup.find_all("a", href=True):
        href = urljoin(BASE, a["href"])
        if "/job/" not in href:
            continue
        # Exclude taxonomy/navigation URLs.
        if "/job-category/" in href or "/job-region/" in href or "/job-tag/" in href:
            continue
        found.append(href.split("?")[0].rstrip("/") + "/")
    return list(dict.fromkeys(found))

def _detail(session, url, timeout, delay):
    time.sleep(delay)
    r = session.get(url, headers=HEADERS, timeout=timeout)
    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    title = _text(soup.select_one("h1"))
    if not title:
        return None

    page_text = _text(soup)

    # Site markup can change; use both selectors and resilient text fallbacks.
    company = _text(
        soup.select_one(".company")
        or soup.select_one(".company_name")
        or soup.select_one(".job_listing-company")
    )
    location = _text(
        soup.select_one(".location")
        or soup.select_one(".job-location")
        or soup.select_one(".job_listing-location")
    )

    posted = ""
    m = re.search(r"Posted\s+((?:\d+\s+)?(?:seconds?|minutes?|hours?|days?|weeks?|months?)\s+ago)", page_text, re.I)
    if m:
        posted = m.group(1)

    desc_node = (
        soup.select_one(".job_description")
        or soup.select_one(".job-description")
        or soup.select_one(".single_job_listing")
        or soup.select_one("main")
    )
    description = _text(desc_node)

    source_job_id = url.rstrip("/").split("/")[-1]
    return Job(
        source="EU Remote Jobs",
        source_job_id=source_job_id,
        title=title,
        company=company,
        location=location,
        posted_date=posted,
        url=url,
        description=description,
    )

def collect(config):
    settings = config["search"]
    timeout = settings["timeout_seconds"]
    delay = settings["request_delay_seconds"]
    max_pages = settings["euremote_pages"]

    session = requests.Session()
    links = []

    # EU Remote Jobs is already a remote-job board. Crawl newest listing pages,
    # then classify locally so unusual titles such as "AI-Native Product Manager"
    # are not missed.
    for page in range(1, max_pages + 1):
        url = f"{BASE}/jobs/" if page == 1 else f"{BASE}/jobs/page/{page}/"
        time.sleep(delay)
        r = session.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code != 200:
            break
        page_links = _extract_job_links(r.text)
        if not page_links:
            break
        links.extend(page_links)

    jobs = []
    for url in list(dict.fromkeys(links)):
        job = _detail(session, url, timeout, delay)
        if job:
            jobs.append(job)
    return jobs
