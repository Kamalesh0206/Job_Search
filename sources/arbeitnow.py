import requests
import logging
from datetime import datetime
from typing import List, Dict, Any
from models import Job

API_URL = "https://www.arbeitnow.com/api/job-board-api"

def collect(config: Dict[str, Any], queries: List[str] = None) -> List[Job]:
    """
    Collects European and worldwide jobs (with heavy presence in Germany, Netherlands, Remote)
    from Arbeitnow official public API.
    """
    jobs = []
    try:
        r = requests.get(API_URL, headers={"User-Agent": "JobSearchAutomationAgent/2.0"}, timeout=15)
        if r.status_code != 200:
            logging.warning(f"Arbeitnow API returned status {r.status_code}")
            return []

        data = r.json()
        raw_jobs = data.get("data", [])

        for item in raw_jobs[:80]: # Collect top relevant batch
            slug = item.get("slug", "")
            title = item.get("title", "")
            company = item.get("company_name", "")
            location = item.get("location", "")
            url = item.get("url", "")
            desc = item.get("description", "")
            is_remote = item.get("remote", False)
            created_at = item.get("created_at", 0)

            posted = ""
            if created_at:
                try:
                    posted = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d")
                except Exception:
                    posted = ""

            visa_sponsorship = "CONFIRMED" if "visa" in item.get("tags", []) or "visa sponsorship" in desc.lower() else "UNKNOWN"

            job = Job(
                id=slug,
                title=title,
                company=company,
                country=location if location else ("Germany" if not is_remote else "Remote"),
                city=location,
                work_arrangement="Remote" if is_remote else "Hybrid / On-site",
                remote_eligibility="Remote" if is_remote else "Local / Relocation",
                visa_sponsorship_status=visa_sponsorship,
                description=desc,
                url=url,
                source="Arbeitnow",
                posted_date=posted,
                found_date=datetime.now().strftime("%Y-%m-%d"),
                last_seen_date=datetime.now().strftime("%Y-%m-%d"),
                status="DISCOVERED"
            )
            jobs.append(job)

        logging.info(f"Arbeitnow API collected {len(jobs)} jobs")
    except Exception as e:
        logging.error(f"Arbeitnow collector error: {e}")

    return jobs
