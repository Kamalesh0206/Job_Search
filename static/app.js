let allJobs = [];

// ---------------- Init ----------------
document.addEventListener("DOMContentLoaded", () => {
  fetchStats();
  fetchJobs();
  fetchProfile();
  setInterval(pollTasks, 3000);
});

// ---------------- Tabs ----------------
function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

  event.currentTarget.classList.add("active");
  const target = document.getElementById(`tab-${tabId}`);
  if (target) target.classList.add("active");
}

// ---------------- Stats ----------------
async function fetchStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();
    document.getElementById("stat-total").textContent = data.total || 0;
    
    const byStatus = data.by_status || {};
    const reviewCount = (byStatus["New"] || 0) + (byStatus["Review"] || 0);
    const appliedCount = byStatus["Applied"] || 0;
    const interviewCount = (byStatus["Interview"] || 0) + (byStatus["Offer"] || 0);

    document.getElementById("stat-review").textContent = reviewCount;
    document.getElementById("stat-applied").textContent = appliedCount;
    document.getElementById("stat-interviews").textContent = interviewCount;

    // Update agent terminal status if running
    if (data.search_task?.status === "running") {
      updateTerminalStatus("🔍 Crawling job portals in background...", true);
    } else if (data.apply_task?.status === "running") {
      updateTerminalStatus("⚡ Apply agent running form automation...", true);
    } else {
      updateTerminalStatus("Agent Idle", false);
    }
  } catch (err) {
    console.error("Failed to load stats", err);
  }
}

// ---------------- Jobs ----------------
async function fetchJobs() {
  try {
    const res = await fetch("/api/jobs");
    const data = await res.json();
    allJobs = data.jobs || [];
    renderJobs(allJobs);
  } catch (err) {
    console.error("Failed to fetch jobs", err);
  }
}

function renderJobs(jobs) {
  const tbody = document.getElementById("jobs-table-body");
  if (!jobs || jobs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-faint); padding: 30px;">No jobs found matching criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = jobs.map(j => {
    const statusClass = `badge-${(j.status || "new").toLowerCase()}`;
    return `
      <tr>
        <td style="font-weight: 700; color: var(--text-faint);">${j.id}</td>
        <td>
          <span style="font-size: 11px; padding: 2px 7px; border-radius: 6px; background: rgba(255,255,255,0.06); color: #38bdf8;">
            ${escapeHtml(j.role_category)}
          </span>
        </td>
        <td class="job-title-cell">
          <a href="${escapeHtml(j.url)}" target="_blank" rel="noopener" style="color: var(--text-main); text-decoration: none;" title="Open Job Link">
            ${escapeHtml(j.title)} 🔗
          </a>
        </td>
        <td class="job-company-cell">${escapeHtml(j.company)}</td>
        <td class="job-location-cell">${escapeHtml(j.location || "Remote")}</td>
        <td>
          <select class="filter-select" style="padding: 4px 8px; font-size: 11px;" onchange="updateJobStatus('${j.id}', this.value)">
            <option value="New" ${j.status === "New" ? "selected" : ""}>New</option>
            <option value="Review" ${j.status === "Review" ? "selected" : ""}>Review</option>
            <option value="Applied" ${j.status === "Applied" ? "selected" : ""}>Applied</option>
            <option value="Interview" ${j.status === "Interview" ? "selected" : ""}>Interview</option>
            <option value="Skip" ${j.status === "Skip" ? "selected" : ""}>Skip</option>
          </select>
        </td>
        <td>
          <div class="row-actions">
            <button class="btn btn-sm btn-primary" title="Launch Auto-Apply for this job" onclick="applyJobFromRow('${j.id}', '${escapeAttr(j.url)}', '${escapeAttr(j.title)}', '${escapeAttr(j.company)}')">
              ⚡ Apply
            </button>
            <button class="btn btn-sm" title="Preview tailored cover letter" onclick="previewCoverLetter('${escapeAttr(j.title)}', '${escapeAttr(j.company)}')">
              ✉️ Letter
            </button>
            <button class="btn btn-sm" title="Recruiter Outreach" onclick="previewOutreach('${escapeAttr(j.company)}', '${escapeAttr(j.title)}')">
              💬 Outreach
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

function handleSearchFilter() {
  const query = document.getElementById("job-search-input").value.toLowerCase().trim();
  const role = document.getElementById("role-filter").value;
  const status = document.getElementById("status-filter").value;

  const filtered = allJobs.filter(j => {
    const matchText = !query || 
      j.title.toLowerCase().includes(query) || 
      j.company.toLowerCase().includes(query) || 
      (j.location && j.location.toLowerCase().includes(query));

    const matchRole = role === "All" || j.role_category === role;
    const matchStatus = status === "All" || (j.status || "").toLowerCase() === status.toLowerCase();

    return matchText && matchRole && matchStatus;
  });

  renderJobs(filtered);
}

// ---------------- Update Status ----------------
async function updateJobStatus(jobId, newStatus) {
  try {
    const res = await fetch(`/api/jobs/${jobId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    if (res.ok) {
      showToast(`Job #${jobId} status updated to ${newStatus}`);
      fetchStats();
    }
  } catch (err) {
    console.error(err);
    showToast("Failed to update status");
  }
}

