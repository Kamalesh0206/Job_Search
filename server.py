import os
import sys
import json
import asyncio
import logging
import base64
import secrets
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Request, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

# Local modules
from profile_manager import ProfileManager
from cover_letter_generator import CoverLetterGenerator
from recruiter_outreach import RecruiterOutreach
from apply_engine import run_apply
from main import run_job_search
from generate_resume_pdf import get_resume_path_for_profile
from scheduler import scheduler_instance
import database

ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
EXCEL_PATH = ROOT / "Job_Search_Tracker.xlsx"
CONFIG_PATH = ROOT / "config.json"
USER_PROFILE_PATH = ROOT / "user_profile.json"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("server")

# Security configuration
DASHBOARD_USERNAME = os.environ.get("DASHBOARD_USERNAME", "").strip()
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "").strip()
AUTH_REQUIRED = bool(DASHBOARD_PASSWORD)

# In-memory session tokens for authenticated dashboard sessions
active_tokens = set()

security_basic = HTTPBasic(auto_error=False)

def verify_authentication(request: Request, credentials: Optional[HTTPBasicCredentials] = Depends(security_basic)):
    if not AUTH_REQUIRED:
        return True

    # 1. Check Bearer / custom token header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        if token in active_tokens:
            return True

    # 2. Check HTTP Basic credentials
    if credentials:
        user_match = secrets.compare_digest(credentials.username, DASHBOARD_USERNAME or "admin")
        pass_match = secrets.compare_digest(credentials.password, DASHBOARD_PASSWORD)
        if user_match and pass_match:
            return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Authentication required to access private application records.",
        headers={"WWW-Authenticate": "Basic"}
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing persistent database layer...")
    database.init_db()
    logger.info("Starting background cloud job search scheduler...")
    scheduler_instance.start()
    yield
    # Shutdown
    logger.info("Stopping background cloud scheduler...")
    scheduler_instance.stop()

app = FastAPI(
    title="Dual-Role AI Job Search and Application Automation Agent",
    description="Cloud-Ready Dual Profile System for AI Engineer and Automotive Test Engineer",
    version="2.1.0",
    lifespan=lifespan
)

# Dynamic CORS configuration
cors_origins_env = os.environ.get("CORS_ORIGINS", "").strip()
if cors_origins_env and cors_origins_env != "*":
    allow_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
    allow_credentials = True
else:
    allow_origins = ["*"]
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
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
    headless: Optional[bool] = None
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
    interval_hours: Optional[float] = 12.0

class LoginRequest(BaseModel):
    username: str
    password: str

class AutoApplyToggleRequest(BaseModel):
    enabled: bool

# ----------------- Helper Functions -----------------
def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(data: Dict[str, Any]):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ----------------- Health & Auth Endpoints -----------------

@app.get("/health")
@app.get("/api/health")
def health_check():
    db_status = "healthy"
    job_count = 0
    try:
        all_jobs = database.get_all_jobs(limit=1)
        # Check total count
        job_count = len(database.get_all_jobs())
    except Exception as e:
        db_status = f"unhealthy: {e}"

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "total_jobs_stored": job_count,
        "scheduler": scheduler_instance.get_status(),
        "active_profiles": ["AI_ENGINEER", "TEST_ENGINEER"],
        "auth_required": AUTH_REQUIRED,
        "environment": os.environ.get("ENVIRONMENT", "production" if os.environ.get("PORT") else "development"),
        "version": "2.4.0"
    }

@app.get("/api/auth/status")
def auth_status(request: Request):
    if not AUTH_REQUIRED:
        return {"auth_required": False, "authenticated": True}

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        tok = auth_header.split(" ", 1)[1].strip()
        if tok in active_tokens:
            return {"auth_required": True, "authenticated": True}

    return {"auth_required": True, "authenticated": False}

@app.post("/api/auth/login")
def auth_login(req: LoginRequest):
    if not AUTH_REQUIRED:
        return {"success": True, "token": "open_access"}

    user_match = secrets.compare_digest(req.username, DASHBOARD_USERNAME or "admin")
    pass_match = secrets.compare_digest(req.password, DASHBOARD_PASSWORD)

    if user_match and pass_match:
        token = secrets.token_hex(24)
        active_tokens.add(token)
        return {"success": True, "token": token, "username": req.username}

    raise HTTPException(status_code=401, detail="Invalid username or password")

# ----------------- Protected API Endpoints -----------------

