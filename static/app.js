// ==========================================================================
// Dual-Role Job Search & Application Automation Agent - Client Application
// ==========================================================================

const state = {
  activeProfile: 'ALL',
  currentTab: 'jobs',
  jobs: [],
  selectedJob: null,
  stats: null,
  filters: {
    status: 'All',
    country: 'All',
    workArrangement: 'All',
    sponsorship: 'All',
    minScore: 0,
    search: ''
  },
  searchPollingInterval: null
};

document.addEventListener('DOMContentLoaded', () => {
  initProfileSelector();
  fetchStats();
  fetchJobs();
  pollSearchStatus();
});

// Profile Mode Switcher (Section 2)
function selectProfile(profileId) {
  state.activeProfile = profileId;

  document.querySelectorAll('.profile-pill-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-profile') === profileId);
  });

  const filterProfileSelect = document.getElementById('filterProfile');
  if (filterProfileSelect) {
    filterProfileSelect.value = profileId;
  }

  fetchStats();
  fetchJobs();
}

function initProfileSelector() {
  const filterProfile = document.getElementById('filterProfile');
  if (filterProfile) {
    filterProfile.addEventListener('change', (e) => {
      selectProfile(e.target.value);
    });
  }
}

// Tab Switching
function switchTab(tabId) {
  state.currentTab = tabId;

  document.querySelectorAll('.nav-tabs .tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });

  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.remove('active');
  });

  const targetPane = document.getElementById(`tab-${tabId}`);
  if (targetPane) {
    targetPane.classList.add('active');
  }

  // Highlight active tab button
  const buttons = document.querySelectorAll('.nav-tabs .tab-btn');
  buttons.forEach(b => {
    if (b.getAttribute('onclick') && b.getAttribute('onclick').includes(tabId)) {
      b.classList.add('active');
    }
  });
}

// Fetch Real Stored Records Stats (Section 10)
async function fetchStats() {
  try {
    const res = await fetch(`/api/stats?profile=${state.activeProfile}`);
    if (!res.ok) throw new Error('Failed to fetch stats');
    const data = await res.json();
    state.stats = data;
    renderStats(data.stats);

    // Populate country dropdown if not already populated
    if (data.available_countries && data.available_countries.length > 0) {
      populateCountryFilter(data.available_countries);
    }
  } catch (err) {
    console.error('Error loading statistics:', err);
  }
}

function renderStats(s) {
  if (!s) return;
  document.getElementById('stat-total').textContent = s.total_jobs ?? 0;
  document.getElementById('stat-relevant').textContent = s.relevant_jobs ?? 0;
  document.getElementById('stat-sponsorship').textContent = s.confirmed_sponsorship ?? 0;
  document.getElementById('stat-remote').textContent = s.remote_jobs ?? 0;
  document.getElementById('stat-applied').textContent = s.applications_submitted ?? 0;
  document.getElementById('stat-interviews').textContent = s.interviews ?? 0;
  document.getElementById('stat-rejections').textContent = s.rejections ?? 0;

  const profName = state.activeProfile === 'ALL' ? 'All Roles' : (state.activeProfile === 'AI_ENGINEER' ? 'AI Engineer' : 'Test Engineer');
  const sub = document.getElementById('stat-total-sub');
  if (sub) sub.textContent = profName;
}

function populateCountryFilter(countries) {
  const sel = document.getElementById('filterCountry');
  if (!sel || sel.children.length > 1) return;

  countries.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c;
    opt.textContent = c;
    sel.appendChild(opt);
  });
}