// ---------------- Apply Actions ----------------
async function applyJobFromRow(id, url, title, company) {
  logTerminal(`[APPLY REQUEST] Launching apply agent for Job #${id} (${title} @ ${company})`);
  showToast(`Starting apply automation for ${company}...`);

  try {
    const res = await fetch("/api/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_url: url,
        job_title: title,
        company_name: company,
        headless: false, // visible headed for interactive review
        dry_run: true,
        auto_submit: false,
        job_id: id
      })
    });
    const data = await res.json();
    logTerminal(`[AGENT DISPATCH] ${data.message}`);
  } catch (err) {
    logTerminal(`[ERROR] Failed to launch apply agent: ${err}`);
  }
}

async function launchDirectApply() {
  const url = document.getElementById("apply-url").value.trim();
  if (!url) {
    alert("Please enter a valid job URL");
    return;
  }
  const title = document.getElementById("apply-title").value.trim() || "AI Engineer";
  const company = document.getElementById("apply-company").value.trim() || "Target Company";
  const headless = document.getElementById("apply-headless").checked;
  const dryRun = document.getElementById("apply-dryrun").checked;
  const autoSubmit = document.getElementById("apply-autosubmit").checked;

  const btn = document.getElementById("btn-launch-apply");
  const spinner = document.getElementById("apply-spinner");
  btn.disabled = true;
  spinner.style.display = "inline-block";

  logTerminal(`[DIRECT APPLY] Target: ${title} @ ${company} (${url})`);
  logTerminal(`[DIRECT APPLY] Options: Headless=${headless}, DryRun=${dryRun}, AutoSubmit=${autoSubmit}`);

  try {
    const res = await fetch("/api/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_url: url,
        job_title: title,
        company_name: company,
        headless: headless,
        dry_run: dryRun,
        auto_submit: autoSubmit
      })
    });
    const data = await res.json();
    showToast(data.message);
    logTerminal(`[AGENT] ${data.message}`);
  } catch (err) {
    logTerminal(`[ERROR] Direct apply failed: ${err}`);
  } finally {
    btn.disabled = false;
    spinner.style.display = "none";
  }
}

// ---------------- Search Trigger ----------------
async function triggerSearch() {
  const btn = document.getElementById("btn-run-search");
  const spinner = document.getElementById("search-spinner");
  btn.disabled = true;
  spinner.style.display = "inline-block";

  logTerminal(`[SEARCH] Triggering crawler for LinkedIn and EU Remote Jobs...`);
  showToast("Crawling job boards for new AI listings...");

  try {
    const res = await fetch("/api/search", { method: "POST" });
    const data = await res.json();
    logTerminal(`[SEARCH] ${data.message}`);
  } catch (err) {
    logTerminal(`[SEARCH ERROR] ${err}`);
  } finally {
    setTimeout(() => {
      btn.disabled = false;
      spinner.style.display = "none";
      fetchJobs();
      fetchStats();
    }, 4000);
  }
}

// ---------------- Cover Letter ----------------
async function previewCoverLetter(title, company) {
  try {
    const res = await fetch("/api/cover-letter", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_title: title, company_name: company })
    });
    const data = await res.json();
    document.getElementById("modal-cl-title").textContent = `Cover Letter: ${title} @ ${company}`;
    document.getElementById("modal-cl-text").textContent = data.cover_letter;
    openModal("modal-cover-letter");
  } catch (err) {
    console.error(err);
  }
}

function previewDirectCoverLetter() {
  const title = document.getElementById("apply-title").value.trim() || "AI Engineer";
  const company = document.getElementById("apply-company").value.trim() || "Target Company";
  previewCoverLetter(title, company);
}

// ---------------- Outreach ----------------
async function previewOutreach(company, role) {
  try {
    const res = await fetch("/api/outreach", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recruiter_name: "Hiring Manager", company_name: company, role_title: role })
    });
    const data = await res.json();
    document.getElementById("modal-outreach-title").textContent = `Outreach: ${role} @ ${company}`;
    document.getElementById("modal-outreach-note").textContent = data.linkedin_note;
    document.getElementById("modal-outreach-inmail").textContent = data.linkedin_inmail;
    openModal("modal-outreach");
  } catch (err) {
    console.error(err);
  }
}