@app.get("/api/stats")
def get_stats(profile: Optional[str] = Query("ALL"), _: bool = Depends(verify_authentication)):
    stats_data = database.get_stats_db(profile)
    stats_data["search_task"] = task_states["search"]
    stats_data["apply_task"] = task_states["apply"]
    stats_data["scheduler"] = scheduler_instance.get_status()
    return stats_data

@app.get("/api/jobs")
def get_jobs(
    profile: Optional[str] = Query("ALL"),
    status: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    work_arrangement: Optional[str] = Query(None),
    sponsorship: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    posting_date: Optional[str] = Query(None),
    limit: Optional[int] = Query(500),
    include_all_scores: bool = Query(False, description="Set true to include jobs with score < 69"),
    _: bool = Depends(verify_authentication)
):
    # Enforce minimum threshold: never show jobs with score < 69 unless explicitly requested
    effective_min_score = min_score
    if not include_all_scores:
        if effective_min_score is None or effective_min_score < 69:
            effective_min_score = 69

    jobs = database.get_all_jobs(
        profile_id=profile,
        status=status,
        country=country,
        work_arrangement=work_arrangement,
        sponsorship=sponsorship,
        min_score=effective_min_score,
        search=search,
        posting_date=posting_date,
        limit=limit
    )

    total_unfiltered = len(database.get_all_jobs())

    return {
        "count": len(jobs),
        "total_unfiltered": total_unfiltered,
        "jobs": jobs
    }

@app.patch("/api/jobs/{job_id}/status")
def patch_job_status(job_id: str, req: StatusUpdateRequest, _: bool = Depends(verify_authentication)):
    success = database.update_job_status_db(job_id, req.status, notes=req.notes)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {"success": True, "job_id": job_id, "new_status": req.status}

@app.post("/api/jobs/{job_id}/approve")
def approve_job(job_id: str, _: bool = Depends(verify_authentication)):
    success = database.update_job_status_db(job_id, "APPROVED", notes="Approved by candidate for application submission")
    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {"success": True, "job_id": job_id, "status": "APPROVED", "message": "Job approved for submission"}

@app.post("/api/jobs/{job_id}/reject")
def reject_job(job_id: str, _: bool = Depends(verify_authentication)):
    success = database.update_job_status_db(job_id, "REJECTED", notes="Rejected by user")
    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {"success": True, "job_id": job_id, "status": "REJECTED", "message": "Job marked as rejected"}

