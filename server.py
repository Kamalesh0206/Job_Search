import os
import sys
import json
import asyncio
import logging
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel
import openpyxl

# Local modules
from profile_manager import ProfileManager
from cover_letter_generator import CoverLetterGenerator
from recruiter_outreach import RecruiterOutreach
from excel_writer import load_jobs_by_status, update_job_status
from apply_engine import run_apply
from main import main as run_job_search_main
import generate_resume_pdf

ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
EXCEL_PATH = ROOT / "Job_Search_Tracker.xlsx"
USER_PROFILE_PATH = ROOT / "user_profile.json"
RESUME_PDF_PATH = ROOT / "resume.pdf"
LOG_DIR = ROOT / "logs"

app = FastAPI(title="Job Search & Apply Agent Dashboard", version="1.0.0")

# Background job states
task_states: Dict[str, Dict[str, Any]] = {
    "search": {"status": "idle", "message": "Ready", "last_run": None},
    "apply": {"status": "idle", "message": "Ready", "last_run": None, "results": []}
}

# ----------------- Models -----------------
class StatusUpdateRequest(BaseModel):
    status: str

class ApplyRequest(BaseModel):
    job_url: str
    job_title: Optional[str] = "AI Engineer"
    company_name: Optional[str] = "Target Company"
    headless: Optional[bool] = False
    dry_run: Optional[bool] = True
    auto_submit: Optional[bool] = False
    job_id: Optional[Any] = None

class CoverLetterRequest(BaseModel):
    job_title: str
    company_name: str
    job_description: Optional[str] = ""

class OutreachRequest(BaseModel):
    recruiter_name: Optional[str] = "Hiring Manager"
    company_name: Optional[str] = "Target Company"
    role_title: Optional[str] = "AI Engineer"

# ----------------- Helper functions -----------------
def get_all_jobs_from_excel() -> List[Dict[str, Any]]:
    if not EXCEL_PATH.exists():
        return []
    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True)
    ws = wb["Jobs"]
    jobs = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or len(row) < 10:
            continue
        job_id, found_date, posted_date, role_category, title, company, location, source, url, status = row[:10]
        fp = row[10] if len(row) >= 11 else ""
        jobs.append({
            "id": job_id,
            "found_date": str(found_date or ""),
            "posted_date": str(posted_date or ""),
            "role_category": str(role_category or "Uncategorized"),
            "title": str(title or ""),
            "company": str(company or ""),
            "location": str(location or ""),
            "source": str(source or ""),
            "url": str(url or ""),
            "status": str(status or "New"),
            "fingerprint": str(fp or "")
        })
    wb.close()
    return jobs

# ----------------- API Endpoints -----------------
@app.get("/api/stats")
def get_stats():
    jobs = get_all_jobs_from_excel()
    total = len(jobs)
    statuses = {}
    categories = {}
    for j in jobs:
        s = j["status"]
        statuses[s] = statuses.get(s, 0) + 1
        c = j["role_category"]
        categories[c] = categories.get(c, 0) + 1

    return {
        "total": total,
        "by_status": statuses,
        "by_category": categories,
        "search_task": task_states["search"],
        "apply_task": task_states["apply"]
    }

@app.get("/api/jobs")
def get_jobs(status: Optional[str] = None, category: Optional[str] = None, search: Optional[str] = None):
    jobs = get_all_jobs_from_excel()
    
    # Filter reverse chronological by default
    jobs = list(reversed(jobs))

    if status and status != "All":
        jobs = [j for j in jobs if j["status"].lower() == status.lower()]
    if category and category != "All":
        jobs = [j for j in jobs if j["role_category"].lower() == category.lower()]
    if search:
        s_lower = search.lower()
        jobs = [j for j in jobs if s_lower in j["title"].lower() or s_lower in j["company"].lower() or s_lower in j["location"].lower()]

    return {"count": len(jobs), "jobs": jobs}