// Fetch Filtered Jobs
async function fetchJobs() {
  const params = new URLSearchParams();
  if (state.activeProfile) params.append('profile', state.activeProfile);
  if (state.filters.status && state.filters.status !== 'All') params.append('status', state.filters.status);
  if (state.filters.country && state.filters.country !== 'All') params.append('country', state.filters.country);
  if (state.filters.workArrangement && state.filters.workArrangement !== 'All') params.append('work_arrangement', state.filters.workArrangement);
  if (state.filters.sponsorship && state.filters.sponsorship !== 'All') params.append('sponsorship', state.filters.sponsorship);
  if (state.filters.minScore > 0) params.append('min_score', state.filters.minScore);
  if (state.filters.search) params.append('search', state.filters.search);

  try {
    const res = await fetch(`/api/jobs?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch jobs');
    const data = await res.json();
    state.jobs = data.jobs || [];

    const tabCount = document.getElementById('tabCountJobs');
    if (tabCount) tabCount.textContent = data.count;

    renderJobsTable(state.jobs);
  } catch (err) {
    console.error('Error fetching jobs:', err);
  }
}

// Render Jobs Table
function renderJobsTable(jobs) {
  const tbody = document.getElementById('jobsTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';

  if (!jobs || jobs.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" style="text-align: center; padding: 48px; color: var(--text-dim);">
          No job listings found matching your current filters.
        </td>
      </tr>
    `;
    return;
  }

  jobs.forEach(job => {
    const tr = document.createElement('tr');

    const score = parseInt(job.relevance_score || 0);
    let scoreClass = 'score-low';
    if (score >= 75) scoreClass = 'score-high';
    else if (score >= 60) scoreClass = 'score-med';

    const pid = (job.role_category || job.profile_id || 'AI_ENGINEER').toUpperCase();
    let roleClass = 'badge-ai';
    if (pid.includes('TEST')) roleClass = 'badge-test';
    else if (pid.includes('BOTH')) roleClass = 'badge-both';

    const statusNorm = (job.status || 'DISCOVERED').toUpperCase();
    const statusClass = `status-${statusNorm.toLowerCase()}`;

    const visaStatus = (job.visa_sponsorship_status || 'UNKNOWN').toUpperCase();
    let visaBadge = `<span style="color: var(--text-dim); font-size: 0.76rem;">Unknown</span>`;
    if (visaStatus === 'CONFIRMED') {
      visaBadge = `<span style="color: var(--accent-emerald); font-weight: 700; font-size: 0.78rem;">✓ Confirmed</span>`;
    } else if (visaStatus === 'NOT_OFFERED') {
      visaBadge = `<span style="color: var(--accent-rose); font-size: 0.76rem;">No Sponsor</span>`;
    }

    const matchedSnippet = job.matched_skills ? job.matched_skills.split(',').slice(0, 3).map(s => `<span class="skill-chip">${escapeHtml(s.trim())}</span>`).join('') : '<span style="color: var(--text-dim); font-size: 0.75rem;">—</span>';

    tr.innerHTML = `
      <td><span class="score-pill ${scoreClass}">${score}</span></td>
      <td><span class="badge-role ${roleClass}">${escapeHtml(pid)}</span></td>
      <td>
        <div style="font-weight: 700; color: #fff;">${escapeHtml(job.title)}</div>
        <div style="font-size: 0.78rem; color: var(--accent-cyan);">${escapeHtml(job.company)} • <span style="color: var(--text-muted);">${escapeHtml(job.source)}</span></div>
      </td>
      <td>
        <div style="font-size: 0.82rem;">${escapeHtml(job.country || job.city || 'Remote')}</div>
        <div style="font-size: 0.74rem; color: var(--text-dim);">${escapeHtml(job.work_arrangement || 'Remote')}</div>
      </td>
      <td>${visaBadge}</td>
      <td><div class="skills-tag-wrap">${matchedSnippet}</div></td>
      <td><span class="status-badge ${statusClass}">${escapeHtml(job.status || 'DISCOVERED')}</span></td>
      <td style="text-align: right;">
        <button class="btn btn-secondary btn-xs" onclick="openJobDrawer(${job.id})">
          🔍 Inspect
        </button>
        ${statusNorm !== 'APPROVED' && statusNorm !== 'APPLIED' ? `
          <button class="btn btn-emerald btn-xs" onclick="quickApprove(${job.id}, event)" title="Approve for submission">
            ✓
          </button>
        ` : ''}
        ${statusNorm !== 'REJECTED' ? `
          <button class="btn btn-rose btn-xs" onclick="quickReject(${job.id}, event)" title="Reject">
            ✕
          </button>
        ` : ''}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Filter Handling
let debounceTimer;
function debounceFilter() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    applyFilters();
  }, 250);
}

function applyFilters() {
  state.filters.status = document.getElementById('filterStatus').value;
  state.filters.country = document.getElementById('filterCountry').value;
  state.filters.workArrangement = document.getElementById('filterWorkArrangement').value;
  state.filters.sponsorship = document.getElementById('filterSponsorship').value;
  state.filters.minScore = parseInt(document.getElementById('filterMinScore').value || '0');
  state.filters.search = document.getElementById('searchInput').value.trim();

  fetchJobs();
}

// Quick Status Actions
async function quickApprove(jobId, e) {
  if (e) e.stopPropagation();
  try {
    const res = await fetch(`/api/jobs/${jobId}/approve`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to approve');
    showToast('Job approved for submission package', 'success');
    fetchJobs();
    fetchStats();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function quickReject(jobId, e) {
  if (e) e.stopPropagation();
  try {
    const res = await fetch(`/api/jobs/${jobId}/reject`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to reject');
    showToast('Job marked as rejected', 'info');
    fetchJobs();
    fetchStats();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Job Inspection Drawer & Human-in-the-Loop Review (Section 9)
async function openJobDrawer(jobId) {
  const job = state.jobs.find(j => String(j.id) === String(jobId));
  if (!job) return;
  state.selectedJob = job;

  document.getElementById('drawerTitle').textContent = job.title;
  document.getElementById('drawerCompanyLoc').textContent = `${job.company} • ${job.country || 'Remote'} • ${job.work_arrangement} (${job.source})`;
  document.getElementById('drawerScore').textContent = job.relevance_score || 0;
  document.getElementById('drawerExplanation').textContent = job.notes || 'Relevance calculated based on domain match and required qualifications.';

  const roleBadge = document.getElementById('drawerRoleBadge');
  const pid = (job.role_category || job.profile_id || 'AI_ENGINEER').toUpperCase();
  roleBadge.textContent = pid;
  roleBadge.className = `badge-role ${pid.includes('TEST') ? 'badge-test' : (pid.includes('BOTH') ? 'badge-both' : 'badge-ai')}`;

  // Matched Skills
  const matchedWrap = document.getElementById('drawerMatchedSkills');
  matchedWrap.innerHTML = '';
  if (job.matched_skills) {
    job.matched_skills.split(',').forEach(s => {
      if (s.trim()) {
        const chip = document.createElement('span');
        chip.className = 'skill-chip';
        chip.textContent = `✓ ${s.trim()}`;
        matchedWrap.appendChild(chip);
      }
    });
  }

  // Missing Skills
  const missingWrap = document.getElementById('drawerMissingSkills');
  missingWrap.innerHTML = '';
  if (job.missing_skills) {
    job.missing_skills.split(',').slice(0, 5).forEach(s => {
      if (s.trim()) {
        const chip = document.createElement('span');
        chip.className = 'missing-chip';
        chip.textContent = `Missing: ${s.trim()}`;
        missingWrap.appendChild(chip);
      }
    });
  }

  // Resume Download link
  const resumeDownload = document.getElementById('drawerResumeDownload');
  const targetPid = pid.includes('TEST') ? 'TEST_ENGINEER' : 'AI_ENGINEER';
  resumeDownload.href = `/api/resume/${targetPid}`;
  document.getElementById('drawerResumeName').textContent = targetPid === 'TEST_ENGINEER' ? 'Kamalesan_C_Test_Engineer_Resume.pdf' : 'Kamalesan_C_AI_Engineer_Resume.pdf';

  // Description
  document.getElementById('drawerDescription').textContent = job.description || 'No extended description available.';

  // External link
  const extLink = document.getElementById('drawerExternalLink');
  extLink.href = job.url || '#';

  // Load Tailored Cover Letter
  loadDrawerCoverLetter(job.id);

  // Show Drawer
  document.getElementById('jobDrawerOverlay').style.display = 'flex';
}

function closeJobDrawer(e) {
  if (e && e.target !== e.currentTarget && e.target.id !== 'jobDrawerOverlay') return;
  document.getElementById('jobDrawerOverlay').style.display = 'none';
  state.selectedJob = null;
}

async function loadDrawerCoverLetter(jobId) {
  const box = document.getElementById('drawerCoverLetterText');
  box.value = 'Loading tailored cover letter...';

  try {
    const res = await fetch(`/api/jobs/${jobId}/cover-letter`);
    if (!res.ok) throw new Error('Could not load cover letter');
    const data = await res.json();
    box.value = data.cover_letter || '';
  } catch (err) {
    box.value = 'Failed to load cover letter: ' + err.message;
  }
}

async function regenerateDrawerDocs() {
  if (!state.selectedJob) return;
  showToast('Regenerating tailored documents...', 'info');
  try {
    const res = await fetch(`/api/jobs/${state.selectedJob.id}/generate-documents`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed');
    document.getElementById('drawerCoverLetterText').value = data.cover_letter || '';
    showToast('Cover letter and ATS resume package updated!', 'success');
    fetchJobs();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function approveCurrentJob() {
  if (!state.selectedJob) return;
  await quickApprove(state.selectedJob.id);
  closeJobDrawer();
}

async function rejectCurrentJob() {
  if (!state.selectedJob) return;
  await quickReject(state.selectedJob.id);
  closeJobDrawer();
}

async function launchPlaywrightApply() {
  if (!state.selectedJob) return;
  const job = state.selectedJob;

  if (!confirm(`Launch Playwright browser assistant for ${job.title} at ${job.company}?\n\nExplicit approval will be recorded.`)) {
    return;
  }

  try {
    const payload = {
      job_id: job.id,
      job_url: job.url,
      job_title: job.title,
      company_name: job.company,
      job_description: job.description,
      profile_id: job.profile_id,
      headless: false,
      dry_run: true,
      auto_submit: false,
      explicit_approval: true
    };

    const res = await fetch('/api/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to trigger apply');

    showToast(data.message, 'success');
    closeJobDrawer();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Background Search Polling
async function triggerSearch() {
  const btn = document.getElementById('btn-run-search');
  const spinner = document.getElementById('search-spinner');
  btn.disabled = true;
  if (spinner) spinner.style.display = 'inline-block';

  try {
    const res = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile: state.activeProfile })
    });
    const data = await res.json();
    showToast(data.message, 'info');
    pollSearchStatus();
  } catch (err) {
    showToast(err.message, 'error');
    btn.disabled = false;
    if (spinner) spinner.style.display = 'none';
  }
}

function pollSearchStatus() {
  const banner = document.getElementById('search-task-banner');
  const bannerText = document.getElementById('search-task-text');
  const btn = document.getElementById('btn-run-search');
  const spinner = document.getElementById('search-spinner');

  if (state.searchPollingInterval) clearInterval(state.searchPollingInterval);

  state.searchPollingInterval = setInterval(async () => {
    try {
      const res = await fetch('/api/stats');
      const data = await res.json();
      const task = data.search_task;

      if (task && task.status === 'running') {
        if (banner) banner.style.display = 'flex';
        if (bannerText) bannerText.textContent = task.message || 'Job search running...';
        if (btn) btn.disabled = true;
        if (spinner) spinner.style.display = 'inline-block';
      } else {
        if (banner) banner.style.display = 'none';
        if (btn) btn.disabled = false;
        if (spinner) spinner.style.display = 'none';
        clearInterval(state.searchPollingInterval);

        if (task && task.status === 'completed') {
          showToast(task.message, 'success');
          fetchStats();
          fetchJobs();
        }
      }
    } catch (e) {
      clearInterval(state.searchPollingInterval);
    }
  }, 3000);
}

// Cover Letter Studio Tab
async function generateStudioCoverLetter() {
  const profileId = document.getElementById('clProfileSelect').value;
  const company = document.getElementById('clCompanyInput').value.trim();
  const title = document.getElementById('clTitleInput').value.trim();
  const desc = document.getElementById('clDescInput').value.trim();

  if (!company || !title) {
    showToast('Please enter both company name and job title', 'warning');
    return;
  }

  showToast('Generating tailored cover letter...', 'info');
  try {
    const res = await fetch('/api/cover-letter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company_name: company,
        job_title: title,
        job_description: desc,
        profile_id: profileId
      })
    });
    const data = await res.json();
    document.getElementById('clOutputText').value = data.cover_letter || '';
    showToast(`Letter generated and saved into ${profileId} documents!`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function copyCoverLetterText() {
  const text = document.getElementById('clOutputText').value;
  if (!text) return;
  navigator.clipboard.writeText(text).then(() => {
    showToast('Cover letter copied to clipboard!', 'success');
  });
}

// Recruiter Outreach Tab
async function generateOutreachNotes() {
  const recruiter = document.getElementById('outreachRecruiterName').value.trim();
  const company = document.getElementById('outreachCompany').value.trim();
  const role = document.getElementById('outreachRole').value.trim();

  try {
    const res = await fetch('/api/outreach', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        recruiter_name: recruiter,
        company_name: company,
        role_title: role
      })
    });
    const data = await res.json();
    document.getElementById('outreachLinkedInNote').value = data.linkedin_note || '';
    document.getElementById('outreachInMail').value = data.linkedin_inmail || '';
    document.getElementById('outreachEmailSub').value = data.cold_email_subject || '';
    document.getElementById('outreachEmailBody').value = data.cold_email_body || '';
    showToast('Outreach communications generated!', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Schedule Settings Tab
async function saveScheduleSettings() {
  const mode = document.getElementById('schedModeSelect').value;
  const timeVal = document.getElementById('schedTimeInput').value;

  try {
    const res = await fetch('/api/config');
    const conf = await res.json();
    conf.schedule = {
      enabled: mode === 'daily',
      mode: mode,
      daily_time: timeVal
    };

    const putRes = await fetch('/api/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(conf)
    });
    if (!putRes.ok) throw new Error('Failed to update config');
    showToast('Schedule settings saved successfully!', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Toast Notifications
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  if (type === 'error') icon = '❌';
  if (type === 'warning') icon = '⚠️';

  toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