@app.post("/api/jobs/{job_id}/generate-documents")
def generate_job_documents(job_id: str, _: bool = Depends(verify_authentication)):
    target = database.get_job_by_id(job_id)
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

    database.update_job_application_db(
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
def get_job_cover_letter(job_id: str, _: bool = Depends(verify_authentication)):
    target = database.get_job_by_id(job_id)
    if not target:
        raise HTTPException(status_code=404, detail="Job not found")

    cl_path_str = target.get("cover_letter_path", "")
    if cl_path_str and Path(cl_path_str).exists():
        text = Path(cl_path_str).read_text(encoding="utf-8")
        return {"cover_letter": text, "file_path": cl_path_str}

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
def download_role_resume(
    profile_id: str,
    download: bool = Query(False, description="Set true to force browser download as attachment"),
    _: bool = Depends(verify_authentication)
):
    resume_path = get_resume_path_for_profile(profile_id)
    if not resume_path.exists():
        raise HTTPException(status_code=404, detail=f"Resume not found for profile {profile_id}")
    return FileResponse(
        path=str(resume_path),
        filename=resume_path.name,
        media_type="application/pdf",
        content_disposition_type="attachment" if download else "inline"
    )

@app.post("/api/cover-letter")
def generate_custom_cover_letter(req: CoverLetterRequest, _: bool = Depends(verify_authentication)):
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
def generate_outreach_api(req: OutreachRequest, _: bool = Depends(verify_authentication)):
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
def trigger_search(req: SearchTriggerRequest, background_tasks: BackgroundTasks, _: bool = Depends(verify_authentication)):
    if task_states["search"]["status"] == "running":
        return {"status": "already_running", "message": "A job search is already active in background"}
    background_tasks.add_task(background_search_worker, req.profile or "ALL")
    return {"status": "started", "message": f"Job search started for profile {req.profile or 'ALL'}"}

def background_apply_worker(req: ApplyRequest):
    task_states["apply"]["status"] = "running"
    task_states["apply"]["message"] = f"Launching application assistant for {req.job_title} at {req.company_name}..."

    # In cloud environments without X11/display, force headless = True
    is_cloud = bool(os.environ.get("PORT") or os.environ.get("ENVIRONMENT") == "production")
    effective_headless = True if (req.headless is None and is_cloud) else bool(req.headless)

    try:
        res = run_apply(
            job_url=req.job_url,
            job_title=req.job_title,
            company_name=req.company_name,
            job_description=req.job_description,
            profile_id=req.profile_id or "AI_ENGINEER",
            headless=effective_headless,
            dry_run=req.dry_run,
            auto_submit=req.auto_submit
        )
        task_states["apply"]["status"] = "completed"
        task_states["apply"]["message"] = f"Application complete: {res.get('status', 'Finished')}"
        task_states["apply"]["results"].append(res)

        if req.job_id:
            # Set status strictly: APPLIED only if submitted is True
            if res.get("submitted"):
                new_status = "APPLIED"
            elif res.get("status") == "MANUAL_ACTION_REQUIRED":
                new_status = "MANUAL_ACTION_REQUIRED"
            elif res.get("status") == "SUBMISSION_FAILED":
                new_status = "SUBMISSION_FAILED"
            else:
                new_status = "READY_TO_APPLY"

            database.update_job_application_db(
                job_id=req.job_id,
                status=new_status,
                resume_used=res.get("resume_used"),
                cover_letter_path=res.get("cover_letter_path"),
                notes=res.get("notes") or res.get("error_details", ""),
                submission_timestamp=res.get("submission_timestamp"),
                submission_response=res.get("submission_response"),
                error_details=res.get("error_details")
            )
    except Exception as e:
        task_states["apply"]["status"] = "error"
        task_states["apply"]["message"] = f"Apply engine failed: {e}"
        if req.job_id:
            database.update_job_application_db(
                job_id=req.job_id,
                status="SUBMISSION_FAILED",
                error_details=str(e),
                notes=f"Submission error: {e}"
            )

@app.post("/api/apply")
def trigger_apply(req: ApplyRequest, background_tasks: BackgroundTasks, _: bool = Depends(verify_authentication)):
    if task_states["apply"]["status"] == "running":
        return {"status": "already_running", "message": "An application is currently running"}

    # Automatic application eligibility verification
    from apply_engine import evaluate_auto_apply_eligibility
    from profile_manager import ProfileManager

    pm = ProfileManager()
    target = database.get_job_by_id(req.job_id) if req.job_id else None
    prof_id = req.profile_id or (target.get("profile_id") if target else "AI_ENGINEER")
    prof_id = pm.normalize_profile_id(prof_id)
    prof_cfg = pm.get_profile(prof_id)
    backend_auto_enabled = bool(prof_cfg.get("auto_apply_enabled", False))

    if req.auto_submit and not req.explicit_approval:
        # Backend validation check 1: Profile-level auto_apply_enabled
        if not backend_auto_enabled:
            raise HTTPException(
                status_code=400,
                detail=f"Auto-Apply Guard: Automatic submission is disabled for {prof_id} in backend configuration."
            )

        # Backend validation check 2: Daily application limit
        daily_count = database.get_daily_applied_count(prof_id)
        max_daily = int(prof_cfg.get("max_applications_per_day", 10))
        if daily_count >= max_daily:
            raise HTTPException(
                status_code=400,
                detail=f"Auto-Apply Guard: Daily application limit ({max_daily}) reached for {prof_id} ({daily_count} submitted today)."
            )

        # Backend validation check 3: Vacancy scoring and qualification checks
        if target:
            match_score = int(target.get("relevance_score", 0))
            threshold = int(prof_cfg.get("match_threshold", 70))
            has_mandatory_gap = bool(target.get("missing_skills") and "mandatory" in str(target.get("notes", "")).lower())

            elig = evaluate_auto_apply_eligibility(
                match_score=match_score,
                mandatory_pass=not has_mandatory_gap,
                job_is_open=True,
                not_already_applied=target.get("application_status") != "APPLIED",
                application_data_is_valid=True,
                submission_method_is_authorized=backend_auto_enabled,
                threshold=threshold,
                daily_limit_reached=(daily_count >= max_daily)
            )
            if not elig["eligible"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Auto-Apply Guard: {elig['reason']}"
                )

    background_tasks.add_task(background_apply_worker, req)
    return {"status": "started", "message": f"Application assistant started for {req.company_name}"}

@app.get("/api/export/excel")
def export_excel(_: bool = Depends(verify_authentication)):
    database.export_to_excel_file(EXCEL_PATH)
    if not EXCEL_PATH.exists():
        raise HTTPException(status_code=404, detail="Excel tracker file could not be generated")
    return FileResponse(
        path=str(EXCEL_PATH),
        filename="Job_Search_Tracker.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.get("/api/config")
def get_config(_: bool = Depends(verify_authentication)):
    return load_config()

@app.put("/api/config")
def update_config_api(data: Dict[str, Any], _: bool = Depends(verify_authentication)):
    save_config(data)
    return {"success": True, "message": "Configuration updated"}

@app.get("/api/profiles")
def get_all_profiles_api(_: bool = Depends(verify_authentication)):
    pm = ProfileManager()
    return pm.get_all_profiles()

@app.get("/api/profiles/{profile_id}")
def get_single_profile_api(profile_id: str, _: bool = Depends(verify_authentication)):
    pm = ProfileManager()
    norm = pm.normalize_profile_id(profile_id)
    return pm.get_profile(norm)

@app.put("/api/profiles/{profile_id}")
def update_single_profile_api(profile_id: str, updates: Dict[str, Any], _: bool = Depends(verify_authentication)):
    pm = ProfileManager()
    norm = pm.normalize_profile_id(profile_id)
    updated = pm.update_profile(norm, updates)
    return {"success": True, "profile_id": norm, "profile": updated}

@app.post("/api/profiles/{profile_id}/auto-apply")
def toggle_profile_auto_apply(profile_id: str, req: AutoApplyToggleRequest, _: bool = Depends(verify_authentication)):
    pm = ProfileManager()
    norm = pm.normalize_profile_id(profile_id)
    updated = pm.update_profile(norm, {"auto_apply_enabled": req.enabled})
    return {
        "success": True,
        "profile_id": norm,
        "auto_apply_enabled": updated.get("auto_apply_enabled", False),
        "message": f"Automatic application for {norm} set to {'ON' if req.enabled else 'OFF'}"
    }

@app.post("/api/profiles/{profile_id}/reset")
def reset_single_profile_api(profile_id: str, _: bool = Depends(verify_authentication)):
    pm = ProfileManager()
    norm = pm.normalize_profile_id(profile_id)
    reset_profile = pm.reset_to_defaults(norm)
    return {"success": True, "profile_id": norm, "profile": reset_profile}

@app.get("/api/profile")
def get_profile_api(_: bool = Depends(verify_authentication)):
    pm = ProfileManager()
    return pm.data

@app.get("/api/logs")
def get_logs(_: bool = Depends(verify_authentication)):
    logs = {}
    search_log = LOG_DIR / "job_search.log"
    apply_log = LOG_DIR / "job_apply.log"
    if search_log.exists():
        with open(search_log, "r", encoding="utf-8", errors="ignore") as f:
            logs["search"] = f.readlines()[-50:]
    if apply_log.exists():
        with open(apply_log, "r", encoding="utf-8", errors="ignore") as f:
            logs["apply"] = f.readlines()[-50:]

    logs["search_db_history"] = database.get_search_logs(20)
    return logs

@app.get("/api/schedule")
def get_schedule(_: bool = Depends(verify_authentication)):
    return scheduler_instance.get_status()

@app.post("/api/schedule")
def update_schedule(req: ScheduleUpdateRequest, _: bool = Depends(verify_authentication)):
    conf = load_config()
    conf.setdefault("schedule", {})
    conf["schedule"]["enabled"] = req.enabled
    conf["schedule"]["interval_hours"] = req.interval_hours
    save_config(conf)
    return {"success": True, "scheduler": scheduler_instance.get_status()}

@app.post("/api/schedule/run-now")
def run_schedule_now(background_tasks: BackgroundTasks, _: bool = Depends(verify_authentication)):
    if scheduler_instance._is_executing:
        return {"status": "already_running", "message": "A scheduled job search cycle is already active"}
    background_tasks.add_task(scheduler_instance.execute_search_cycle)
    return {"status": "started", "message": "Immediate dual-profile cloud search cycle launched in background."}

# ----------------- Static Mounting & SPA Fallback -----------------
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>Dual-Role AI Job Search Dashboard loading...</h1>")
    return FileResponse(
        str(index_file),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    is_cloud = bool(os.environ.get("PORT"))

    print("\n" + "=" * 65)
    print("  Dual-Role AI Job Search & Application Automation Dashboard")
    print(f"  Mode             : {'Public Cloud Host' if is_cloud else 'Local Development'}")
    print(f"  Binding Address  : http://{host}:{port}")
    print(f"  Authentication   : {'Enabled (Protected)' if AUTH_REQUIRED else 'Open (Local)'}")
    print(f"  Database Storage : {'PostgreSQL' if os.environ.get('DATABASE_URL') else 'SQLite Persistent Volume'}")
    print("=" * 65 + "\n")

    uvicorn.run("server:app", host=host, port=port, reload=False)
