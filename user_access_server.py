import os
import sys
import json
import socket
import platform
import subprocess
import datetime
import ctypes
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "user_access_static"
DB_PATH = ROOT / "user_access_db.json"

app = FastAPI(
    title="User Access & Host Management Dashboard",
    description="Enterprise User Access Control & Host Name Management Portal",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_db() -> Dict[str, Any]:
    if not DB_PATH.exists():
        return {"system": {}, "users": [], "roles": [], "activity_logs": [], "tokens": []}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data: Dict[str, Any]):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def log_activity(action: str, target: str, user: str = "Admin", ip: str = "127.0.0.1", severity: str = "info", status: str = "Success"):
    try:
        db = load_db()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_id = f"act-{len(db.get('activity_logs', [])) + 1:03d}"
        entry = {
            "id": new_id,
            "timestamp": now_str,
            "user": user,
            "action": action,
            "target": target,
            "ip": ip,
            "status": status,
            "severity": severity
        }
        db.setdefault("activity_logs", []).insert(0, entry)
        db["activity_logs"] = db["activity_logs"][:100]  # keep latest 100
        save_db(db)
    except Exception as e:
        print(f"Error logging activity: {e}")

def is_admin_user() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

def get_system_uptime() -> str:
    try:
        millis = ctypes.windll.kernel32.GetTickCount64()
        seconds = int(millis / 1000)
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        return f"{hours}h {minutes}m"
    except Exception:
        return "Unknown"

def get_ip_addresses() -> List[str]:
    ips = ["127.0.0.1"]
    try:
        hostname = socket.gethostname()
        _, _, addrs = socket.gethostbyname_ex(hostname)
        for a in addrs:
            if a not in ips:
                ips.append(a)
    except Exception:
        pass
    return ips

# ----------------- Models -----------------
class HostnameChangeRequest(BaseModel):
    new_hostname: str
    user_confirmed: Optional[bool] = False

class CreateUserRequest(BaseModel):
    username: str
    full_name: str
    email: str
    role: str
    department: Optional[str] = "General"
    status: Optional[str] = "Active"
    two_factor: Optional[bool] = False

class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None
    two_factor: Optional[bool] = None

class CreateTokenRequest(BaseModel):
    name: str
    role: str

# ----------------- System & Hostname APIs -----------------
@app.get("/api/system/info")
def get_system_info():
    current_hostname = socket.gethostname()
    db = load_db()
    
    # Check if a pending rename was initiated
    sys_meta = db.get("system", {})
    users_list = db.get("users", [])
    active_users = sum(1 for u in users_list if u.get("status") == "Active")

    return {
        "hostname": current_hostname,
        "computer_name": os.environ.get("COMPUTERNAME", current_hostname),
        "username": os.environ.get("USERNAME", "softk"),
        "os_name": f"{platform.system()} {platform.release()}",
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "uptime": get_system_uptime(),
        "is_admin": is_admin_user(),
        "ip_addresses": get_ip_addresses(),
        "last_hotfix": sys_meta.get("last_update", "KB5129195 (05-10-2026)"),
        "last_rename_attempt": sys_meta.get("last_rename_attempt"),
        "total_users": len(users_list),
        "active_users": active_users,
        "status": "Operational"
    }

def validate_hostname_rules(name: str):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Host name cannot be empty.")
    if len(name) > 15:
        raise HTTPException(
            status_code=400, 
            detail=f"Windows NetBIOS host names must be 15 characters or fewer (entered {len(name)} chars)."
        )
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9]$", name) and len(name) > 1:
        raise HTTPException(
            status_code=400,
            detail="Host name must contain only alphanumeric characters and hyphens, and cannot start or end with a hyphen."
        )
    if len(name) == 1 and not re.match(r"^[A-Za-z0-9]$", name):
        raise HTTPException(status_code=400, detail="Host name must be alphanumeric.")
    return name

@app.post("/api/system/hostname/validate")
def validate_hostname(req: HostnameChangeRequest):
    valid_name = validate_hostname_rules(req.new_hostname)
    current = socket.gethostname()
    return {
        "valid": True,
        "new_hostname": valid_name,
        "current_hostname": current,
        "is_different": valid_name.lower() != current.lower()
    }

