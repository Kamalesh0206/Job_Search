import argparse
import logging
from pathlib import Path
from apply_engine import run_apply
from excel_writer import load_jobs_by_status, update_job_status
from profile_manager import ProfileManager

ROOT = Path(__file__).resolve().parent
EXCEL_PATH = ROOT / "Job_Search_Tracker.xlsx"
LOG_PATH = ROOT / "logs" / "job_apply.log"

def setup_logging():
    LOG_PATH.parent.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Agent Jobs Apply - Automated Job Application Assistant")
    parser.add_argument("--url", type=str, help="Apply directly to a job URL")
    parser.add_argument("--id", type=str, help="Apply to a specific Job ID from Job_Search_Tracker.xlsx")
    parser.add_argument("--batch", action="store_true", help="Batch apply to pending jobs from Excel tracker")
    parser.add_argument("--status-filter", type=str, default="New,Review", help="Comma-separated statuses to process (default: New,Review)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode (default: false / headed for review)")
    parser.add_argument("--submit", action="store_true", help="Auto-submit applications after filling (default: false / dry-run)")

    args = parser.parse_args()

    print("=========================================")
    print("      AGENT JOBS APPLY ASSISTANT         ")
    print("=========================================")

    pm = ProfileManager()
    if not pm.data or not pm.get_full_name():
        print("[!] Candidate profile is incomplete or missing. Please check user_profile.json.")
        return

    print(f"Applicant: {pm.get_full_name()} ({pm.personal.get('email')})")
    resume_p = pm.get_resume_absolute_path()
    if resume_p:
        print(f"Resume:    {resume_p.name} (Found)")
    else:
        print("[!] Resume file not found at path configured in user_profile.json")

    dry_run = not args.submit
    print(f"Mode:      {'Auto-Submit' if args.submit else 'Interactive / Dry-Run (Form Filled for Review)'}")
    print(f"Browser:   {'Headless' if args.headless else 'Headed (Visible Browser)'}\n")

    if args.url:
        print(f"Processing URL: {args.url}")
        res = run_apply(
            job_url=args.url,
            job_title="Custom Job",
            company_name="Target Company",
            headless=args.headless,
            dry_run=dry_run,
            auto_submit=args.submit
        )
        print(f"Result: {res}")

    elif args.id:
        jobs = load_jobs_by_status(EXCEL_PATH, target_statuses=["New", "Review", "Applied", "Interview", "Skip"])
        matching = [j for j in jobs if str(j["id"]) == str(args.id)]
        if not matching:
            print(f"[!] Job ID {args.id} not found in {EXCEL_PATH.name}")
            return
        job = matching[0]
        print(f"Processing Job #{job['id']}: {job['title']} at {job['company']}")
        res = run_apply(
            job_url=job["url"],
            job_title=job["title"],
            company_name=job["company"],
            headless=args.headless,
            dry_run=dry_run,
            auto_submit=args.submit
        )
        new_status = "Applied" if res.get("submitted") else "Review"
        update_job_status(EXCEL_PATH, job["id"], new_status)
        print(f"Tracker updated: Job #{job['id']} -> Status: {new_status}")

    elif args.batch:
        statuses = [s.strip() for s in args.status_filter.split(",")]
        jobs = load_jobs_by_status(EXCEL_PATH, target_statuses=statuses)
        if not jobs:
            print(f"No pending jobs found with status in ({', '.join(statuses)}) in {EXCEL_PATH.name}")
            return
        print(f"Found {len(jobs)} pending jobs to process.\n")
        for idx, job in enumerate(jobs, 1):
            print(f"[{idx}/{len(jobs)}] Job #{job['id']}: {job['title']} @ {job['company']}")
            res = run_apply(
                job_url=job["url"],
                job_title=job["title"],
                company_name=job["company"],
                headless=args.headless,
                dry_run=dry_run,
                auto_submit=args.submit
            )
            new_status = "Applied" if res.get("submitted") else "Review"
            update_job_status(EXCEL_PATH, job["id"], new_status)
            print(f"    -> Outcome: {res.get('notes')}")
            print(f"    -> Updated status: {new_status}\n")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
