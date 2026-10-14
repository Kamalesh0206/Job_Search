import time
import random
import requests

from bs4 import BeautifulSoup
from models import Job


BASE = "https://www.linkedin.com"

SEARCH_ENDPOINT = (
    BASE + "/jobs-guest/jobs/api/seeMoreJobPostings/search"
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,"
              "application/xml;q=0.9,*/*;q=0.8"
}


def _clean(node):
    if node is None:
        return ""

    return node.get_text(
        " ",
        strip=True
    )


def _get_job_id(card):

    urn = card.get(
        "data-entity-urn",
        ""
    )

    if urn:
        return urn.rsplit(
            ":",
            1
        )[-1]

    link = card.select_one(
        "a.base-card__full-link"
    )

    if link:

        href = link.get(
            "href",
            ""
        )

        href = href.split("?")[0]

        parts = href.rstrip(
            "/"
        ).split("-")

        if parts:
            last = parts[-1]

            if last.isdigit():
                return last

    return ""


def _sleep(base_delay):

    # Small random variation prevents requests
    # from happening at exactly fixed intervals.

    wait = (
        base_delay
        + random.uniform(
            0.5,
            1.5
        )
    )

    time.sleep(wait)


def _request_page(
    session,
    params,
    config
):

    search_cfg = config["search"]

    timeout = search_cfg[
        "timeout_seconds"
    ]

    max_retries = search_cfg.get(
        "rate_limit_retries",
        2
    )

    rate_wait = search_cfg.get(
        "rate_limit_wait_seconds",
        30
    )

    for attempt in range(
        max_retries + 1
    ):

        response = session.get(
            SEARCH_ENDPOINT,
            params=params,
            headers=HEADERS,
            timeout=timeout
        )

        if response.status_code == 200:
            return response

        if response.status_code == 429:

            print(
                "LinkedIn rate limit detected."
            )

            if attempt < max_retries:

                wait_time = (
                    rate_wait
                    * (attempt + 1)
                )

                print(
                    f"Waiting {wait_time} seconds "
                    "before retry..."
                )

                time.sleep(
                    wait_time
                )

                continue

            print(
                "LinkedIn still rate limited. "
                "Stopping LinkedIn collection."
            )

            return None

        print(
            "LinkedIn request failed:",
            response.status_code
        )

        return None

    return None


def collect(config, queries=None):

    search_cfg = config.get("search", {})

    recent_hours = search_cfg.get("linkedin_recent_hours", 24)

    max_pages = search_cfg.get(
        "linkedin_max_pages",
        10
    )

    page_size = search_cfg.get(
        "linkedin_page_size",
        25
    )

    delay = search_cfg.get(
        "request_delay_seconds",
        2
    )

    recent_seconds = int(
        recent_hours * 3600
    )

    if queries is None:
        queries = []
        profiles = config.get("profiles", {})
        active_prof = config.get("active_profile", "ALL")
        if active_prof in ("AI_ENGINEER", "ALL") and "AI_ENGINEER" in profiles and profiles["AI_ENGINEER"].get("enabled", True):
            queries.extend(profiles["AI_ENGINEER"].get("search_queries", []))
        if active_prof in ("TEST_ENGINEER", "ALL") and "TEST_ENGINEER" in profiles and profiles["TEST_ENGINEER"].get("enabled", True):
            queries.extend(profiles["TEST_ENGINEER"].get("search_queries", []))
        if not queries:
            queries = config.get("linkedin_queries", ["AI Engineer", "Automotive Test Engineer"])
    queries = list(dict.fromkeys(queries))

    session = requests.Session()

    all_jobs = []

    # Deduplicate BEFORE adding to result
    seen_job_ids = set()
    seen_urls = set()

    print(
        f"LinkedIn search window: "
        f"last {recent_hours} hours"
    )

    print(
        f"LinkedIn search queries: "
        f"{len(queries)}"
    )

    for query in queries:

        print()
        print(
            f"Searching LinkedIn: {query}"
        )

        query_total = 0

        for page in range(
            max_pages
        ):

            start = (
                page * page_size
            )

            params = {
                "keywords": query,

                # Remote
                "f_WT": "2",

                # Last 24 hours
                "f_TPR":
                    f"r{recent_seconds}",

                # Pagination
                "start": start
            }

            _sleep(
                delay
            )

            response = _request_page(
                session,
                params,
                config
            )

            if response is None:

                print(
                    "Stopping this LinkedIn run."
                )

                return all_jobs

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            cards = soup.select(
                "div.base-card"
            )

            # No more jobs means
            # pagination is complete.
            if not cards:

                print(
                    f"No more results for "
                    f"{query}."
                )

                break

            new_on_page = 0

            for card in cards:

                job_id = _get_job_id(
                    card
                )

                title = _clean(
                    card.select_one(
                        ".base-search-card__title"
                    )
                )

                company = _clean(
                    card.select_one(
                        ".base-search-card__subtitle"
                    )
                )

                location = _clean(
                    card.select_one(
                        ".job-search-card__location"
                    )
                )

                date_node = card.select_one(
                    "time"
                )

                posted_date = ""

                if date_node:

                    posted_date = (
                        date_node.get(
                            "datetime",
                            ""
                        )
                        or
                        _clean(
                            date_node
                        )
                    )

                link_node = (
                    card.select_one(
                        "a.base-card__full-link"
                    )
                )

                url = ""

                if link_node:

                    url = link_node.get(
                        "href",
                        ""
                    )

                    url = url.split(
                        "?"
                    )[0]

                if not title:
                    continue

                # -----------------------
                # DUPLICATE CHECK
                # -----------------------

                if (
                    job_id
                    and job_id in seen_job_ids
                ):
                    continue

                if (
                    url
                    and url in seen_urls
                ):
                    continue

                if job_id:
                    seen_job_ids.add(
                        job_id
                    )

                if url:
                    seen_urls.add(
                        url
                    )

                # IMPORTANT:
                # Do NOT fetch individual
                # LinkedIn job descriptions.
                #
                # This avoids hundreds of
                # extra requests and reduces
                # rate limiting.

                job = Job(
                    source="LinkedIn",
                    source_job_id=job_id,
                    title=title,
                    company=company,
                    location=location,
                    posted_date=posted_date,
                    url=url,
                    description=""
                )

                all_jobs.append(
                    job
                )

                query_total += 1
                new_on_page += 1

            print(
                f"Page {page + 1}: "
                f"{len(cards)} returned, "
                f"{new_on_page} new unique jobs"
            )

            # If LinkedIn returns fewer than
            # the normal page size, this is
            # usually the last page.
            if len(cards) < page_size:

                print(
                    f"Reached final page "
                    f"for {query}."
                )

                break

        print(
            f"{query}: "
            f"{query_total} unique jobs collected"
        )

    print()
    print(
        "Total unique LinkedIn jobs "
        f"collected: {len(all_jobs)}"
    )

    return all_jobs