@app.post("/api/system/hostname/rename")
def request_hostname_rename(req: HostnameChangeRequest):
    new_name = validate_hostname_rules(req.new_hostname)
    current = socket.gethostname()
    
    if new_name.lower() == current.lower():
        raise HTTPException(status_code=400, detail=f"The new host name '{new_name}' is already the current host name.")

    admin = is_admin_user()
    
    # Prepare Windows commands
    ps_elevated_script = f"Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -Command Rename-Computer -NewName \"{new_name}\" -Force; Write-Host \"[SUCCESS] Computer successfully renamed to {new_name}. Restart your PC for changes to take effect.\"; pause'"
    cmd_admin_command = f"wmic computersystem where caption='%COMPUTERNAME%' rename {new_name}"
    ps_direct_command = f"Rename-Computer -NewName \"{new_name}\" -Force"

    db = load_db()
    db.setdefault("system", {})["last_rename_attempt"] = {
        "requested_name": new_name,
        "requested_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Initiated"
    }
    save_db(db)

    # If running directly with administrator rights, execute directly
    if admin:
        try:
            cmd = f'powershell.exe -NoProfile -Command "Rename-Computer -NewName \'{new_name}\' -Force -ErrorAction Stop"'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                log_activity("Rename Computer Hostname", f"Changed from {current} to {new_name}", severity="warning")
                return {
                    "success": True,
                    "applied_directly": True,
                    "new_hostname": new_name,
                    "restart_required": True,
                    "message": f"Successfully renamed host to '{new_name}'. A computer restart is required to complete the change."
                }
            else:
                err_msg = res.stderr or res.stdout
                raise Exception(err_msg)
        except Exception as e:
            # Fall back to elevation workflow
            pass

    log_activity("Hostname Rename Requested", f"Target: {new_name} (Requires Elevation)", severity="info")
    return {
        "success": False,
        "applied_directly": False,
        "requires_elevation": True,
        "new_hostname": new_name,
        "current_hostname": current,
        "message": f"Renaming Windows host to '{new_name}' requires Administrator elevation.",
        "commands": {
            "powershell_elevated": ps_elevated_script,
            "cmd_admin": cmd_admin_command,
            "powershell_direct": ps_direct_command
        }
    }

