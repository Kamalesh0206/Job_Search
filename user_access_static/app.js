// ==========================================================================
// AccessHub Frontend Application Logic
// Enterprise Identity & Host System Management Portal
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  // Global State
  const state = {
    currentTab: 'overview',
    systemInfo: null,
    users: [],
    roles: [],
    activityLogs: [],
    tokens: [],
    filters: {
      search: '',
      role: 'All',
      status: 'All'
    }
  };

  // DOM Elements
  const navTabs = document.querySelectorAll('.nav-item');
  const tabPanes = document.querySelectorAll('.tab-pane');
  const pageMainHeading = document.getElementById('pageMainHeading');

  // Modals
  const userModalOverlay = document.getElementById('userModalOverlay');
  const tokenModalOverlay = document.getElementById('tokenModalOverlay');
  const userForm = document.getElementById('userForm');
  const tokenForm = document.getElementById('tokenForm');

  // Host Controls
  const newHostnameInput = document.getElementById('newHostnameInput');
  const hostnameCharCount = document.getElementById('hostnameCharCount');
  const hostnameValidationMsg = document.getElementById('hostnameValidationMsg');
  const btnValidateHostname = document.getElementById('btnValidateHostname');
  const btnApplyElevation = document.getElementById('btnApplyElevation');
  const btnShowScriptCommands = document.getElementById('btnShowScriptCommands');
  const commandsDrawer = document.getElementById('commandsDrawer');
  const btnCloseCommandsDrawer = document.getElementById('btnCloseCommandsDrawer');
  const btnCopyPsCommand = document.getElementById('btnCopyPsCommand');
  const btnCopyCmdCommand = document.getElementById('btnCopyCmdCommand');

  // Quick Action buttons
  const btnTopChangeHost = document.getElementById('btnTopChangeHost');
  const btnTopAddUser = document.getElementById('btnTopAddUser');
  const btnHeroRename = document.getElementById('btnHeroRename');
  const btnHeroViewAudit = document.getElementById('btnHeroViewAudit');
  const btnOverviewSeeAllUsers = document.getElementById('btnOverviewSeeAllUsers');
  const btnOverviewSeeAllAudit = document.getElementById('btnOverviewSeeAllAudit');
  const btnCreateUserModal = document.getElementById('btnCreateUserModal');
  const btnExportUsersJson = document.getElementById('btnExportUsersJson');
  const btnNewTokenModal = document.getElementById('btnNewTokenModal');
  const btnRefreshHostInfo = document.getElementById('btnRefreshHostInfo');

  // Search & Filter Inputs
  const userSearchInput = document.getElementById('userSearchInput');
  const userRoleFilter = document.getElementById('userRoleFilter');
  const userStatusFilter = document.getElementById('userStatusFilter');
  const auditSearchInput = document.getElementById('auditSearchInput');

  // ================= 1. TAB ROUTING & SWITCHING =================
  function switchTab(tabId) {
    state.currentTab = tabId;

    navTabs.forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
    });

    tabPanes.forEach(pane => {
      pane.classList.remove('active');
    });

    const targetPaneId = 'pane' + tabId.charAt(0).toUpperCase() + tabId.slice(1);
    const targetPane = document.getElementById(targetPaneId);
    if (targetPane) {
      targetPane.classList.add('active');
    }

    // Update main heading based on tab
    const titles = {
      overview: 'User Access & Host Management Dashboard',
      users: 'User Identity & Access Directory',
      host: 'Windows Host Name & System Configuration',
      roles: 'Role-Based Access Control (RBAC) Matrix',
      audit: 'Security Activity & Access Audit Log',
      tokens: 'Service Accounts & API Access Tokens'
    };
    if (pageMainHeading && titles[tabId]) {
      pageMainHeading.textContent = titles[tabId];
    }
  }

  navTabs.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.getAttribute('data-tab');
      switchTab(tabId);
    });
  });

  if (btnTopChangeHost) btnTopChangeHost.addEventListener('click', () => switchTab('host'));
  if (btnHeroRename) btnHeroRename.addEventListener('click', () => switchTab('host'));
  if (btnHeroViewAudit) btnHeroViewAudit.addEventListener('click', () => switchTab('audit'));
  if (btnOverviewSeeAllUsers) btnOverviewSeeAllUsers.addEventListener('click', () => switchTab('users'));
  if (btnOverviewSeeAllAudit) btnOverviewSeeAllAudit.addEventListener('click', () => switchTab('audit'));

  const quickHostTag = document.getElementById('quickHostTag');
  if (quickHostTag) quickHostTag.addEventListener('click', () => switchTab('host'));

  // ================= 2. DATA FETCHING =================
  async function fetchSystemInfo() {
    try {
      const res = await fetch('/api/system/info');
      if (!res.ok) throw new Error('Failed to fetch system info');
      const data = await res.json();
      state.systemInfo = data;
      renderSystemInfo(data);
    } catch (err) {
      console.error(err);
      showToast('Could not refresh host system info', 'error');
    }
  }

  async function fetchUsers() {
    try {
      const res = await fetch('/api/users');
      if (!res.ok) throw new Error('Failed to fetch users');
      const data = await res.json();
      state.users = data.users || [];
      renderUsersTable();
      renderOverviewUsers();
    } catch (err) {
      console.error(err);
      showToast('Failed to load user directory', 'error');
    }
  }

  async function fetchRoles() {
    try {
      const res = await fetch('/api/roles');
      if (!res.ok) throw new Error('Failed to fetch roles');
      const data = await res.json();
      state.roles = data.roles || [];
      renderRolesCards();
    } catch (err) {
      console.error(err);
    }
  }

  async function fetchActivity() {
    try {
      const res = await fetch('/api/activity');
      if (!res.ok) throw new Error('Failed to fetch activity');
      const data = await res.json();
      state.activityLogs = data.logs || [];
      renderAuditTable();
      renderOverviewAudit();
    } catch (err) {
      console.error(err);
    }
  }

  async function fetchTokens() {
    try {
      const res = await fetch('/api/tokens');
      if (!res.ok) throw new Error('Failed to fetch tokens');
      const data = await res.json();
      state.tokens = data.tokens || [];
      renderTokensTable();
    } catch (err) {
      console.error(err);
    }
  }

  // ================= 3. RENDER FUNCTIONS =================
  function renderSystemInfo(info) {
    if (!info) return;

    // Sidebar
    const sidebarHostName = document.getElementById('sidebarHostName');
    const sidebarHostIp = document.getElementById('sidebarHostIp');
    if (sidebarHostName) sidebarHostName.textContent = info.hostname;
    if (sidebarHostIp && info.ip_addresses && info.ip_addresses.length) {
      const mainIp = info.ip_addresses.find(ip => ip !== '127.0.0.1') || info.ip_addresses[0];
      sidebarHostIp.textContent = `${mainIp}:8080`;
    }

    // Topbar
    const topHostValue = document.getElementById('topHostValue');
    if (topHostValue) topHostValue.textContent = info.hostname;

    // Overview Stats
    const statTotalUsers = document.getElementById('statTotalUsers');
    const statActiveUsers = document.getElementById('statActiveUsers');
    const statHostName = document.getElementById('statHostName');
    const statHostIp = document.getElementById('statHostIp');
    const statUptime = document.getElementById('statUptime');

    if (statTotalUsers) statTotalUsers.textContent = info.total_users;
    if (statActiveUsers) statActiveUsers.textContent = info.active_users;
    if (statHostName) statHostName.textContent = info.hostname;
    if (statHostIp) {
      const mainIp = (info.ip_addresses || []).find(ip => ip !== '127.0.0.1') || '127.0.0.1';
      statHostIp.textContent = mainIp;
    }
    if (statUptime) statUptime.textContent = info.uptime || 'Active';

    // Hero Card
    const heroHostName = document.getElementById('heroHostName');
    const heroOsVersion = document.getElementById('heroOsVersion');
    const heroLoggedUser = document.getElementById('heroLoggedUser');
    const heroLastUpdate = document.getElementById('heroLastUpdate');
    const heroNetworkUrl = document.getElementById('heroNetworkUrl');

    if (heroHostName) heroHostName.textContent = info.hostname;
    if (heroOsVersion) heroOsVersion.textContent = info.os_name;
    if (heroLoggedUser) heroLoggedUser.textContent = `${info.username} (Kamalesan C)`;
    if (heroLastUpdate) heroLastUpdate.textContent = info.last_hotfix;
    if (heroNetworkUrl) heroNetworkUrl.textContent = `http://${info.hostname}:8080`;

    // Host Management Tab details
    const hostDetailName = document.getElementById('hostDetailName');
    const hostDetailComputer = document.getElementById('hostDetailComputer');
    const hostDetailIps = document.getElementById('hostDetailIps');
    const hostDetailOs = document.getElementById('hostDetailOs');
    const hostDetailArch = document.getElementById('hostDetailArch');
    const hostDetailLastUpdate = document.getElementById('hostDetailLastUpdate');
    const hostDetailAdminStatus = document.getElementById('hostDetailAdminStatus');

    if (hostDetailName) hostDetailName.textContent = info.hostname;
    if (hostDetailComputer) hostDetailComputer.textContent = info.computer_name;
    if (hostDetailIps) hostDetailIps.textContent = (info.ip_addresses || []).join(', ');
    if (hostDetailOs) hostDetailOs.textContent = info.os_name;
    if (hostDetailArch) hostDetailArch.textContent = `${info.architecture} Architecture`;
    if (hostDetailLastUpdate) hostDetailLastUpdate.textContent = info.last_hotfix;
    if (hostDetailAdminStatus) {
      hostDetailAdminStatus.textContent = info.is_admin ? 'Administrator (Direct)' : 'Standard User (Elevation via UAC)';
    }

    // Set initial preview code
    updateHostPreviews(info.hostname);
  }

  function renderOverviewUsers() {
    const tbody = document.getElementById('overviewUsersTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const displayUsers = state.users.slice(0, 5);
    displayUsers.forEach(u => {
      const tr = document.createElement('tr');
      const initials = (u.full_name || u.username).split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
      const roleClass = getRoleClass(u.role);
      const statusClass = `status-${u.status.toLowerCase()}`;

      tr.innerHTML = `
        <td>
          <div class="user-cell">
            <div class="avatar" style="background-color: ${u.avatar_color || '#6366f1'}; width: 32px; height: 32px; font-size: 0.75rem;">${initials}</div>
            <div class="user-cell-meta">
              <span class="user-cell-name">${escapeHtml(u.full_name)}</span>
              <span class="user-cell-username">@${escapeHtml(u.username)}</span>
            </div>
          </div>
        </td>
        <td><span class="pill-role ${roleClass}">${escapeHtml(u.role)}</span></td>
        <td><span class="status-pill ${statusClass}">${escapeHtml(u.status)}</span></td>
        <td class="monospace" style="font-size: 0.78rem; color: var(--text-muted);">${escapeHtml(u.last_login)}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  function renderOverviewAudit() {
    const container = document.getElementById('overviewAuditList');
    if (!container) return;
    container.innerHTML = '';

    const recentLogs = state.activityLogs.slice(0, 5);
    recentLogs.forEach(log => {
      const div = document.createElement('div');
      div.className = 'audit-item';
      const badgeClass = log.severity || 'info';

      div.innerHTML = `
        <div class="audit-item-left">
          <span class="audit-badge ${badgeClass}">${escapeHtml(log.severity || 'INFO')}</span>
          <div>
            <strong>${escapeHtml(log.action)}</strong>
            <span style="color: var(--text-muted); margin-left: 6px;">${escapeHtml(log.target)}</span>
          </div>
        </div>
        <div class="monospace" style="font-size: 0.74rem; color: var(--text-muted);">
          ${escapeHtml(log.timestamp)}
        </div>
      `;
      container.appendChild(div);
    });
  }

  function renderUsersTable() {
    const tbody = document.getElementById('usersTableBody');
    const countLabel = document.getElementById('usersTableCount');
    const navUserCount = document.getElementById('navUserCount');
    if (!tbody) return;
    tbody.innerHTML = '';

    const filtered = state.users.filter(u => {
      const q = state.filters.search.toLowerCase().trim();
      const matchesSearch = !q || 
        u.username.toLowerCase().includes(q) || 
        u.full_name.toLowerCase().includes(q) || 
        u.email.toLowerCase().includes(q);

      const matchesRole = state.filters.role === 'All' || u.role === state.filters.role;
      const matchesStatus = state.filters.status === 'All' || u.status === state.filters.status;

      return matchesSearch && matchesRole && matchesStatus;
    });

    if (countLabel) countLabel.textContent = `Showing ${filtered.length} of ${state.users.length} users`;
    if (navUserCount) navUserCount.textContent = state.users.length;

    if (filtered.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" style="text-align: center; padding: 32px; color: var(--text-muted);">
            No user accounts found matching your filter criteria.
          </td>
        </tr>
      `;
      return;
    }

    filtered.forEach(u => {
      const tr = document.createElement('tr');
      const initials = (u.full_name || u.username).split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
      const roleClass = getRoleClass(u.role);
      const statusClass = `status-${u.status.toLowerCase()}`;

      tr.innerHTML = `
        <td>
          <div class="user-cell">
            <div class="avatar" style="background-color: ${u.avatar_color || '#6366f1'}">${initials}</div>
            <div class="user-cell-meta">
              <span class="user-cell-name">${escapeHtml(u.full_name)}</span>
              <span class="user-cell-username">@${escapeHtml(u.username)}</span>
            </div>
          </div>
        </td>
        <td class="monospace" style="font-size: 0.82rem;">${escapeHtml(u.email)}</td>
        <td>${escapeHtml(u.department || 'General')}</td>
        <td><span class="pill-role ${roleClass}">${escapeHtml(u.role)}</span></td>
        <td>
          ${u.two_factor 
            ? `<span style="color: var(--accent-emerald); font-size: 0.8rem; font-weight: 600;">&#10003; Enforced</span>` 
            : `<span style="color: var(--text-dim); font-size: 0.8rem;">Optional</span>`}
        </td>
        <td><span class="status-pill ${statusClass}">${escapeHtml(u.status)}</span></td>
        <td class="monospace" style="font-size: 0.78rem; color: var(--text-muted);">${escapeHtml(u.last_login)}</td>
        <td class="text-right">
          <button class="btn-action-icon" data-action="toggle" data-id="${u.id}" title="Toggle Active / Suspended">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px; height:14px;">
              <path d="M18.36 6.64a9 9 0 1 1-12.73 0"/>
              <line x1="12" y1="2" x2="12" y2="12"/>
            </svg>
          </button>
          <button class="btn-action-icon" data-action="edit" data-id="${u.id}" title="Edit User">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px; height:14px;">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </button>
          <button class="btn-action-icon danger" data-action="delete" data-id="${u.id}" title="Delete User">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px; height:14px;">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    // Attach row button events
    tbody.querySelectorAll('[data-action="toggle"]').forEach(btn => {
      btn.addEventListener('click', () => toggleUserStatus(btn.getAttribute('data-id')));
    });
    tbody.querySelectorAll('[data-action="edit"]').forEach(btn => {
      btn.addEventListener('click', () => openEditUserModal(btn.getAttribute('data-id')));
    });
    tbody.querySelectorAll('[data-action="delete"]').forEach(btn => {
      btn.addEventListener('click', () => deleteUser(btn.getAttribute('data-id')));
    });
  }

  function renderRolesCards() {
    const grid = document.getElementById('rolesCardsGrid');
    if (!grid) return;
    grid.innerHTML = '';

    state.roles.forEach(r => {
      const div = document.createElement('div');
      div.className = 'role-card';
      const badgeClass = getRoleClass(r.name);

      div.innerHTML = `
        <div class="role-card-header">
          <span class="role-title">${escapeHtml(r.name)}</span>
          <span class="pill-role ${badgeClass}">${r.permissions.length} Grants</span>
        </div>
        <p class="role-desc">${escapeHtml(r.description)}</p>
        <div class="permissions-tag-list">
          ${r.permissions.map(p => `<span class="perm-tag">${escapeHtml(p)}</span>`).join('')}
        </div>
      `;
      grid.appendChild(div);
    });
  }

  function renderAuditTable() {
    const tbody = document.getElementById('auditTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const filterVal = (auditSearchInput ? auditSearchInput.value : '').toLowerCase().trim();
    const filtered = state.activityLogs.filter(log => {
      if (!filterVal) return true;
      return (log.user || '').toLowerCase().includes(filterVal) ||
             (log.action || '').toLowerCase().includes(filterVal) ||
             (log.target || '').toLowerCase().includes(filterVal) ||
             (log.ip || '').toLowerCase().includes(filterVal);
    });

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--text-muted);">No matching audit log entries.</td></tr>`;
      return;
    }

    filtered.forEach(log => {
      const tr = document.createElement('tr');
      const badgeClass = log.severity || 'info';

      tr.innerHTML = `
        <td class="monospace" style="font-size: 0.78rem; color: var(--text-muted);">${escapeHtml(log.timestamp)}</td>
        <td><strong style="color: #fff;">${escapeHtml(log.user)}</strong></td>
        <td><strong>${escapeHtml(log.action)}</strong></td>
        <td><span class="monospace" style="font-size: 0.82rem; color: hsl(215, 30%, 85%);">${escapeHtml(log.target)}</span></td>
        <td class="monospace" style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(log.ip)}</td>
        <td><span class="audit-badge ${badgeClass}">${escapeHtml(log.severity || 'INFO')}</span></td>
        <td><span class="status-pill status-active">${escapeHtml(log.status || 'Success')}</span></td>
      `;
      tbody.appendChild(tr);
    });
  }

  function renderTokensTable() {
    const tbody = document.getElementById('tokensTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (state.tokens.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--text-muted);">No API tokens generated yet.</td></tr>`;
      return;
    }

    state.tokens.forEach(tok => {
      const tr = document.createElement('tr');
      const roleClass = getRoleClass(tok.role);

      tr.innerHTML = `
        <td><strong>${escapeHtml(tok.name)}</strong></td>
        <td><code class="preview-code text-cyan">${escapeHtml(tok.prefix)}</code></td>
        <td><span class="pill-role ${roleClass}">${escapeHtml(tok.role)}</span></td>
        <td class="monospace" style="font-size: 0.8rem;">${escapeHtml(tok.created_at)}</td>
        <td class="monospace" style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(tok.last_used)}</td>
        <td><span class="status-pill status-active">${escapeHtml(tok.status)}</span></td>
        <td class="text-right">
          <button class="btn btn-xs btn-outline" data-action="revoke-token" data-id="${tok.id}">Revoke</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll('[data-action="revoke-token"]').forEach(btn => {
      btn.addEventListener('click', () => revokeToken(btn.getAttribute('data-id')));
    });
  }

  // Helper for Role Class Styling
  function getRoleClass(role) {
    if (!role) return 'role-viewer';
    const r = role.toLowerCase();
    if (r.includes('super admin')) return 'role-super-admin';
    if (r.includes('infra')) return 'role-infra-admin';
    if (r.includes('devops')) return 'role-devops';
    if (r.includes('security')) return 'role-security';
    if (r.includes('operator')) return 'role-operator';
    return 'role-viewer';
  }

  // ================= 4. HOST NAME MANAGEMENT ENGINE =================
  function updateHostPreviews(name) {
    const validName = (name && name.trim()) ? name.trim().toUpperCase() : 'NEW-HOSTNAME';
    const previewLanUrl = document.getElementById('previewLanUrl');
    const previewNetBios = document.getElementById('previewNetBios');
    const codePsCommand = document.getElementById('codePsCommand');
    const codeCmdCommand = document.getElementById('codeCmdCommand');

    if (previewLanUrl) previewLanUrl.textContent = `http://${validName}:8080`;
    if (previewNetBios) previewNetBios.textContent = `\\\\${validName}`;
    if (codePsCommand) codePsCommand.textContent = `Rename-Computer -NewName "${validName}" -Force -Restart:$false`;
    if (codeCmdCommand) codeCmdCommand.textContent = `wmic computersystem where caption='%COMPUTERNAME%' rename ${validName}`;
  }

  if (newHostnameInput) {
    newHostnameInput.addEventListener('input', (e) => {
      const val = e.target.value.toUpperCase();
      e.target.value = val;
      const len = val.length;
      if (hostnameCharCount) {
        hostnameCharCount.textContent = `${len} / 15 chars`;
      }
      updateHostPreviews(val);
      validateHostnameClientSide(val);
    });
  }

  function validateHostnameClientSide(val) {
    if (!hostnameValidationMsg) return false;
    val = val.trim();

    if (!val) {
      hostnameValidationMsg.className = 'validation-message';
      hostnameValidationMsg.textContent = '';
      return false;
    }

    if (val.length > 15) {
      hostnameValidationMsg.className = 'validation-message error';
      hostnameValidationMsg.textContent = 'Host name cannot exceed 15 characters (Windows NetBIOS limit).';
      return false;
    }

    const regex = /^[A-Z0-9][A-Z0-9\-]*[A-Z0-9]$/;
    if (val.length === 1 && /^[A-Z0-9]$/.test(val)) {
      hostnameValidationMsg.className = 'validation-message success';
      hostnameValidationMsg.textContent = 'Valid 1-character host name.';
      return true;
    }

    if (!regex.test(val)) {
      hostnameValidationMsg.className = 'validation-message error';
      hostnameValidationMsg.textContent = 'Can only contain letters, numbers, and hyphens. Cannot start or end with a hyphen.';
      return false;
    }

    if (state.systemInfo && val.toLowerCase() === (state.systemInfo.hostname || '').toLowerCase()) {
      hostnameValidationMsg.className = 'validation-message error';
      hostnameValidationMsg.textContent = `"${val}" is already the current host name.`;
      return false;
    }

    hostnameValidationMsg.className = 'validation-message success';
    hostnameValidationMsg.textContent = `Valid host name: "${val}". Ready to apply.`;
    return true;
  }

  if (btnValidateHostname) {
    btnValidateHostname.addEventListener('click', async () => {
      const name = (newHostnameInput.value || '').trim();
      if (!name) {
        showToast('Please type a host name to validate', 'warning');
        return;
      }
      try {
        const res = await fetch('/api/system/hostname/validate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ new_hostname: name })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Validation failed');
        showToast(`Host name "${data.new_hostname}" is valid!`, 'success');
        validateHostnameClientSide(data.new_hostname);
      } catch (err) {
        showToast(err.message, 'error');
        if (hostnameValidationMsg) {
          hostnameValidationMsg.className = 'validation-message error';
          hostnameValidationMsg.textContent = err.message;
        }
      }
    });
  }

  // Trigger Windows UAC elevation popup
  if (btnApplyElevation) {
    btnApplyElevation.addEventListener('click', async () => {
      const val = (newHostnameInput.value || '').trim();
      if (!val) {
        showToast('Please enter a new computer host name first', 'warning');
        newHostnameInput.focus();
        return;
      }

      if (!validateHostnameClientSide(val)) {
        showToast('Please fix validation errors before applying', 'error');
        return;
      }

      if (!confirm(`Are you sure you want to rename this computer host to "${val}"?\n\nThis will trigger Windows Administrator elevation. A system restart is required afterward.`)) {
        return;
      }

      try {
        btnApplyElevation.disabled = true;
        btnApplyElevation.innerHTML = '<span>Triggering Elevation...</span>';

        const res = await fetch('/api/system/hostname/launch-elevation', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ new_hostname: val })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to trigger elevation');

        showToast(data.message, 'success');
        if (commandsDrawer) commandsDrawer.style.display = 'block';
        fetchActivity();
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        btnApplyElevation.disabled = false;
        btnApplyElevation.innerHTML = `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span>Apply Host Name via Windows UAC</span>
        `;
      }
    });
  }

  // Toggle Command Drawer
  if (btnShowScriptCommands) {
    btnShowScriptCommands.addEventListener('click', () => {
      if (commandsDrawer) {
        commandsDrawer.style.display = commandsDrawer.style.display === 'none' ? 'block' : 'none';
      }
    });
  }

  if (btnCloseCommandsDrawer) {
    btnCloseCommandsDrawer.addEventListener('click', () => {
      if (commandsDrawer) commandsDrawer.style.display = 'none';
    });
  }

  // Copy Commands to Clipboard
  if (btnCopyPsCommand) {
    btnCopyPsCommand.addEventListener('click', () => {
      const text = document.getElementById('codePsCommand').textContent;
      copyToClipboard(text, 'PowerShell command copied to clipboard!');
    });
  }

  if (btnCopyCmdCommand) {
    btnCopyCmdCommand.addEventListener('click', () => {
      const text = document.getElementById('codeCmdCommand').textContent;
      copyToClipboard(text, 'CMD command copied to clipboard!');
    });
  }

  if (btnRefreshHostInfo) {
    btnRefreshHostInfo.addEventListener('click', () => {
      fetchSystemInfo();
      showToast('Host telemetry refreshed', 'success');
    });
  }

  // ================= 5. USER CRUD MODALS & OPERATIONS =================
  function openAddUserModal() {
    userForm.reset();
    document.getElementById('formUserId').value = '';
    document.getElementById('userModalTitle').textContent = 'Add New User';
    document.getElementById('formUsername').disabled = false;
    userModalOverlay.style.display = 'flex';
  }

  function openEditUserModal(userId) {
    const user = state.users.find(u => u.id === userId);
    if (!user) return;

    document.getElementById('formUserId').value = user.id;
    document.getElementById('formUsername').value = user.username;
    document.getElementById('formUsername').disabled = true; // username locked
    document.getElementById('formFullName').value = user.full_name;
    document.getElementById('formEmail').value = user.email;
    document.getElementById('formRole').value = user.role;
    document.getElementById('formDepartment').value = user.department || '';
    document.getElementById('formStatus').value = user.status;
    document.getElementById('formTwoFactor').checked = Boolean(user.two_factor);

    document.getElementById('userModalTitle').textContent = `Edit User: @${user.username}`;
    userModalOverlay.style.display = 'flex';
  }

  function closeUserModal() {
    userModalOverlay.style.display = 'none';
  }

  if (btnTopAddUser) btnTopAddUser.addEventListener('click', openAddUserModal);
  if (btnCreateUserModal) btnCreateUserModal.addEventListener('click', openAddUserModal);
  if (document.getElementById('btnCloseUserModal')) {
    document.getElementById('btnCloseUserModal').addEventListener('click', closeUserModal);
  }
  if (document.getElementById('btnCancelUserModal')) {
    document.getElementById('btnCancelUserModal').addEventListener('click', closeUserModal);
  }

  userForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const userId = document.getElementById('formUserId').value;
    const isEdit = Boolean(userId);

    const payload = {
      username: document.getElementById('formUsername').value.trim(),
      full_name: document.getElementById('formFullName').value.trim(),
      email: document.getElementById('formEmail').value.trim(),
      role: document.getElementById('formRole').value,
      department: document.getElementById('formDepartment').value.trim(),
      status: document.getElementById('formStatus').value,
      two_factor: document.getElementById('formTwoFactor').checked
    };

    try {
      let res;
      if (isEdit) {
        res = await fetch(`/api/users/${userId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      } else {
        res = await fetch('/api/users', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to save user');

      showToast(data.message || 'User saved successfully!', 'success');
      closeUserModal();
      fetchUsers();
      fetchActivity();
      fetchSystemInfo();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  async function toggleUserStatus(userId) {
    try {
      const res = await fetch(`/api/users/${userId}/toggle-status`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to toggle status');

      showToast(`User status set to ${data.status}`, 'success');
      fetchUsers();
      fetchActivity();
      fetchSystemInfo();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  async function deleteUser(userId) {
    const user = state.users.find(u => u.id === userId);
    const username = user ? user.username : userId;
    if (!confirm(`Are you sure you want to permanently delete user @${username}?`)) {
      return;
    }

    try {
      const res = await fetch(`/api/users/${userId}`, { method: 'DELETE' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to delete user');

      showToast(data.message || 'User deleted', 'success');
      fetchUsers();
      fetchActivity();
      fetchSystemInfo();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  // Export Users JSON
  if (btnExportUsersJson) {
    btnExportUsersJson.addEventListener('click', () => {
      const jsonStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(state.users, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", jsonStr);
      downloadAnchor.setAttribute("download", `accesshub_users_${new Date().toISOString().slice(0,10)}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      showToast('User directory exported successfully', 'success');
    });
  }

  // ================= 6. SEARCH & FILTERS =================
  if (userSearchInput) {
    userSearchInput.addEventListener('input', (e) => {
      state.filters.search = e.target.value;
      renderUsersTable();
    });
  }

  if (userRoleFilter) {
    userRoleFilter.addEventListener('change', (e) => {
      state.filters.role = e.target.value;
      renderUsersTable();
    });
  }

  if (userStatusFilter) {
    userStatusFilter.addEventListener('change', (e) => {
      state.filters.status = e.target.value;
      renderUsersTable();
    });
  }

  if (auditSearchInput) {
    auditSearchInput.addEventListener('input', () => {
      renderAuditTable();
    });
  }

  // ================= 7. API TOKENS =================
  function openTokenModal() {
    tokenForm.reset();
    tokenModalOverlay.style.display = 'flex';
  }

  function closeTokenModal() {
    tokenModalOverlay.style.display = 'none';
  }

  if (btnNewTokenModal) btnNewTokenModal.addEventListener('click', openTokenModal);
  if (document.getElementById('btnCloseTokenModal')) {
    document.getElementById('btnCloseTokenModal').addEventListener('click', closeTokenModal);
  }
  if (document.getElementById('btnCancelTokenModal')) {
    document.getElementById('btnCancelTokenModal').addEventListener('click', closeTokenModal);
  }

  tokenForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      name: document.getElementById('formTokenName').value.trim(),
      role: document.getElementById('formTokenRole').value
    };

    try {
      const res = await fetch('/api/tokens', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to create token');

      showToast('API token generated successfully!', 'success');
      closeTokenModal();
      fetchTokens();
      fetchActivity();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  async function revokeToken(tokenId) {
    if (!confirm('Revoke this API token immediately? Any service using this key will lose access.')) {
      return;
    }
    try {
      const res = await fetch(`/api/tokens/${tokenId}`, { method: 'DELETE' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to revoke token');

      showToast(data.message || 'Token revoked', 'warning');
      fetchTokens();
      fetchActivity();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  // ================= 8. UTILITIES =================
  function copyToClipboard(text, successMsg) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        showToast(successMsg, 'success');
      }).catch(() => fallbackCopy(text, successMsg));
    } else {
      fallbackCopy(text, successMsg);
    }
  }

  function fallbackCopy(text, successMsg) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
      showToast(successMsg, 'success');
    } catch (e) {
      showToast('Could not copy automatically. Please copy manually.', 'warning');
    }
    document.body.removeChild(textArea);
  }

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

  // Initialize Data
  fetchSystemInfo();
  fetchUsers();
  fetchRoles();
  fetchActivity();
  fetchTokens();
});
