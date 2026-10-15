// ==========================================================================
// Dual-Role Job Search & Application Automation Agent - Client Application
// Production Cloud & Local Compatible Architecture
// ==========================================================================

// Environment API Base Configuration:
// Uses explicitly provided window.API_BASE_URL if set; otherwise uses current origin.
const API_BASE = window.API_BASE_URL || window.location.origin;

function getAuthHeaders() {
  const token = sessionStorage.getItem('agent_auth_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function apiFetch(endpoint, options = {}) {
  const fullUrl = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  const headers = {
    ...getAuthHeaders(),
    ...(options.headers || {})
  };
  const response = await fetch(fullUrl, { ...options, headers });
  if (response.status === 401) {
    promptLogin();
    throw new Error('Authentication required: please log in.');
  }
  return response;
}

function promptLogin() {
  if (document.getElementById('auth-modal-overlay')) return;
  const overlay = document.createElement('div');
  overlay.id = 'auth-modal-overlay';
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(10,15,30,0.85);backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;z-index:99999;';
  overlay.innerHTML = `
    <div style="background:#131d33;border:1px solid #1e293b;border-radius:14px;padding:32px;width:90%;max-width:380px;box-shadow:0 20px 40px rgba(0,0,0,0.6);text-align:center;">
      <div style="font-size:2rem;margin-bottom:12px;">🔒</div>
      <h3 style="color:#f8fafc;margin-bottom:8px;font-size:1.25rem;">Remote Access Security</h3>
      <p style="color:#94a3b8;font-size:0.85rem;margin-bottom:20px;">Enter your dashboard credentials to access candidate profiles, resumes, and actions.</p>
      <input id="authUsernameInput" type="text" placeholder="Username (e.g. admin)" style="width:100%;padding:10px 14px;background:#0b1120;border:1px solid #334155;border-radius:8px;color:#fff;margin-bottom:12px;box-sizing:border-box;">
      <input id="authPasswordInput" type="password" placeholder="Password" style="width:100%;padding:10px 14px;background:#0b1120;border:1px solid #334155;border-radius:8px;color:#fff;margin-bottom:20px;box-sizing:border-box;">
      <button id="authSubmitBtn" style="width:100%;padding:11px;background:#0284c7;color:#fff;font-weight:700;border:none;border-radius:8px;cursor:pointer;">Unlock Dashboard</button>
      <div id="authErrorMsg" style="color:#f43f5e;font-size:0.8rem;margin-top:10px;display:none;"></div>
    </div>
  `;
  document.body.appendChild(overlay);

  document.getElementById('authSubmitBtn').onclick = async () => {
    const user = document.getElementById('authUsernameInput').value.trim();
    const pass = document.getElementById('authPasswordInput').value;
    const errDiv = document.getElementById('authErrorMsg');
    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: user, password: pass })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');
      sessionStorage.setItem('agent_auth_token', data.token);
      overlay.remove();
      showToast('Authenticated successfully!', 'success');
      fetchStats();
      fetchJobs();
    } catch (err) {
      errDiv.textContent = err.message;
      errDiv.style.display = 'block';
    }
  };
}

const state = {
  activeProfile: 'ALL',
  currentTab: 'jobs',
  jobs: [],
  selectedJob: null,
  stats: null,
  profiles: {},
  settingsProfile: 'AI_ENGINEER',
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
  fetchProfiles();
  fetchStats();
  fetchJobs();
  pollSearchStatus();
});

// Fetch Profile Configuration from Backend API (Section 1 & 2)
async function fetchProfiles() {
  try {
    const res = await apiFetch('/api/profiles');
    if (!res.ok) throw new Error('Failed to load profiles');
    state.profiles = await res.json();
    renderHeaderProfile();
    if (state.currentTab === 'skills-roles') {
      renderSettingsForm();
    }
  } catch (err) {
    console.error('Error fetching profile data:', err);
  }
}