async function generateOutreachStudio() {
  const name = document.getElementById("outreach-name").value.trim() || "Hiring Manager";
  const company = document.getElementById("outreach-company").value.trim() || "Target Company";
  const role = document.getElementById("outreach-role").value.trim() || "AI Engineer";

  try {
    const res = await fetch("/api/outreach", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recruiter_name: name, company_name: company, role_title: role })
    });
    const data = await res.json();

    document.getElementById("outreach-note-box").textContent = data.linkedin_note;
    document.getElementById("outreach-inmail-box").textContent = data.linkedin_inmail;
    document.getElementById("outreach-email-subject").textContent = `Subject: ${data.cold_email_subject}`;
    document.getElementById("outreach-email-body").textContent = data.cold_email_body;

    document.getElementById("outreach-results").style.display = "block";
    showToast("Outreach messages generated!");
  } catch (err) {
    console.error(err);
  }
}

// ---------------- Profile ----------------
async function fetchProfile() {
  try {
    const res = await fetch("/api/profile");
    const data = await res.json();

    const p = data.personal || {};
    document.getElementById("prof-name").value = `${p.first_name || ""} ${p.last_name || ""}`.trim();
    document.getElementById("prof-email").value = p.email || "";
    document.getElementById("prof-phone").value = p.phone || "";
    document.getElementById("prof-location").value = `${p.city || ""}, ${p.state || ""}, ${p.country || ""}`;

    const l = data.links || {};
    document.getElementById("prof-linkedin").value = l.linkedin || "";
    document.getElementById("prof-github").value = l.github || "";

    const w = data.work_authorization || {};
    document.getElementById("prof-auth").value = `${w.visa_status || ""} | Open to Relocation: ${w.open_to_relocation || "Yes"}`;

    const d = data.documents || {};
    document.getElementById("prof-coverletter").value = d.default_cover_letter || "";
  } catch (err) {
    console.error(err);
  }
}

async function regenerateResumePdf() {
  const spinner = document.getElementById("regen-spinner");
  spinner.style.display = "inline-block";
  showToast("Recompiling resume PDF with Playwright...");
  try {
    const res = await fetch("/api/resume/regenerate", { method: "POST" });
    const data = await res.json();
    showToast(data.message);
    logTerminal(`[RESUME] ${data.message}`);
    // Reload iframe
    const iframe = document.querySelector("#tab-profile iframe");
    if (iframe) iframe.src = "/api/resume?" + new Date().getTime();
  } catch (err) {
    logTerminal(`[ERROR] Resume regeneration failed: ${err}`);
  } finally {
    spinner.style.display = "none";
  }
}

// ---------------- Polling ----------------
async function pollTasks() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();

    if (data.search_task?.status === "completed" && data.search_task?.last_run !== "logged") {
      logTerminal(`[SEARCH FINISHED] ${data.search_task.message}`);
      data.search_task.last_run = "logged";
      fetchJobs();
    }
    if (data.apply_task?.status === "completed" && data.apply_task?.last_run !== "logged") {
      logTerminal(`[APPLY FINISHED] ${data.apply_task.message}`);
      data.apply_task.last_run = "logged";
      fetchJobs();
      fetchStats();
    }

    // Read recent logs
    const lRes = await fetch("/api/logs");
    const lData = await lRes.json();
    if (lData.apply && lData.apply.length > 0) {
      const lastLine = lData.apply[lData.apply.length - 1];
      if (!window.lastLoggedLine || window.lastLoggedLine !== lastLine) {
        window.lastLoggedLine = lastLine;
        logTerminal(`[AGENT LOG] ${lastLine.trim()}`);
      }
    }
  } catch (e) {}
}

// ---------------- Helpers ----------------
function logTerminal(msg) {
  const body = document.getElementById("terminal-body");
  const time = new Date().toLocaleTimeString();
  body.textContent += `\n[${time}] ${msg}`;
  body.scrollTop = body.scrollHeight;
}

function updateTerminalStatus(text, isBusy) {
  const el = document.getElementById("terminal-status");
  el.textContent = text;
  el.style.color = isBusy ? "#38bdf8" : "var(--text-faint)";
}

function openModal(id) {
  document.getElementById(id).classList.add("open");
}
function closeModal(id) {
  document.getElementById(id).classList.remove("open");
}

function showToast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2800);
}

function copyFromElement(id) {
  const text = document.getElementById(id).textContent;
  navigator.clipboard.writeText(text);
  showToast("Copied to clipboard!");
}

function copyColdEmail() {
  const subj = document.getElementById("outreach-email-subject").textContent;
  const body = document.getElementById("outreach-email-body").textContent;
  navigator.clipboard.writeText(`${subj}\n\n${body}`);
  showToast("Subject & Email copied!");
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
function escapeAttr(str) {
  if (!str) return "";
  return String(str).replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