@app.patch("/api/jobs/{job_id}/status")
def patch_job_status(job_id: str, req: StatusUpdateRequest):
    success = update_job_status(EXCEL_PATH, job_id, req.status)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found in Excel tracker")
    return {"success": True, "job_id": job_id, "new_status": req.status}

@app.post("/api/cover-letter")
def generate_cover_letter_api(req: CoverLetterRequest):
    clg = CoverLetterGenerator()
    letter = clg.generate(req.job_title, req.company_name, req.job_description)
    return {"cover_letter": letter}

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

@app.get("/api/profile")
def get_profile():
    pm = ProfileManager()
    return pm.data

@app.put("/api/profile")
def update_profile(data: Dict[str, Any]):
    with open(USER_PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return {"success": True, "message": "Profile updated successfully"}

@app.get("/api/resume")
def download_resume():
    if not RESUME_PDF_PATH.exists():
        raise HTTPException(status_code=404, detail="Resume PDF not found")
    return FileResponse(
        path=str(RESUME_PDF_PATH),
        filename="Kamalesan_C_AI_Engineer_Resume.pdf",
        media_type="application/pdf"
    )

@app.post("/api/resume/regenerate")
async def regenerate_resume_api():
    try:
        await generate_resume_pdf.main()
        return {"success": True, "message": "Resume PDF regenerated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- Search & Apply Workers -----------------
def background_search_worker():
    task_states["search"]["status"] = "running"
    task_states["search"]["message"] = "Collecting new AI openings from LinkedIn & EU Remote Jobs..."
    try:
        run_job_search_main()
        task_states["search"]["status"] = "completed"
        task_states["search"]["message"] = "Search completed. Tracker updated!"
    except Exception as e:
        task_states["search"]["status"] = "error"
        task_states["search"]["message"] = f"Search failed: {e}"

@app.post("/api/search")
def trigger_search(background_tasks: BackgroundTasks):
    if task_states["search"]["status"] == "running":
        return {"status": "already_running", "message": "Job search is already in progress"}
    background_tasks.add_task(background_search_worker)
    return {"status": "started", "message": "Job search started in background"}

def background_apply_worker(req: ApplyRequest):
    task_states["apply"]["status"] = "running"
    task_states["apply"]["message"] = f"Running Playwright application for {req.job_title} at {req.company_name}..."
    try:
        res = run_apply(
            job_url=req.job_url,
            job_title=req.job_title,
            company_name=req.company_name,
            headless=req.headless,
            dry_run=req.dry_run,
            auto_submit=req.auto_submit
        )
        task_states["apply"]["status"] = "completed"
        task_states["apply"]["message"] = f"Application processed: {res.get('status', 'Finished')}"
        task_states["apply"]["results"].append(res)

        # Update status in Excel if job_id was given
        if req.job_id:
            new_status = "Applied" if res.get("submitted") else "Review"
            update_job_status(EXCEL_PATH, req.job_id, new_status)
    except Exception as e:
        task_states["apply"]["status"] = "error"
        task_states["apply"]["message"] = f"Apply agent failed: {e}"

@app.post("/api/apply")
def trigger_apply(req: ApplyRequest, background_tasks: BackgroundTasks):
    if task_states["apply"]["status"] == "running":
        return {"status": "already_running", "message": "An application is already running in the agent"}
    background_tasks.add_task(background_apply_worker, req)
    return {"status": "started", "message": f"Apply agent launched for {req.company_name}"}

@app.get("/api/logs")
def get_logs():
    logs = {}
    search_log = LOG_DIR / "job_search.log"
    apply_log = LOG_DIR / "job_apply.log"
    if search_log.exists():
        with open(search_log, "r", encoding="utf-8", errors="ignore") as f:
            logs["search"] = f.readlines()[-40:]
    if apply_log.exists():
        with open(apply_log, "r", encoding="utf-8", errors="ignore") as f:
            logs["apply"] = f.readlines()[-40:]
    return logs

# ----------------- Static Mounting -----------------
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>Dashboard frontend loading...</h1>")
    return FileResponse(str(index_file))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
