import requests
import logging
from datetime import datetime
from typing import List, Dict, Any
from models import Job

API_URL = "https://remotive.com/api/remote-jobs?category=software-dev&limit=60"

def collect(config: Dict[str, Any], queries: List[str] = None) -> List[Job]:
    """
    Collects remote engineering jobs from Remotive official public API.
    """
    jobs = []
    try:
        r = requests.get(API_URL, headers={"User-Agent": "JobSearchAutomationAgent/2.0"}, timeout=15)
        if r.status_code != 200:
            logging.warning(f"Remotive API returned status {r.status_code}")
            return []

        data = r.json()
        raw_jobs = data.get("jobs", [])

        for item in raw_jobs:
            job_id = str(item.get("id", ""))
            title = item.get("title", "")
            company = item.get("company_name", "")
            location = item.get("candidate_required_location", "Worldwide Remote")
            url = item.get("url", "")
            desc = item.get("description", "")
            pub_date = item.get("publication_date", "")
            salary = item.get("salary", "")

            posted = ""
            if pub_date:
                posted = pub_date[:10]

            job = Job(
                id=job_id,
                title=title,
                company=company,
                country=location,
                city="Remote",
                work_arrangement="Remote",
                remote_eligibility=location,
                salary_range=salary,
                description=desc,
                url=url,
                source="Remotive",
                posted_date=posted,
                found_date=datetime.now().strftime("%Y-%m-%d"),
                last_seen_date=datetime.now().strftime("%Y-%m-%d"),
                status="DISCOVERED"
            )
            jobs.append(job)

        logging.info(f"Remotive API collected {len(jobs)} jobs")
    except Exception as e:
        logging.error(f"Remotive collector error: {e}")

    return jobs