// Dynamic Dashboard Header Rendering (Section 1 & 2)
function renderHeaderProfile() {
  const container = document.getElementById('headerProfileContainer');
  if (!container) return;

  const ai = state.profiles['AI_ENGINEER'] || {
    name: "Kamalesan C",
    display_title: "AI Engineer",
    experience_years: "7.4",
    location: "Coimbatore, India",
    phone: "+91 7305131264",
    email: "kamaleshcai686@gmail.com",
    linkedin: "https://www.linkedin.com/in/kamalesan-c-546646442",
    github: "https://github.com/Kamalesh0206"
  };

  const test = state.profiles['TEST_ENGINEER'] || {
    name: "Kamalesan C",
    display_title: "Test Engineer",
    experience_years: "7.4",
    location: "Coimbatore, Tamil Nadu, India",
    phone: "+91 98436 19970",
    email: "softkamalesh@gmail.com",
    linkedin: "https://www.linkedin.com/in/kamalesh-chinnathambi-62b952299",
    github: ""
  };

  if (state.activeProfile === 'AI_ENGINEER') {
    container.innerHTML = `
      <div class="candidate-profile-block">
        <div class="avatar-circle">KC</div>
        <div>
          <div class="candidate-name">
            ${escapeHtml(ai.name)}
            <span class="badge-tag">AI Engineer</span>
            <span class="badge-tag badge-purple">${escapeHtml(ai.experience_years || '7.4')} Years Experience</span>
          </div>
          <div class="candidate-meta">
            <span>📍 ${escapeHtml(ai.location)}</span>
            <span>📞 ${escapeHtml(ai.phone)}</span>
            <a href="mailto:${escapeHtml(ai.email)}">✉️ ${escapeHtml(ai.email)}</a>
            ${ai.linkedin ? `<a href="${escapeHtml(ai.linkedin)}" target="_blank" rel="noopener">🔗 LinkedIn Profile</a>` : ''}
            ${ai.github ? `<a href="${escapeHtml(ai.github)}" target="_blank" rel="noopener">💻 GitHub Portfolio</a>` : ''}
          </div>
        </div>
      </div>
    `;
  } else if (state.activeProfile === 'TEST_ENGINEER') {
    container.innerHTML = `
      <div class="candidate-profile-block">
        <div class="avatar-circle" style="background: linear-gradient(135deg, #10b981, #06b6d4);">KC</div>
        <div>
          <div class="candidate-name">
            ${escapeHtml(test.name)}
            <span class="badge-tag" style="background: hsla(158, 64%, 45%, 0.2); color: #34d399; border-color: hsla(158, 64%, 45%, 0.35);">Test Engineer</span>
            <span class="badge-tag badge-purple">${escapeHtml(test.experience_years || '7.4')} Years Experience</span>
          </div>
          <div class="candidate-meta">
            <span>📍 ${escapeHtml(test.location)}</span>
            <span>📞 ${escapeHtml(test.phone)}</span>
            <a href="mailto:${escapeHtml(test.email)}">✉️ ${escapeHtml(test.email)}</a>
            ${test.linkedin ? `<a href="${escapeHtml(test.linkedin)}" target="_blank" rel="noopener">🔗 LinkedIn Profile</a>` : ''}
            ${test.github ? `<a href="${escapeHtml(test.github)}" target="_blank" rel="noopener">💻 GitHub Portfolio</a>` : ''}
          </div>
        </div>
      </div>
    `;
  } else {
    // ALL PROFILES selected: render separate profile cards. Never combine contact details!
    container.innerHTML = `
      <div class="dual-profile-cards">
        <div class="profile-summary-card ai-card">
          <div class="card-top">
            <span class="card-name">${escapeHtml(ai.name)}</span>
            <span class="badge-tag">AI Engineer • ${escapeHtml(ai.experience_years || '7.4')}y Exp</span>
          </div>
          <div class="card-meta">
            <div>📍 ${escapeHtml(ai.location)} • 📞 ${escapeHtml(ai.phone)}</div>
            <div>
              <a href="mailto:${escapeHtml(ai.email)}">✉️ ${escapeHtml(ai.email)}</a> •
              ${ai.linkedin ? `<a href="${escapeHtml(ai.linkedin)}" target="_blank" rel="noopener">LinkedIn</a>` : ''}
              ${ai.github ? ` • <a href="${escapeHtml(ai.github)}" target="_blank" rel="noopener">GitHub</a>` : ''}
            </div>
          </div>
        </div>

        <div class="profile-summary-card test-card">
          <div class="card-top">
            <span class="card-name">${escapeHtml(test.name)}</span>
            <span class="badge-tag" style="background: hsla(158, 64%, 45%, 0.2); color: #34d399; border-color: hsla(158, 64%, 45%, 0.35);">Test Engineer • ${escapeHtml(test.experience_years || '7.4')}y Exp</span>
          </div>
          <div class="card-meta">
            <div>📍 ${escapeHtml(test.location)} • 📞 ${escapeHtml(test.phone)}</div>
            <div>
              <a href="mailto:${escapeHtml(test.email)}">✉️ ${escapeHtml(test.email)}</a> •
              ${test.linkedin ? `<a href="${escapeHtml(test.linkedin)}" target="_blank" rel="noopener">LinkedIn</a>` : ''}
              ${test.github ? ` • <a href="${escapeHtml(test.github)}" target="_blank" rel="noopener">GitHub</a>` : ''}
            </div>
          </div>
        </div>
      </div>
    `;
  }
}

