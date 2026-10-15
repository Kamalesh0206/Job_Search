import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from classifier import classify_job
from scoring_engine import calculate_relevance
from cover_letter_generator import CoverLetterGenerator
from generate_resume_pdf import get_resume_path_for_profile
from excel_writer import (
    append_jobs,
    load_existing_fingerprints,
    load_all_jobs,
    update_job_last_seen
)
import database
from utils import fingerprint, company_title_fingerprint, canonical_url
from sources.remotive import collect as collect_remotive
from sources.arbeitnow import collect as collect_arbeitnow
from sources.linkedin import collect as collect_linkedin
from sources.euremotejobs import collect as collect_euremote

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
EXCEL_PATH = ROOT / "Job_Search_Tracker.xlsx"
LOG_PATH = ROOT / "logs" / "job_search.log"

def setup_logging():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(LOG_PATH),
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

def run_job_search(target_profile: Optional[str] = None) -> Dict[str, Any]:
    """
    Main job search runner supporting independent profiles:
      - 'AI_ENGINEER'
      - 'TEST_ENGINEER'
      - 'ALL'
    """
    setup_logging()
    start_time = datetime.now()
    logging.info(f"=== Job Search Started at {start_time} for Profile: {target_profile or 'ALL'} ===")

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing configuration at {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    active_profile = (target_profile or config.get("active_profile", "ALL")).upper()
    config["active_profile"] = active_profile

    # Determine search queries based on profile
    queries = []
    profiles = config.get("profiles", {})
    if active_profile in ("AI_ENGINEER", "ALL") and "AI_ENGINEER" in profiles:
        if profiles["AI_ENGINEER"].get("enabled", True):
            queries.extend(profiles["AI_ENGINEER"].get("search_queries", []))
    if active_profile in ("TEST_ENGINEER", "ALL") and "TEST_ENGINEER" in profiles:
        if profiles["TEST_ENGINEER"].get("enabled", True):
            queries.extend(profiles["TEST_ENGINEER"].get("search_queries", []))
    queries = list(dict.fromkeys(queries))

    print(f"\n========================================================")
    print(f"  Dual-Role Job Search Automation Agent")
    print(f"  Active Profile Scope: {active_profile}")
    print(f"  Target Queries: {', '.join(queries)}")
    print(f"========================================================\n")

    all_discovered = []
    source_stats = {}

    # 1. Remotive Collector (Official Public API - Worldwide Remote)
    try:
        print("[1/4] Querying Remotive Public API...")
        rem_jobs = collect_remotive(config, queries)
        all_discovered.extend(rem_jobs)
        source_stats["Remotive"] = len(rem_jobs)
        print(f"      -> Collected {len(rem_jobs)} jobs from Remotive")
    except Exception as e:
        logging.exception("Remotive collector failed")
        source_stats["Remotive"] = f"Error: {e}"
        print(f"      [!] Remotive error: {e}")

    # 2. Arbeitnow Collector (Official Public API - Germany, Europe & Global)
    try:
        print("[2/4] Querying Arbeitnow Public API (Germany/Europe/Global)...")
        arb_jobs = collect_arbeitnow(config, queries)
        all_discovered.extend(arb_jobs)
        source_stats["Arbeitnow"] = len(arb_jobs)
        print(f"      -> Collected {len(arb_jobs)} jobs from Arbeitnow")
    except Exception as e:
        logging.exception("Arbeitnow collector failed")
        source_stats["Arbeitnow"] = f"Error: {e}"
        print(f"      [!] Arbeitnow error: {e}")

    # 3. EU Remote Jobs (Public Board)
    try:
        print("[3/4] Querying EU Remote Jobs board...")
        eu_jobs = collect_euremote(config)
        all_discovered.extend(eu_jobs)
        source_stats["EURemoteJobs"] = len(eu_jobs)
        print(f"      -> Collected {len(eu_jobs)} jobs from EU Remote Jobs")
    except Exception as e:
        logging.exception("EU Remote Jobs collector failed")
        source_stats["EURemoteJobs"] = f"Error: {e}"
        print(f"      [!] EU Remote Jobs error: {e}")

    # 4. LinkedIn Guest Collector (Polite public endpoints)
    try:
        print("[4/4] Querying LinkedIn Public Listings (polite rate limits)...")
        # Run top 2 queries per run to avoid 429 rate limit
        sample_queries = queries[:3]
        li_jobs = collect_linkedin(config, queries=sample_queries)
        all_discovered.extend(li_jobs)
        source_stats["LinkedIn"] = len(li_jobs)
        print(f"      -> Collected {len(li_jobs)} jobs from LinkedIn")
    except Exception as e:
        logging.exception("LinkedIn collector failed")
        source_stats["LinkedIn"] = f"Error: {e}"
        print(f"      [!] LinkedIn error: {e}")

    print(f"\nTotal raw vacancies discovered across all sources: {len(all_discovered)}")

    # Load existing database state for deduplication
    database.init_db()
    existing_fps = database.get_existing_fingerprints()
    existing_jobs = database.get_all_jobs()
    existing_urls = {canonical_url(j.get("url", "")) for j in existing_jobs if j.get("url")}
    existing_cross = {company_title_fingerprint(j.get("company", ""), j.get("title", "")) for j in existing_jobs}

    today = datetime.now().strftime("%Y-%m-%d")
    clg = CoverLetterGenerator()

    new_relevant_rows = []
    run_seen_fps = set()
    duplicate_count = 0
    irrelevant_count = 0
    updated_last_seen = 0

    for job in all_discovered:
        fp = fingerprint(job.source, job.id, job.title, job.company, job.url)
        canon_url = canonical_url(job.url)
        cross_fp = company_title_fingerprint(job.company, job.title)

        # Check for duplicate
        if fp in existing_fps or (canon_url and canon_url in existing_urls) or cross_fp in existing_cross:
            duplicate_count += 1
            # Update last-seen timestamp on existing entry
            database.update_last_seen_db([fp], today)
            update_job_last_seen(EXCEL_PATH, fp, today)
            updated_last_seen += 1
            continue

        if fp in run_seen_fps:
            duplicate_count += 1
            continue

        run_seen_fps.add(fp)

        # Classify Job
        classification = classify_job(job.title, job.description, config, active_profile)
        category = classification["category"]

        if category == "IRRELEVANT":
            irrelevant_count += 1
            continue

        # Check if matches target active profile filter
        if active_profile != "ALL" and category != active_profile and category != "BOTH":
            continue

        profile_assigned = category if category in ("AI_ENGINEER", "TEST_ENGINEER") else "AI_ENGINEER"

        # Calculate Relevance Score
        job_dict = job.to_dict()
        scoring = calculate_relevance(job_dict, profile_assigned, config)

        # Assign resume used
        resume_p = get_resume_path_for_profile(profile_assigned, job.company)

        # Generate tailored cover letter
        cover_res = clg.generate(
            job_title=job.title,
            company_name=job.company,
            job_description=job.description,
            profile_id=profile_assigned,
            save_to_disk=True
        )

        # Automatic Application Rule Evaluation
        from apply_engine import evaluate_auto_apply_eligibility
        prof_cfg = config.get("profiles", {}).get(profile_assigned, {})
        auto_apply_allowed = prof_cfg.get("auto_apply_enabled", True)

        eligibility = evaluate_auto_apply_eligibility(
            match_score=scoring["score"],
            mandatory_pass=scoring.get("mandatory_requirements_pass", True),
            job_is_open=True,
            not_already_applied=True,
            application_data_is_valid=bool(resume_p and resume_p.exists() and job.url),
            submission_method_is_authorized=auto_apply_allowed,
            threshold=int(prof_cfg.get("match_threshold", 70))
        )

        assigned_status = eligibility["status"]

        # Prepare final row record
        row = {
            "profile_id": profile_assigned,
            "role_category": category,
            "title": job.title,
            "company": job.company,
            "country": job.country,
            "city": job.city,
            "work_arrangement": scoring["work_arrangement"],
            "remote_eligibility": job.remote_eligibility or "Worldwide",
            "visa_sponsorship_status": scoring["visa_sponsorship_status"],
            "salary_range": job.salary_range,
            "experience_required": job.experience_required or "7.4y preferred",
            "required_skills": ", ".join(scoring["matched_skills"] + scoring["missing_skills"][:3]),
            "matched_skills": ", ".join(scoring["matched_skills"]),
            "missing_skills": ", ".join(scoring["missing_skills"]),
            "description": job.description,
            "url": job.url,
            "source": job.source,
            "posted_date": job.posted_date or today,
            "found_date": today,
            "last_seen_date": today,
            "relevance_score": scoring["score"],
            "resume_used": resume_p.name if resume_p else "",
            "cover_letter_path": cover_res.get("file_path", ""),
            "status": assigned_status,
            "application_date": "",
            "recruiter_name": "",
            "recruiter_contact": "",
            "follow_up_date": "",
            "notes": f"Rule: {eligibility['reason']} | Breakdown: {scoring['explanation']}",
            "fingerprint": fp
        }
        new_relevant_rows.append(row)

    # Sort new rows by relevance score descending
    new_relevant_rows.sort(key=lambda x: (x["relevance_score"], x["found_date"]), reverse=True)

    added_count = 0
    if new_relevant_rows:
        added_count = database.save_jobs_to_db(new_relevant_rows)
        # Also ensure append_jobs in excel for backwards compatibility if needed
        try:
            append_jobs(EXCEL_PATH, new_relevant_rows)
        except Exception:
            pass

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    summary = {
        "status": "completed",
        "active_profile": active_profile,
        "total_discovered": len(all_discovered),
        "new_relevant_added": added_count,
        "duplicates_skipped": duplicate_count,
        "duplicates_last_seen_updated": updated_last_seen,
        "irrelevant_filtered": irrelevant_count,
        "source_breakdown": source_stats,
        "duration_seconds": round(duration, 2),
        "excel_path": str(EXCEL_PATH)
    }

    database.record_search_log(
        active_profile,
        "completed",
        len(all_discovered),
        added_count,
        duplicate_count,
        summary
    )

    print("\n---------------- SEARCH SUMMARY ----------------")
    print(f"Total Discovered: {summary['total_discovered']}")
    print(f"New Relevant Jobs Added: {summary['new_relevant_added']}")
    print(f"Duplicates Prevented: {summary['duplicates_skipped']} (Updated {summary['duplicates_last_seen_updated']} last-seen dates)")
    print(f"Irrelevant Filtered: {summary['irrelevant_filtered']}")
    print(f"Duration: {summary['duration_seconds']}s")
    print(f"Tracker: {EXCEL_PATH}")
    print("------------------------------------------------\n")

    logging.info(f"Search completed: {summary}")
    return summary

def main():
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "ALL"
    run_job_search(target)

if __name__ == "__main__":
    main()