@app.post("/api/system/hostname/launch-elevation")
def launch_elevation_prompt(req: HostnameChangeRequest):
    new_name = validate_hostname_rules(req.new_hostname)
    current = socket.gethostname()
    
    # Trigger Windows UAC popup via Start-Process powershell -Verb RunAs
    # This pops up the native Windows elevation modal for the user to confirm!
    ps_args = f"-NoProfile -Command \"Rename-Computer -NewName '{new_name}' -Force; Write-Host ''; Write-Host '===================================================' -ForegroundColor Green; Write-Host ' [SUCCESS] Computer Host Name Updated to: {new_name}' -ForegroundColor Green; Write-Host '===================================================' -ForegroundColor Green; Write-Host ''; Write-Host 'Note: Windows requires a system restart for this host name to take effect.' -ForegroundColor Yellow; Write-Host ''; Write-Host 'Press any key to close this window...'; [Console]::ReadKey() | Out-Null\""
    
    full_cmd = f"powershell.exe -NoProfile -Command \"Start-Process powershell.exe -Verb RunAs -ArgumentList '{ps_args}'\""
    
    try:
        subprocess.Popen(full_cmd, shell=True)
        log_activity("Elevated Hostname UAC Prompt", f"Triggered Windows UAC for '{new_name}'", severity="warning")
        return {
            "success": True,
            "message": f"Windows Administrator confirmation prompt (UAC) launched for renaming host to '{new_name}'. Check your taskbar or screen for the prompt."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to launch elevation dialog: {str(e)}")

# ----------------- User Management APIs -----------------
@app.get("/api/users")
def get_users(
    query: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    db = load_db()
    users = db.get("users", [])
    
    filtered = []
    q = query.lower().strip() if query else None

    for u in users:
        if q and not (q in u.get("username", "").lower() or q in u.get("full_name", "").lower() or q in u.get("email", "").lower()):
            continue
        if role and role != "All" and u.get("role") != role:
            continue
        if status and status != "All" and u.get("status") != status:
            continue
        filtered.append(u)
        
    return {"users": filtered, "total": len(filtered)}

@app.post("/api/users")
def create_user(req: CreateUserRequest):
    db = load_db()
    users = db.setdefault("users", [])

    # Check unique username and email
    if any(u.get("username", "").lower() == req.username.lower() for u in users):
        raise HTTPException(status_code=400, detail=f"Username '{req.username}' is already taken.")
    if any(u.get("email", "").lower() == req.email.lower() for u in users):
        raise HTTPException(status_code=400, detail=f"Email '{req.email}' is already registered.")

    new_id = f"usr-{len(users) + 1:03d}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    colors = ["#6366f1", "#06b6d4", "#10b981", "#ec4899", "#f59e0b", "#8b5cf6"]
    avatar_color = colors[len(users) % len(colors)]

    new_user = {
        "id": new_id,
        "username": req.username.strip(),
        "full_name": req.full_name.strip(),
        "email": req.email.strip(),
        "role": req.role,
        "department": req.department or "General",
        "status": req.status or "Active",
        "two_factor": bool(req.two_factor),
        "created_at": now_str,
        "last_login": "Never",
        "avatar_color": avatar_color
    }

    users.append(new_user)
    save_db(db)
    log_activity("Create User", f"Created account @{req.username} ({req.role})", severity="info")
    return {"success": True, "user": new_user, "message": f"User @{req.username} created successfully."}

@app.put("/api/users/{user_id}")
def update_user(user_id: str, req: UpdateUserRequest):
    db = load_db()
    users = db.setdefault("users", [])
    
    target_idx = None
    for idx, u in enumerate(users):
        if u.get("id") == user_id:
            target_idx = idx
            break
            
    if target_idx is None:
        raise HTTPException(status_code=404, detail="User not found.")

    u = users[target_idx]
    if req.full_name is not None:
        u["full_name"] = req.full_name
    if req.email is not None:
        u["email"] = req.email
    if req.role is not None:
        u["role"] = req.role
    if req.department is not None:
        u["department"] = req.department
    if req.status is not None:
        u["status"] = req.status
    if req.two_factor is not None:
        u["two_factor"] = req.two_factor

    save_db(db)
    log_activity("Update User", f"Modified user {u.get('username')}", severity="info")
    return {"success": True, "user": u, "message": "User updated successfully."}

@app.delete("/api/users/{user_id}")
def delete_user(user_id: str):
    db = load_db()
    users = db.get("users", [])
    
    target = next((u for u in users if u.get("id") == user_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
        
    db["users"] = [u for u in users if u.get("id") != user_id]
    save_db(db)
    log_activity("Delete User", f"Removed user @{target.get('username')}", severity="warning")
    return {"success": True, "message": f"User @{target.get('username')} deleted."}

@app.post("/api/users/{user_id}/toggle-status")
def toggle_user_status(user_id: str):
    db = load_db()
    users = db.get("users", [])
    target = next((u for u in users if u.get("id") == user_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
        
    curr = target.get("status", "Active")
    new_status = "Suspended" if curr == "Active" else "Active"
    target["status"] = new_status
    save_db(db)
    log_activity("Toggle User Status", f"Set @{target.get('username')} to {new_status}", severity="info")
    return {"success": True, "status": new_status, "user": target}

# ----------------- Roles, Logs & Tokens -----------------
@app.get("/api/roles")
def get_roles():
    db = load_db()
    return {"roles": db.get("roles", [])}

@app.get("/api/activity")
def get_activity():
    db = load_db()
    return {"logs": db.get("activity_logs", [])}

@app.get("/api/tokens")
def get_tokens():
    db = load_db()
    return {"tokens": db.get("tokens", [])}

@app.post("/api/tokens")
def create_token(req: CreateTokenRequest):
    db = load_db()
    tokens = db.setdefault("tokens", [])
    new_id = f"tok-{len(tokens) + 1:03d}"
    import uuid
    rand_prefix = f"agt_{uuid.uuid4().hex[:6]}..."
    entry = {
        "id": new_id,
        "name": req.name,
        "prefix": rand_prefix,
        "role": req.role,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d"),
        "last_used": "Never",
        "status": "Active"
    }
    tokens.append(entry)
    save_db(db)
    log_activity("Create API Token", f"Generated token '{req.name}' ({req.role})", severity="info")
    return {"success": True, "token": entry}

@app.delete("/api/tokens/{token_id}")
def delete_token(token_id: str):
    db = load_db()
    tokens = db.get("tokens", [])
    target = next((t for t in tokens if t.get("id") == token_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Token not found.")
    db["tokens"] = [t for t in tokens if t.get("id") != token_id]
    save_db(db)
    log_activity("Revoke API Token", f"Revoked token '{target.get('name')}'", severity="warning")
    return {"success": True, "message": "Token revoked."}

# Mount static folder
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"message": "User Access Dashboard API is running."})

if __name__ == "__main__":
    import uvicorn
    port = 8080
    host_ip = "0.0.0.0"
    print(f"\n==================================================================")
    print(f"  USER ACCESS & HOST MANAGEMENT DASHBOARD")
    print(f"  Current Host Name : {socket.gethostname()}")
    print(f"  Local Dashboard   : http://localhost:{port}")
    print(f"  Network Access    : http://{socket.gethostname()}:{port}")
    print(f"==================================================================\n")
    uvicorn.run("user_access_server:app", host=host_ip, port=port, reload=False)
