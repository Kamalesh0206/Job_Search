import os
import sys
import json
import asyncio
import logging
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Local modules
from profile_manager import ProfileManager
from cover_letter_generator import CoverLetterGenerator
from recruiter_outreach import RecruiterOutreach
from excel_writer import (
    load_all_jobs,
    update_job_status,
    update_job_application,
    migrate_if_needed
)
from apply_engine import run_apply
from main import run_job_search
from generate_resume_pdf import get_resume_path_for_profile

ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
EXCEL_PATH = ROOT / "Job_Search_Tracker.xlsx"
CONFIG_PATH = ROOT / "config.json"
USER_PROFILE_PATH = ROOT / "user_profile.json"
LOG_DIR = ROOT / "logs"

app = FastAPI(
    title="Dual-Role AI Job Search and Application Automation Agent",
    description="Dual Profile System for AI Engineer and Automotive Test Engineer",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background search and apply task states
task_states: Dict[str, Dict[str, Any]] = {
    "search": {"status": "idle", "message": "Ready", "last_run": None, "profile": "ALL", "summary": None},
    "apply": {"status": "idle", "message": "Ready", "last_run": None, "results": []}
}

# ----------------- Request Models -----------------
class StatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = None

class SearchTriggerRequest(BaseModel):
    profile: Optional[str] = "ALL"

class ApplyRequest(BaseModel):
    job_id: Any
    job_url: str
    job_title: Optional[str] = "AI Engineer"
    company_name: Optional[str] = "Target Company"
    job_description: Optional[str] = ""
    profile_id: Optional[str] = "AI_ENGINEER"
    headless: Optional[bool] = False
    dry_run: Optional[bool] = True
    auto_submit: Optional[bool] = False
    explicit_approval: Optional[bool] = False

class CoverLetterRequest(BaseModel):
    job_title: str
    company_name: str
    job_description: Optional[str] = ""
    profile_id: Optional[str] = "AI_ENGINEER"

class OutreachRequest(BaseModel):
    recruiter_name: Optional[str] = "Hiring Manager"
    company_name: Optional[str] = "Target Company"
    role_title: Optional[str] = "AI Engineer"
    profile_id: Optional[str] = "AI_ENGINEER"

class ScheduleUpdateRequest(BaseModel):
    enabled: bool
    mode: Optional[str] = "manual"
    daily_time: Optional[str] = "09:00"

# ----------------- Helper Functions -----------------
def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(data: Dict[str, Any]):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def calculate_profile_stats(jobs: List[Dict[str, Any]], profile_filter: Optional[str] = None) -> Dict[str, Any]:
    if profile_filter and profile_filter != "ALL":
        target = profile_filter.upper()
        # Include BOTH in either profile count
        filtered = [j for j in jobs if j.get("profile_id", "").upper() == target or j.get("role_category", "").upper() == "BOTH"]
    else:
        filtered = jobs

    total = len(filtered)
    relevant = sum(1 for j in filtered if int(j.get("relevance_score", 0)) >= 60)
    confirmed_sponsorship = sum(1 for j in filtered if j.get("visa_sponsorship_status", "").upper() == "CONFIRMED")
    remote_jobs = sum(1 for j in filtered if "remote" in j.get("work_arrangement", "").lower())
    applied = sum(1 for j in filtered if j.get("status", "").upper() == "APPLIED")
    interviews = sum(1 for j in filtered if j.get("status", "").upper() == "INTERVIEW")
    rejections = sum(1 for j in filtered if j.get("status", "").upper() == "REJECTED")
    ready_for_review = sum(1 for j in filtered if j.get("status", "").upper() == "READY_FOR_REVIEW")
    approved = sum(1 for j in filtered if j.get("status", "").upper() == "APPROVED")

    return {
        "total_jobs": total,
        "relevant_jobs": relevant,
        "confirmed_sponsorship": confirmed_sponsorship,
        "remote_jobs": remote_jobs,
        "applications_submitted": applied,
        "interviews": interviews,
        "rejections": rejections,
        "ready_for_review": ready_for_review,
        "approved": approved
    }

# ----------------- API Endpoints -----------------

@app.get("/api/stats")
def get_stats(profile: Optional[str] = Query("ALL")):
    migrate_if_needed(EXCEL_PATH)
    all_jobs = load_all_jobs(EXCEL_PATH)

    ai_stats = calculate_profile_stats(all_jobs, "AI_ENGINEER")
    test_stats = calculate_profile_stats(all_jobs, "TEST_ENGINEER")
    overall_stats = calculate_profile_stats(all_jobs, "ALL")

    active_stats = overall_stats
    if profile == "AI_ENGINEER":
        active_stats = ai_stats
    elif profile == "TEST_ENGINEER":
        active_stats = test_stats

    # Available countries list for filter dropdown
    countries = sorted(list({j.get("country", "").strip() for j in all_jobs if j.get("country", "").strip()}))

    return {
        "profile_selected": profile,
        "stats": active_stats,
        "ai_engineer": ai_stats,
        "test_engineer": test_stats,
        "all_profiles": overall_stats,
        "available_countries": countries,
        "search_task": task_states["search"],
        "apply_task": task_states["apply"]
    }

@app.get("/api/jobs")
def get_jobs(
    profile: Optional[str] = Query("ALL"),
    status: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    work_arrangement: Optional[str] = Query(None),
    sponsorship: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    limit: Optional[int] = Query(500)
):
    migrate_if_needed(EXCEL_PATH)
    jobs = load_all_jobs(EXCEL_PATH)

    # 1. Filter by profile
    if profile and profile != "ALL":
        p_up = profile.upper()
        jobs = [j for j in jobs if j.get("profile_id", "").upper() == p_up or j.get("role_category", "").upper() == "BOTH"]

    # 2. Filter by status
    if status and status != "All":
        s_up = status.upper()
        jobs = [j for j in jobs if j.get("status", "").upper() == s_up]

    # 3. Filter by country
    if country and country != "All":
        c_low = country.lower()
        jobs = [j for j in jobs if c_low in j.get("country", "").lower()]

    # 4. Filter by work arrangement
    if work_arrangement and work_arrangement != "All":
        w_low = work_arrangement.lower()
        jobs = [j for j in jobs if w_low in j.get("work_arrangement", "").lower()]

    # 5. Filter by sponsorship
    if sponsorship and sponsorship != "All":
        spon_up = sponsorship.upper()
        jobs = [j for j in jobs if j.get("visa_sponsorship_status", "").upper() == spon_up]

    # 6. Filter by min score
    if min_score is not None and min_score > 0:
        jobs = [j for j in jobs if int(j.get("relevance_score", 0)) >= min_score]

    # 7. Search text
    if search:
        s_lower = search.lower().strip()
        jobs = [
            j for j in jobs if (
                s_lower in j.get("title", "").lower() or
                s_lower in j.get("company", "").lower() or
                s_lower in j.get("country", "").lower() or
                s_lower in j.get("matched_skills", "").lower()
            )
        ]

    # Sort reverse chronological by Found Date, then score
    jobs.sort(key=lambda x: (x.get("found_date", ""), int(x.get("relevance_score", 0))), reverse=True)

    return {
        "count": len(jobs),
        "total_unfiltered": len(load_all_jobs(EXCEL_PATH)),
        "jobs": jobs[:limit]
    }

@app.patch("/api/jobs/{job_id}/status")
def patch_job_status(job_id: str, req: StatusUpdateRequest):
    success = update_job_status(EXCEL_PATH, job_id, req.status, notes=req.notes)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found in Excel tracker")
    return {"success": True, "job_id": job_id, "new_status": req.status}

@app.post("/api/jobs/{job_id}/approve")
def approve_job(job_id: str):
    success = update_job_status(EXCEL_PATH, job_id, "APPROVED", notes="Approved by candidate for application submission")
    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {"success": True, "job_id": job_id, "status": "APPROVED", "message": "Job approved for submission"}

@app.post("/api/jobs/{job_id}/reject")
def reject_job(job_id: str):
    success = update_job_status(EXCEL_PATH, job_id, "REJECTED", notes="Rejected by user")
    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {"success": True, "job_id": job_id, "status": "REJECTED", "message": "Job marked as rejected"}

@app.post("/api/jobs/{job_id}/generate-documents")
def generate_job_documents(job_id: str):
    jobs = load_all_jobs(EXCEL_PATH)
    target = next((j for j in jobs if str(j.get("id")) == str(job_id)), None)
    if not target:
        raise HTTPException(status_code=404, detail="Job not found")

    profile_id = target.get("profile_id", "AI_ENGINEER")
    clg = CoverLetterGenerator()
    cl_res = clg.generate(
        job_title=target.get("title", ""),
        company_name=target.get("company", ""),
        job_description=target.get("description", ""),
        profile_id=profile_id,
        save_to_disk=True
    )

    resume_p = get_resume_path_for_profile(profile_id, target.get("company", ""))
    
    # Update Excel with paths
    update_job_application(
        EXCEL_PATH,
        job_id=job_id,
        status=target.get("status", "READY_FOR_REVIEW"),
        resume_used=resume_p.name,
        cover_letter_path=cl_res.get("file_path", "")
    )

    return {
        "success": True,
        "job_id": job_id,
        "profile_id": profile_id,
        "cover_letter": cl_res.get("cover_letter", ""),
        "cover_letter_path": cl_res.get("file_path", ""),
        "resume_name": resume_p.name
    }

@app.get("/api/jobs/{job_id}/cover-letter")
def get_job_cover_letter(job_id: str):
    jobs = load_all_jobs(EXCEL_PATH)
    target = next((j for j in jobs if str(j.get("id")) == str(job_id)), None)
    if not target:
        raise HTTPException(status_code=404, detail="Job not found")

    # If already generated file exists, read it
    cl_path_str = target.get("cover_letter_path", "")
    if cl_path_str and Path(cl_path_str).exists():
        text = Path(cl_path_str).read_text(encoding="utf-8")
        return {"cover_letter": text, "file_path": cl_path_str}

    # Generate on the fly
    clg = CoverLetterGenerator()
    res = clg.generate(
        job_title=target.get("title", ""),
        company_name=target.get("company", ""),
        job_description=target.get("description", ""),
        profile_id=target.get("profile_id", "AI_ENGINEER"),
        save_to_disk=True
    )
    return res

@app.get("/api/resume/{profile_id}")
def download_role_resume(profile_id: str):
    resume_path = get_resume_path_for_profile(profile_id)
    if not resume_path.exists():
        raise HTTPException(status_code=404, detail=f"Resume not found for profile {profile_id}")
    return FileResponse(
        path=str(resume_path),
        filename=resume_path.name,
        media_type="application/pdf"
    )

@app.post("/api/cover-letter")
def generate_custom_cover_letter(req: CoverLetterRequest):
    clg = CoverLetterGenerator()
    res = clg.generate(
        job_title=req.job_title,
        company_name=req.company_name,
        job_description=req.job_description or "",
        profile_id=req.profile_id or "AI_ENGINEER",
        save_to_disk=True
    )
    return res

@app.post("/api/outreach")
def generate_outreach_api(req: OutreachRequest):
    ro = RecruiterOutreach()
    recruiter_name = req.recruiter_name or "Hiring Manager"
    company = req.company_name or "Target Company"
    role = req.role_title or "AI Engineer"

    note = ro.generate_linkedin_connection_note(recruiter_name, company)
    inmail = ro.generate_recruiter_inmail(recruiter_name, company, role)
    email_data = ro.generate_cold_email(recruiter_name, company, role)
    followup = ro.generate_followup(recruiter_name, company, role)

    return {
        "linkedin_note": note,
        "linkedin_inmail": inmail,
        "cold_email_subject": email_data["subject"],
        "cold_email_body": email_data["body"],
        "followup": followup
    }

# ----------------- Search & Apply Workers -----------------
def background_search_worker(profile_target: str):
    task_states["search"]["status"] = "running"
    task_states["search"]["profile"] = profile_target
    task_states["search"]["message"] = f"Collecting worldwide vacancies for {profile_target}..."
    try:
        summary = run_job_search(profile_target)
        task_states["search"]["status"] = "completed"
        task_states["search"]["last_run"] = summary.get("duration_seconds")
        task_states["search"]["summary"] = summary
        task_states["search"]["message"] = f"Finished: +{summary.get('new_relevant_added', 0)} new jobs added. ({summary.get('duplicates_skipped', 0)} duplicates prevented)"
    except Exception as e:
        task_states["search"]["status"] = "error"
        task_states["search"]["message"] = f"Search failed: {e}"

@app.post("/api/search")
def trigger_search(req: SearchTriggerRequest, background_tasks: BackgroundTasks):
    if task_states["search"]["status"] == "running":
        return {"status": "already_running", "message": "A job search is already active in background"}
    background_tasks.add_task(background_search_worker, req.profile or "ALL")
    return {"status": "started", "message": f"Job search started for profile {req.profile or 'ALL'}"}

def background_apply_worker(req: ApplyRequest):
    task_states["apply"]["status"] = "running"
    task_states["apply"]["message"] = f"Launching Playwright application for {req.job_title} at {req.company_name}..."
    try:
        res = run_apply(
            job_url=req.job_url,
            job_title=req.job_title,
            company_name=req.company_name,
            job_description=req.job_description,
            profile_id=req.profile_id or "AI_ENGINEER",
            headless=req.headless,
            dry_run=req.dry_run,
            auto_submit=req.auto_submit
        )
        task_states["apply"]["status"] = "completed"
        task_states["apply"]["message"] = f"Application complete: {res.get('status', 'Finished')}"
        task_states["apply"]["results"].append(res)

        if req.job_id:
            new_status = "APPLIED" if res.get("submitted") else "READY_FOR_REVIEW"
            update_job_status(EXCEL_PATH, req.job_id, new_status, notes=res.get("notes", ""))
    except Exception as e:
        task_states["apply"]["status"] = "error"
        task_states["apply"]["message"] = f"Apply engine failed: {e}"

@app.post("/api/apply")
def trigger_apply(req: ApplyRequest, background_tasks: BackgroundTasks):
    if task_states["apply"]["status"] == "running":
        return {"status": "already_running", "message": "An application is currently running"}

    # Human-in-the-loop safety verification
    if req.auto_submit and not req.explicit_approval:
        jobs = load_all_jobs(EXCEL_PATH)
        target = next((j for j in jobs if str(j.get("id")) == str(req.job_id)), None)
        if target and target.get("status") != "APPROVED":
            raise HTTPException(
                status_code=400,
                detail="Safety Guard: Job must be explicitly marked as 'APPROVED' before automatic submission."
            )

    background_tasks.add_task(background_apply_worker, req)
    return {"status": "started", "message": f"Application agent started for {req.company_name}"}

@app.get("/api/export/excel")
def export_excel():
    if not EXCEL_PATH.exists():
        raise HTTPException(status_code=404, detail="Excel tracker file not found")
    return FileResponse(
        path=str(EXCEL_PATH),
        filename="Job_Search_Tracker.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.get("/api/config")
def get_config():
    return load_config()

@app.put("/api/config")
def update_config_api(data: Dict[str, Any]):
    save_config(data)
    return {"success": True, "message": "Configuration updated"}

@app.get("/api/profile")
def get_profile_api():
    pm = ProfileManager()
    return pm.data

@app.get("/api/logs")
def get_logs():
    logs = {}
    search_log = LOG_DIR / "job_search.log"
    apply_log = LOG_DIR / "job_apply.log"
    if search_log.exists():
        with open(search_log, "r", encoding="utf-8", errors="ignore") as f:
            logs["search"] = f.readlines()[-50:]
    if apply_log.exists():
        with open(apply_log, "r", encoding="utf-8", errors="ignore") as f:
            logs["apply"] = f.readlines()[-50:]
    return logs

# ----------------- Static Mounting -----------------
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>Dashboard loading...</h1>")
    return FileResponse(str(index_file))

if __name__ == "__main__":
    import uvicorn
    import socket
    port = 8000
    host_name = socket.gethostname()
    print("\n" + "=" * 60)
    print("  Dual-Role AI Job Search & Application Automation Dashboard")
    print(f"  System Host Name : http://{host_name}:{port}")
    print(f"  Custom Host Name : http://jobagent.local:{port}")
    print(f"  Local Loopback   : http://localhost:{port}")
    print("=" * 60 + "\n")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
