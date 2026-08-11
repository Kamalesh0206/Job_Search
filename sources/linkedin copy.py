import time
from datetime import datetime
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from models import Job

BASE = "https://www.linkedin.com"
SEARCH_ENDPOINT = BASE + "/jobs-guest/jobs/api/seeMoreJobPostings/search"
DETAIL_ENDPOINT = BASE + "/jobs-guest/jobs/api/jobPosting/{job_id}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

def _clean(node):
    return node.get_text(" ", strip=True) if node else ""

def _job_id(card):
    urn = card.get("data-entity-urn", "")
    if urn:
        return urn.rsplit(":", 1)[-1]
    link = card.select_one("a.base-card__full-link")
    if link:
        href = link.get("href", "")
        parts = href.rstrip("/").split("-")
        if parts and parts[-1].isdigit():
            return parts[-1]
    return ""

def _fetch_description(session, job_id, timeout, delay):
    if not job_id:
        return ""
    time.sleep(delay)
    r = session.get(
        DETAIL_ENDPOINT.format(job_id=job_id),
        headers=HEADERS,
        timeout=timeout,
    )
    if r.status_code != 200:
        return ""
    soup = BeautifulSoup(r.text, "html.parser")
    node = (
        soup.select_one(".show-more-less-html__markup")
        or soup.select_one(".description__text")
        or soup
    )
    return _clean(node)

def collect(config):
    settings = config["search"]
    timeout = settings["timeout_seconds"]
    delay = settings["request_delay_seconds"]
    pages = settings["linkedin_pages_per_query"]
    recent_seconds = int(settings["linkedin_recent_hours"] * 3600)

    jobs = []
    session = requests.Session()

    # Broad queries are intentional. Classification happens after collection.
    queries = []
    for rules in config["role_families"].values():
        queries.extend(rules.get("search_queries", []))
    queries = list(dict.fromkeys(queries))

    for query in queries:
        for page in range(pages):
            params = {
                "keywords": query,
                "f_WT": "2",                 # LinkedIn remote workplace filter
                "f_TPR": f"r{recent_seconds}",# Recent jobs
                "start": page * 25,
            }
            time.sleep(delay)
            r = session.get(SEARCH_ENDPOINT, params=params, headers=HEADERS, timeout=timeout)

            if r.status_code == 429:
                print("LinkedIn rate limit reached. Stopping LinkedIn collection for this run.")
                return jobs
            if r.status_code != 200:
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select("div.base-card")
            if not cards:
                break

            for card in cards:
                jid = _job_id(card)
                title = _clean(card.select_one(".base-search-card__title"))
                company = _clean(card.select_one(".base-search-card__subtitle"))
                location = _clean(card.select_one(".job-search-card__location"))
                date_node = card.select_one("time")
                posted = date_node.get("datetime", "") if date_node else ""
                link = card.select_one("a.base-card__full-link")
                url = link.get("href", "").split("?")[0] if link else ""
                description = _fetch_description(session, jid, timeout, delay)

                if title:
                    jobs.append(Job(
                        source="LinkedIn",
                        source_job_id=jid,
                        title=title,
                        company=company,
                        location=location,
                        posted_date=posted,
                        url=url,
                        description=description,
                    ))
    return jobs
