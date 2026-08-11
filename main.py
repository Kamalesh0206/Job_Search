import json
import logging
from datetime import datetime
from pathlib import Path

from classifier import classify_job
from excel_writer import append_jobs, load_existing_fingerprints
from utils import fingerprint
from sources.linkedin import collect as collect_linkedin
from sources.euremotejobs import collect as collect_euremote

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
EXCEL_PATH = ROOT / "Job_Search_Tracker.xlsx"
LOG_PATH = ROOT / "logs" / "job_search.log"

def setup_logging():
    LOG_PATH.parent.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

def main():
    setup_logging()
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    print("Collecting jobs...")
    all_jobs = []

    try:
        jobs = collect_linkedin(config)
        print(f"LinkedIn collected: {len(jobs)}")
        all_jobs.extend(jobs)
    except Exception as e:
        logging.exception("LinkedIn collector failed")
        print(f"LinkedIn collector error: {e}")

    try:
        jobs = collect_euremote(config)
        print(f"EU Remote Jobs collected: {len(jobs)}")
        all_jobs.extend(jobs)
    except Exception as e:
        logging.exception("EU Remote Jobs collector failed")
        print(f"EU Remote Jobs collector error: {e}")

    existing = load_existing_fingerprints(EXCEL_PATH)
    today = datetime.now().strftime("%Y-%m-%d")
    new_rows = []
    run_seen = set()

    for job in all_jobs:
        category = classify_job(job.title, job.description, config)
        if not category:
            continue

        fp = fingerprint(job.source, job.source_job_id, job.title, job.company, job.url)
        if fp in existing or fp in run_seen:
            continue

        run_seen.add(fp)
        job.role_category = category
        job.found_date = today

        row = job.to_dict()
        row["fingerprint"] = fp
        new_rows.append(row)

    # Sort so Excel is easy to scan date-wise and role-wise.
    new_rows.sort(key=lambda x: (x["found_date"], x["role_category"], x["company"], x["title"]))

    if new_rows:
        append_jobs(EXCEL_PATH, new_rows)

    print(f"Relevant new jobs added: {len(new_rows)}")
    print(f"Excel: {EXCEL_PATH}")
    logging.info("Run complete. Collected=%s RelevantNew=%s", len(all_jobs), len(new_rows))

if __name__ == "__main__":
    main()