// Profile Mode Switcher (Section 2)
function selectProfile(profileId) {
  state.activeProfile = profileId;

  document.querySelectorAll('#profileSelector .profile-pill-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-profile') === profileId);
  });

  const filterProfileSelect = document.getElementById('filterProfile');
  if (filterProfileSelect) {
    filterProfileSelect.value = profileId;
  }

  // Update header immediately
  renderHeaderProfile();
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

  if (tabId === 'skills-roles') {
    renderSettingsForm();
  }
}

// Fetch Real Stored Records Stats (Section 10)
async function fetchStats() {
  try {
    const res = await apiFetch(`/api/stats?profile=${state.activeProfile}`);
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
    const res = await apiFetch(`/api/jobs?${params.toString()}`);
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
        <td colspan="11" style="text-align: center; padding: 48px; color: var(--text-dim);">
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
    const missingSnippet = job.missing_skills ? job.missing_skills.split(',').slice(0, 2).map(s => `<span class="missing-chip">${escapeHtml(s.trim())}</span>`).join('') : '<span style="color: var(--text-dim); font-size: 0.75rem;">None</span>';

    const jobIdAttr = escapeHtml(String(job.id));
    const jobUrl = job.url || '#';
    const jobDate = job.application_date || job.posted_date || job.found_date || '—';

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
      <td>
        <a href="${escapeHtml(jobUrl)}" target="_blank" rel="noopener" style="color: var(--accent-cyan); text-decoration: none; font-size: 0.82rem; font-weight: 600;">
          🔗 Open
        </a>
      </td>
      <td><div class="skills-tag-wrap">${matchedSnippet}</div></td>
      <td><div class="skills-tag-wrap">${missingSnippet}</div></td>
      <td>${visaBadge}</td>
      <td><span class="status-badge ${statusClass}">${escapeHtml(job.status || 'DISCOVERED')}</span></td>
      <td style="font-size: 0.78rem; color: var(--text-muted);">${escapeHtml(jobDate)}</td>
      <td style="text-align: right;">
        <button class="btn btn-secondary btn-xs" onclick="openJobDrawer('${jobIdAttr}')">
          🔍 Inspect
        </button>
        ${statusNorm !== 'APPROVED' && statusNorm !== 'APPLIED' ? `
          <button class="btn btn-emerald btn-xs" onclick="quickApprove('${jobIdAttr}', event)" title="Approve for submission">
            ✓
          </button>
        ` : ''}
        ${statusNorm !== 'REJECTED' ? `
          <button class="btn btn-rose btn-xs" onclick="quickReject('${jobIdAttr}', event)" title="Reject">
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
    const res = await apiFetch(`/api/jobs/${jobId}/approve`, { method: 'POST' });
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
    const res = await apiFetch(`/api/jobs/${jobId}/reject`, { method: 'POST' });
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
  const resumeBtn = document.getElementById('drawerResumeDownloadBtn');
  if (resumeBtn) {
    resumeBtn.href = `${API_BASE}/api/resume/${pid.includes('TEST') ? 'TEST_ENGINEER' : 'AI_ENGINEER'}`;
  }

  // Job Listing External Link
  const linkBtn = document.getElementById('drawerJobUrlLink');
  if (linkBtn) {
    linkBtn.href = job.url;
  }

  // Description
  document.getElementById('drawerDescription').textContent = job.description || 'Full description recorded in persistent database.';

  // Load / Generate Tailored Cover Letter
  loadDrawerCoverLetter(job.id);

  // Status Badge in Drawer
  const statusEl = document.getElementById('drawerStatusBadge');
  statusEl.textContent = (job.status || 'DISCOVERED').toUpperCase();
  statusEl.className = `status-badge status-${(job.status || 'DISCOVERED').toLowerCase()}`;

  document.getElementById('jobDrawer').classList.add('open');
  document.getElementById('drawerBackdrop').classList.add('open');
}

function closeJobDrawer() {
  document.getElementById('jobDrawer').classList.remove('open');
  document.getElementById('drawerBackdrop').classList.remove('open');
  state.selectedJob = null;
}

async function loadDrawerCoverLetter(jobId) {
  const box = document.getElementById('drawerCoverLetterText');
  box.value = 'Loading tailored cover letter from storage...';
  try {
    const res = await apiFetch(`/api/jobs/${jobId}/cover-letter`);
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
    const res = await apiFetch(`/api/jobs/${state.selectedJob.id}/generate-documents`, { method: 'POST' });
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

  if (!confirm(`Launch application assistant for ${job.title} at ${job.company}?\n\nExplicit approval will be recorded.`)) {
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
      headless: true, // Default to headless for cloud stability
      dry_run: true,
      auto_submit: false,
      explicit_approval: true
    };

    const res = await apiFetch('/api/apply', {
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
    const res = await apiFetch('/api/search', {
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

  if (state.searchPollingInterval) {
    clearInterval(state.searchPollingInterval);
  }

  state.searchPollingInterval = setInterval(async () => {
    try {
      const res = await apiFetch('/api/stats');
      if (!res.ok) return;
      const data = await res.json();
      const task = data.search_task;

      if (task && task.status === 'running') {
        if (banner) banner.style.display = 'flex';
        if (bannerText) bannerText.textContent = task.message;
        if (btn) btn.disabled = true;
        if (spinner) spinner.style.display = 'inline-block';
      } else {
        if (banner) banner.style.display = 'none';
        if (btn) btn.disabled = false;
        if (spinner) spinner.style.display = 'none';

        if (task && task.status === 'completed') {
          fetchStats();
          fetchJobs();
          clearInterval(state.searchPollingInterval);
          state.searchPollingInterval = null;
        } else if (task && task.status === 'error') {
          showToast(task.message, 'error');
          clearInterval(state.searchPollingInterval);
          state.searchPollingInterval = null;
        }
      }
    } catch (e) {
      // Continue polling silently
    }
  }, 3000);
}

// Outreach Generator Tab
async function generateOutreach() {
  const recruiter = document.getElementById('outreachRecruiterName').value.trim() || 'Hiring Manager';
  const company = document.getElementById('outreachCompanyName').value.trim() || 'Target Company';
  const role = document.getElementById('outreachRoleTitle').value.trim() || 'AI Engineer';
  const profileId = document.getElementById('outreachProfileSelect').value || 'AI_ENGINEER';

  try {
    showToast('Generating personalized multi-channel outreach templates...', 'info');
    const res = await apiFetch('/api/outreach', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        recruiter_name: recruiter,
        company_name: company,
        role_title: role,
        profile_id: profileId
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed');

    document.getElementById('outreachLinkedinNote').value = data.linkedin_note;
    document.getElementById('outreachInMail').value = data.linkedin_inmail;
    document.getElementById('outreachEmailSubject').value = data.cold_email_subject;
    document.getElementById('outreachEmailBody').value = data.cold_email_body;
    document.getElementById('outreachFollowup').value = data.followup;

    showToast('Outreach package ready for review!', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Cover Letter Generator Tab
async function generateStandaloneCoverLetter() {
  const comp = document.getElementById('clCompanyName').value.trim();
  const title = document.getElementById('clJobTitle').value.trim();
  const desc = document.getElementById('clJobDesc').value.trim();
  const pid = document.getElementById('clProfileSelect').value;

  if (!comp || !title) {
    showToast('Please provide Company Name and Job Title', 'warning');
    return;
  }

  try {
    showToast('Synthesizing ATS-optimized cover letter...', 'info');
    const res = await apiFetch('/api/cover-letter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company_name: comp,
        job_title: title,
        job_description: desc,
        profile_id: pid
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed');
    document.getElementById('clOutputText').value = data.cover_letter;
    showToast('Tailored cover letter generated!', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Schedule Settings Tab
async function saveScheduleSettings() {
  const mode = document.getElementById('schedModeSelect').value;
  const timeVal = document.getElementById('schedTimeInput').value;

  try {
    const res = await apiFetch('/api/config');
    const conf = await res.json();
    conf.schedule = {
      enabled: mode === 'daily',
      mode: mode,
      daily_time: timeVal
    };

    const putRes = await apiFetch('/api/config', {
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

// ==========================================================================
// Independent Skills & Roles Settings Management (Section 3 & 7)
// ==========================================================================

function selectSettingsProfile(profileId) {
  state.settingsProfile = profileId;
  const btnAI = document.getElementById('settingsRoleBtnAI');
  const btnTest = document.getElementById('settingsRoleBtnTest');
  if (btnAI && btnTest) {
    btnAI.classList.toggle('active', profileId === 'AI_ENGINEER');
    btnTest.classList.toggle('active', profileId === 'TEST_ENGINEER');
  }
  renderSettingsForm();
}

function renderSettingsForm() {
  const p = state.profiles[state.settingsProfile] || {};
  
  const nameInput = document.getElementById('setContactName');
  const locInput = document.getElementById('setContactLocation');
  const phoneInput = document.getElementById('setContactPhone');
  const emailInput = document.getElementById('setContactEmail');
  const liInput = document.getElementById('setContactLinkedin');
  const ghInput = document.getElementById('setContactGithub');
  const autoApplyBox = document.getElementById('setAutoApplyEnabled');
  const threshInput = document.getElementById('setMatchThreshold');

  if (nameInput) nameInput.value = p.name || 'Kamalesan C';
  if (locInput) locInput.value = p.location || '';
  if (phoneInput) phoneInput.value = p.phone || '';
  if (emailInput) emailInput.value = p.email || '';
  if (liInput) liInput.value = p.linkedin || '';
  if (ghInput) ghInput.value = p.github || '';
  if (autoApplyBox) autoApplyBox.checked = Boolean(p.auto_apply_enabled);
  if (threshInput) threshInput.value = p.match_threshold || 70;

  renderTitlesList();
  renderSkillsList();
  renderExcludeList();
}

function renderTitlesList() {
  const container = document.getElementById('settingsTitlesList');
  if (!container) return;
  const p = state.profiles[state.settingsProfile] || {};
  const titles = p.target_roles || [];
  container.innerHTML = '';

  if (titles.length === 0) {
    container.innerHTML = '<span style="color: var(--text-dim); font-size: 0.8rem;">No titles defined.</span>';
    return;
  }

  titles.forEach((title, idx) => {
    const chip = document.createElement('span');
    chip.className = 'settings-chip';
    chip.innerHTML = `
      <span>${escapeHtml(title)}</span>
      <span class="settings-chip-actions">
        <button class="settings-chip-btn" onclick="editJobTitle(${idx})" title="Edit">✏️</button>
        <button class="settings-chip-btn delete-btn" onclick="deleteJobTitle(${idx})" title="Delete">✕</button>
      </span>
    `;
    container.appendChild(chip);
  });
}

function renderSkillsList() {
  const container = document.getElementById('settingsSkillsList');
  if (!container) return;
  const p = state.profiles[state.settingsProfile] || {};
  const skills = p.technical_skills || [];
  const weights = p.skill_weights || {};
  container.innerHTML = '';

  if (skills.length === 0) {
    container.innerHTML = '<span style="color: var(--text-dim); font-size: 0.8rem;">No skills defined.</span>';
    return;
  }

  skills.forEach((skill, idx) => {
    const chip = document.createElement('span');
    chip.className = 'settings-chip';
    const weight = weights[skill] !== undefined ? weights[skill] : 1.0;
    chip.innerHTML = `
      <span>${escapeHtml(skill)}</span>
      <span class="weight-tag">w: ${weight}</span>
      <span class="settings-chip-actions">
        <button class="settings-chip-btn" onclick="editSkill(${idx})" title="Edit">✏️</button>
        <button class="settings-chip-btn delete-btn" onclick="deleteSkill(${idx})" title="Delete">✕</button>
      </span>
    `;
    container.appendChild(chip);
  });
}

function renderExcludeList() {
  const container = document.getElementById('settingsExcludeList');
  if (!container) return;
  const p = state.profiles[state.settingsProfile] || {};
  const terms = p.exclude_terms || [];
  container.innerHTML = '';

  if (terms.length === 0) {
    container.innerHTML = '<span style="color: var(--text-dim); font-size: 0.8rem;">No excluded terms.</span>';
    return;
  }

  terms.forEach((term, idx) => {
    const chip = document.createElement('span');
    chip.className = 'settings-chip';
    chip.style.borderColor = 'hsla(350, 70%, 50%, 0.3)';
    chip.innerHTML = `
      <span>${escapeHtml(term)}</span>
      <span class="settings-chip-actions">
        <button class="settings-chip-btn" onclick="editExclude(${idx})" title="Edit">✏️</button>
        <button class="settings-chip-btn delete-btn" onclick="deleteExclude(${idx})" title="Delete">✕</button>
      </span>
    `;
    container.appendChild(chip);
  });
}

// Add / Edit / Delete Job Titles
function addJobTitlePrompt() {
  const title = prompt('Enter new target job title:');
  if (!title || !title.trim()) return;
  const clean = title.trim();
  const p = state.profiles[state.settingsProfile];
  if (!p.target_roles) p.target_roles = [];
  if (p.target_roles.includes(clean)) {
    showToast('Job title already exists', 'warning');
    return;
  }
  p.target_roles.push(clean);
  renderTitlesList();
}

function editJobTitle(idx) {
  const p = state.profiles[state.settingsProfile];
  const old = p.target_roles[idx];
  const updated = prompt('Edit job title:', old);
  if (!updated || !updated.trim()) return;
  p.target_roles[idx] = updated.trim();
  renderTitlesList();
}

function deleteJobTitle(idx) {
  const p = state.profiles[state.settingsProfile];
  p.target_roles.splice(idx, 1);
  renderTitlesList();
}

// Add / Edit / Delete Skills & Weights
function addSkillPrompt() {
  const skill = prompt('Enter technical skill name:');
  if (!skill || !skill.trim()) return;
  const clean = skill.trim();
  const p = state.profiles[state.settingsProfile];
  if (!p.technical_skills) p.technical_skills = [];
  if (p.technical_skills.includes(clean)) {
    showToast('Skill already exists', 'warning');
    return;
  }
  const weightStr = prompt('Enter importance weight for ' + clean + ' (e.g. 1.0, 1.2, 1.5):', '1.0');
  const weight = parseFloat(weightStr) || 1.0;
  p.technical_skills.push(clean);
  if (!p.skill_weights) p.skill_weights = {};
  p.skill_weights[clean] = weight;
  renderSkillsList();
}

function editSkill(idx) {
  const p = state.profiles[state.settingsProfile];
  const old = p.technical_skills[idx];
  const currentWeight = (p.skill_weights && p.skill_weights[old] !== undefined) ? p.skill_weights[old] : 1.0;

  const updatedName = prompt('Edit skill name:', old);
  if (!updatedName || !updatedName.trim()) return;
  const cleanName = updatedName.trim();

  const updatedWeightStr = prompt('Edit weight for ' + cleanName + ':', currentWeight);
  const weight = parseFloat(updatedWeightStr) || 1.0;

  p.technical_skills[idx] = cleanName;
  if (!p.skill_weights) p.skill_weights = {};
  if (old !== cleanName) delete p.skill_weights[old];
  p.skill_weights[cleanName] = weight;

  renderSkillsList();
}

function deleteSkill(idx) {
  const p = state.profiles[state.settingsProfile];
  const old = p.technical_skills[idx];
  p.technical_skills.splice(idx, 1);
  if (p.skill_weights && p.skill_weights[old] !== undefined) {
    delete p.skill_weights[old];
  }
  renderSkillsList();
}

// Add / Edit / Delete Excluded Terms
function addExcludePrompt() {
  const term = prompt('Enter keyword to exclude / disqualify:');
  if (!term || !term.trim()) return;
  const clean = term.trim().toLowerCase();
  const p = state.profiles[state.settingsProfile];
  if (!p.exclude_terms) p.exclude_terms = [];
  if (p.exclude_terms.includes(clean)) {
    showToast('Keyword already in exclusion list', 'warning');
    return;
  }
  p.exclude_terms.push(clean);
  renderExcludeList();
}

function editExclude(idx) {
  const p = state.profiles[state.settingsProfile];
  const old = p.exclude_terms[idx];
  const updated = prompt('Edit excluded keyword:', old);
  if (!updated || !updated.trim()) return;
  p.exclude_terms[idx] = updated.trim().toLowerCase();
  renderExcludeList();
}

function deleteExclude(idx) {
  const p = state.profiles[state.settingsProfile];
  p.exclude_terms.splice(idx, 1);
  renderExcludeList();
}

// Save Profile Settings (PUT /api/profiles/{profile_id})
async function saveActiveProfileSettings() {
  const pid = state.settingsProfile;
  const p = state.profiles[pid];
  if (!p) return;

  const nameVal = document.getElementById('setContactName').value.trim();
  const locVal = document.getElementById('setContactLocation').value.trim();
  const phoneVal = document.getElementById('setContactPhone').value.trim();
  const emailVal = document.getElementById('setContactEmail').value.trim();
  const liVal = document.getElementById('setContactLinkedin').value.trim();
  const ghVal = document.getElementById('setContactGithub').value.trim();
  const autoApply = document.getElementById('setAutoApplyEnabled').checked;
  const thresh = parseInt(document.getElementById('setMatchThreshold').value) || 70;

  const payload = {
    personal: {
      name: nameVal,
      location: locVal,
      phone: phoneVal,
      email: emailVal,
      linkedin: liVal,
      github: ghVal
    },
    name: nameVal,
    location: locVal,
    phone: phoneVal,
    email: emailVal,
    linkedin: liVal,
    github: ghVal,
    auto_apply_enabled: autoApply,
    match_threshold: thresh,
    target_roles: p.target_roles || [],
    technical_skills: p.technical_skills || [],
    skill_weights: p.skill_weights || {},
    exclude_terms: p.exclude_terms || []
  };

  try {
    showToast('Saving profile settings...', 'info');
    const res = await apiFetch(`/api/profiles/${pid}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to save');
    state.profiles[pid] = data.profile;
    showToast(`Profile settings for ${pid === 'AI_ENGINEER' ? 'AI Engineer' : 'Test Engineer'} saved successfully!`, 'success');
    renderHeaderProfile();
    renderSettingsForm();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Reset to Defaults (POST /api/profiles/{profile_id}/reset)
async function resetActiveProfileDefaults() {
  const pid = state.settingsProfile;
  if (!confirm(`Are you sure you want to reset ${pid === 'AI_ENGINEER' ? 'AI Engineer' : 'Test Engineer'} settings to default values?`)) {
    return;
  }

  try {
    showToast('Resetting profile to defaults...', 'info');
    const res = await apiFetch(`/api/profiles/${pid}/reset`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Reset failed');
    state.profiles[pid] = data.profile;
    showToast(`Profile ${pid} reset to default configuration!`, 'success');
    renderHeaderProfile();
    renderSettingsForm();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

