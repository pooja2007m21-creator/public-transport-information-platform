/**
 * Admin Portal JavaScript - Comprehensive CRUD and Chart Analytics
 */

// Verify Admin authentication on every admin page
function checkAdminAccess() {
  const user = getStoredUser();
  if (!user || (user.role !== "ADMIN" && user.role !== "OPERATOR")) {
    window.location.href = "/admin/login.html";
    return false;
  }
  const adminNameEl = document.getElementById("admin-user-display");
  if (adminNameEl) adminNameEl.textContent = `${user.full_name} (${user.role})`;
  return true;
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!checkAdminAccess()) return;

  // Initialize specific Admin Page Views
  if (document.getElementById("admin-dashboard-stats")) {
    await loadAdminDashboard();
  } else if (document.getElementById("admin-users-table-body")) {
    await loadAdminUsers();
    setupAdminUserSearch();
  } else if (document.getElementById("admin-routes-table-body")) {
    await loadAdminRoutes();
    setupAdminRouteForms();
  } else if (document.getElementById("admin-stops-table-body")) {
    await loadAdminStops();
    setupAdminStopForms();
  } else if (document.getElementById("admin-schedules-table-body")) {
    await loadAdminSchedules();
    setupAdminScheduleForms();
  } else if (document.getElementById("admin-fares-table-body")) {
    await loadAdminFares();
    setupAdminFareForms();
  } else if (document.getElementById("admin-alerts-table-body")) {
    await loadAdminAlerts();
    setupAdminAlertForms();
  }
});

// ==========================================
// 1. ADMIN DASHBOARD & CHARTS
// ==========================================
async function loadAdminDashboard() {
  showLoading();
  try {
    const data = await apiRequest("/api/admin/dashboard");

    // Stat Cards
    document.getElementById("adm-stat-users").textContent = data.total_users;
    document.getElementById("adm-stat-routes").textContent = data.total_routes;
    document.getElementById("adm-stat-stops").textContent = data.total_stops;
    document.getElementById("adm-stat-active-routes").textContent = data.active_routes;
    document.getElementById("adm-stat-alerts").textContent = data.active_alerts;
    document.getElementById("adm-stat-operators").textContent = data.total_operators;

    // Render Recent Users
    const recentUsersTbody = document.getElementById("adm-recent-users-body");
    if (recentUsersTbody && data.recent_users) {
      recentUsersTbody.innerHTML = data.recent_users.map(u => `
        <tr>
          <td><span class="fw-bold">${u.full_name}</span><br><small class="text-muted">@${u.username}</small></td>
          <td>${u.email}</td>
          <td><span class="badge bg-primary text-uppercase">${u.role}</span></td>
          <td>${getStatusBadge(u.status)}</td>
          <td><small class="text-muted">${new Date(u.created_at).toLocaleDateString()}</small></td>
        </tr>
      `).join("");
    }

    // Render Recent Alerts
    const recentAlertsTbody = document.getElementById("adm-recent-alerts-body");
    if (recentAlertsTbody && data.recent_alerts) {
      recentAlertsTbody.innerHTML = data.recent_alerts.map(a => `
        <tr>
          <td>${getPriorityBadge(a.priority)}</td>
          <td><strong>${a.title}</strong></td>
          <td><span class="badge bg-secondary">${a.route_number || 'All'}</span></td>
          <td>${getStatusBadge(a.status)}</td>
        </tr>
      `).join("");
    }

    // Initialize Chart.js Visualizations
    initAdminCharts(data);

  } catch (err) {
    showToast("Error loading admin dashboard: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

function initAdminCharts(data) {
  if (typeof Chart === "undefined") return;

  // Chart 1: Route Status Distribution
  const routeCanvas = document.getElementById("chart-route-status");
  if (routeCanvas) {
    const routeLabels = Object.keys(data.route_status_breakdown || {});
    const routeValues = Object.values(data.route_status_breakdown || {});

    new Chart(routeCanvas, {
      type: "doughnut",
      data: {
        labels: routeLabels.length ? routeLabels : ["ACTIVE", "DELAYED", "SUSPENDED"],
        datasets: [{
          data: routeValues.length ? routeValues : [3, 1, 1],
          backgroundColor: ["#10b981", "#f59e0b", "#ef4444", "#3b82f6", "#64748b"],
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom" }
        }
      }
    });
  }

  // Chart 2: Alerts Priority Breakdown
  const alertsCanvas = document.getElementById("chart-alerts-priority");
  if (alertsCanvas) {
    const alertLabels = Object.keys(data.alert_priority_breakdown || {});
    const alertValues = Object.values(data.alert_priority_breakdown || {});

    new Chart(alertsCanvas, {
      type: "bar",
      data: {
        labels: alertLabels.length ? alertLabels : ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        datasets: [{
          label: "Alert Count",
          data: alertValues.length ? alertValues : [1, 1, 1, 1],
          backgroundColor: ["#94a3b8", "#38bdf8", "#fbbf24", "#f87171"],
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 } }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }
}

// ==========================================
// 2. USER MANAGEMENT
// ==========================================
async function loadAdminUsers(search = "", role = "ALL", status = "ALL") {
  showLoading();
  try {
    let queryParams = new URLSearchParams();
    if (search) queryParams.append("search", search);
    if (role && role !== "ALL") queryParams.append("role", role);
    if (status && status !== "ALL") queryParams.append("status", status);

    const users = await apiRequest(`/api/admin/users?${queryParams.toString()}`);
    const tbody = document.getElementById("admin-users-table-body");
    const countBadge = document.getElementById("admin-users-count");
    if (countBadge) countBadge.textContent = `${users.length} Users`;

    if (!tbody) return;

    if (!users || users.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">No user accounts found.</td></tr>`;
      return;
    }

    tbody.innerHTML = users.map(u => `
      <tr>
        <td>#${u.id}</td>
        <td><strong>${u.full_name}</strong></td>
        <td>@${u.username}</td>
        <td>${u.email}</td>
        <td>${u.phone || '-'}</td>
        <td><span class="badge ${u.role === 'ADMIN' ? 'bg-danger' : (u.role === 'OPERATOR' ? 'bg-warning text-dark' : 'bg-primary')}">${u.role}</span></td>
        <td>${getStatusBadge(u.status)}</td>
        <td><small class="text-muted">${new Date(u.created_at).toLocaleDateString()}</small></td>
        <td>
          <button class="btn btn-xs btn-outline-primary me-1" onclick="openEditUserModal(${u.id}, '${escapeHtml(u.full_name)}', '${u.email}', '${u.phone || ''}', '${u.role}', '${u.status}')">
            <i class="fa-solid fa-pen-to-square"></i>
          </button>
          <button class="btn btn-xs btn-outline-danger" onclick="deleteAdminUser(${u.id}, '${escapeHtml(u.username)}')">
            <i class="fa-solid fa-trash"></i>
          </button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    showToast("Failed to load users: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

function openEditUserModal(id, fullName, email, phone, role, status) {
  document.getElementById("edit_user_id").value = id;
  document.getElementById("edit_user_name").value = fullName;
  document.getElementById("edit_user_email").value = email;
  document.getElementById("edit_user_phone").value = phone;
  document.getElementById("edit_user_role").value = role;
  document.getElementById("edit_user_status").value = status;

  const modal = new bootstrap.Modal(document.getElementById("editUserModal"));
  modal.show();
}

async function saveAdminUserEdit(e) {
  e.preventDefault();
  const userId = document.getElementById("edit_user_id").value;
  const fullName = document.getElementById("edit_user_name").value.trim();
  const email = document.getElementById("edit_user_email").value.trim();
  const phone = document.getElementById("edit_user_phone").value.trim();
  const role = document.getElementById("edit_user_role").value;
  const status = document.getElementById("edit_user_status").value;

  showLoading();
  try {
    await apiRequest(`/api/admin/users/${userId}`, {
      method: "PUT",
      body: JSON.stringify({ full_name: fullName, email, phone, role, status })
    });
    showToast("User details updated successfully.", "success");
    bootstrap.Modal.getInstance(document.getElementById("editUserModal")).hide();
    await loadAdminUsers();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    hideLoading();
  }
}

async function deleteAdminUser(id, username) {
  if (!confirm(`Are you sure you want to delete user account '${username}'?`)) return;
  showLoading();
  try {
    await apiRequest(`/api/admin/users/${id}`, { method: "DELETE" });
    showToast("User deleted successfully.", "info");
    await loadAdminUsers();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    hideLoading();
  }
}

function setupAdminUserSearch() {
  const searchInput = document.getElementById("adm_user_search");
  const roleSelect = document.getElementById("adm_user_role_filter");
  const statusSelect = document.getElementById("adm_user_status_filter");
  const editForm = document.getElementById("edit-user-form");

  if (editForm) editForm.addEventListener("submit", saveAdminUserEdit);

  const filterHandler = () => {
    loadAdminUsers(
      searchInput ? searchInput.value.trim() : "",
      roleSelect ? roleSelect.value : "ALL",
      statusSelect ? statusSelect.value : "ALL"
    );
  };

  if (searchInput) searchInput.addEventListener("input", debounce(filterHandler, 400));
  if (roleSelect) roleSelect.addEventListener("change", filterHandler);
  if (statusSelect) statusSelect.addEventListener("change", filterHandler);
}

// ==========================================
// 3. ROUTE ADMINISTRATION
// ==========================================
async function loadAdminRoutes() {
  showLoading();
  try {
    const routes = await apiRequest("/api/routes");
    const tbody = document.getElementById("admin-routes-table-body");
    const countBadge = document.getElementById("admin-routes-count");
    if (countBadge) countBadge.textContent = `${routes.length} Routes`;

    if (!tbody) return;

    tbody.innerHTML = routes.map(r => `
      <tr>
        <td><span class="route-number-badge fs-6 py-1 px-2">${r.route_number}</span></td>
        <td><strong>${r.route_name}</strong><br><small class="text-muted">${r.bus_type}</small></td>
        <td>${r.start_point} &rarr; ${r.destination}</td>
        <td>${r.distance} km</td>
        <td>${r.estimated_duration} mins</td>
        <td>₹${r.fare}</td>
        <td>${r.operating_days}</td>
        <td>${getStatusBadge(r.status)}</td>
        <td>
          <button class="btn btn-xs btn-outline-primary me-1" onclick="openEditRouteModal(${r.id})">
            <i class="fa-solid fa-pen-to-square"></i>
          </button>
          <button class="btn btn-xs btn-outline-danger" onclick="deleteAdminRoute(${r.id}, '${r.route_number}')">
            <i class="fa-solid fa-trash"></i>
          </button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    showToast("Failed to load routes: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

function openCreateRouteModal() {
  document.getElementById("routeModalTitle").textContent = "Create New Transit Route";
  document.getElementById("route_form_id").value = "";
  document.getElementById("route_form_number").value = "";
  document.getElementById("route_form_name").value = "";
  document.getElementById("route_form_start").value = "";
  document.getElementById("route_form_dest").value = "";
  document.getElementById("route_form_distance").value = "10.0";
  document.getElementById("route_form_duration").value = "30";
  document.getElementById("route_form_fare").value = "20";
  document.getElementById("route_form_days").value = "Monday - Sunday";
  document.getElementById("route_form_type").value = "Standard Express";
  document.getElementById("route_form_status").value = "ACTIVE";
  document.getElementById("route_form_desc").value = "";

  const modal = new bootstrap.Modal(document.getElementById("routeModal"));
  modal.show();
}

async function openEditRouteModal(routeId) {
  showLoading();
  try {
    const r = await apiRequest(`/api/routes/${routeId}`);
    document.getElementById("routeModalTitle").textContent = `Edit Route ${r.route_number}`;
    document.getElementById("route_form_id").value = r.id;
    document.getElementById("route_form_number").value = r.route_number;
    document.getElementById("route_form_name").value = r.route_name;
    document.getElementById("route_form_start").value = r.start_point;
    document.getElementById("route_form_dest").value = r.destination;
    document.getElementById("route_form_distance").value = r.distance;
    document.getElementById("route_form_duration").value = r.estimated_duration;
    document.getElementById("route_form_fare").value = r.fare;
    document.getElementById("route_form_days").value = r.operating_days;
    document.getElementById("route_form_type").value = r.bus_type;
    document.getElementById("route_form_status").value = r.status;
    document.getElementById("route_form_desc").value = r.description || "";

    const modal = new bootstrap.Modal(document.getElementById("routeModal"));
    modal.show();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    hideLoading();
  }
}

function setupAdminRouteForms() {
  const form = document.getElementById("route-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("route_form_id").value;
    const body = {
      route_number: document.getElementById("route_form_number").value.trim(),
      route_name: document.getElementById("route_form_name").value.trim(),
      start_point: document.getElementById("route_form_start").value.trim(),
      destination: document.getElementById("route_form_dest").value.trim(),
      distance: parseFloat(document.getElementById("route_form_distance").value),
      estimated_duration: parseInt(document.getElementById("route_form_duration").value),
      fare: parseFloat(document.getElementById("route_form_fare").value),
      operating_days: document.getElementById("route_form_days").value.trim(),
      bus_type: document.getElementById("route_form_type").value,
      status: document.getElementById("route_form_status").value,
      description: document.getElementById("route_form_desc").value.trim()
    };

    showLoading();
    try {
      if (id) {
        await apiRequest(`/api/routes/${id}`, { method: "PUT", body: JSON.stringify(body) });
        showToast("Route updated successfully.", "success");
      } else {
        await apiRequest("/api/routes", { method: "POST", body: JSON.stringify(body) });
        showToast("Route created successfully.", "success");
      }
      bootstrap.Modal.getInstance(document.getElementById("routeModal")).hide();
      await loadAdminRoutes();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      hideLoading();
    }
  });
}

async function deleteAdminRoute(routeId, routeNumber) {
  if (!confirm(`Are you sure you want to delete route ${routeNumber}? All connected schedules and stops will be updated.`)) return;
  showLoading();
  try {
    await apiRequest(`/api/routes/${routeId}`, { method: "DELETE" });
    showToast(`Route ${routeNumber} deleted.`, "info");
    await loadAdminRoutes();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    hideLoading();
  }
}

// ==========================================
// 4. STOP ADMINISTRATION
// ==========================================
async function loadAdminStops() {
  showLoading();
  try {
    const stops = await apiRequest("/api/stops");
    const tbody = document.getElementById("admin-stops-table-body");
    const countBadge = document.getElementById("admin-stops-count");
    if (countBadge) countBadge.textContent = `${stops.length} Stops`;

    if (!tbody) return;

    tbody.innerHTML = stops.map(s => `
      <tr>
        <td>#${s.id}</td>
        <td><span class="badge bg-dark">${s.stop_code}</span></td>
        <td><strong>${s.stop_name}</strong></td>
        <td>${s.address || '-'}</td>
        <td>${s.area || '-'}</td>
        <td><small class="text-muted">${s.latitude}, ${s.longitude}</small></td>
        <td>${getStatusBadge(s.status)}</td>
        <td>
          <button class="btn btn-xs btn-outline-primary me-1" onclick="openEditStopModal(${s.id}, '${s.stop_code}', '${escapeHtml(s.stop_name)}', '${escapeHtml(s.address || '')}', '${escapeHtml(s.area || '')}', ${s.latitude}, ${s.longitude}, '${s.status}')">
            <i class="fa-solid fa-pen-to-square"></i>
          </button>
          <button class="btn btn-xs btn-outline-danger" onclick="deleteAdminStop(${s.id}, '${escapeHtml(s.stop_name)}')">
            <i class="fa-solid fa-trash"></i>
          </button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    showToast("Failed to load stops: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

function openCreateStopModal() {
  document.getElementById("stopModalTitle").textContent = "Add New Transport Stop";
  document.getElementById("stop_form_id").value = "";
  document.getElementById("stop_form_code").value = "";
  document.getElementById("stop_form_name").value = "";
  document.getElementById("stop_form_address").value = "";
  document.getElementById("stop_form_area").value = "";
  document.getElementById("stop_form_lat").value = "18.5204";
  document.getElementById("stop_form_lng").value = "73.8567";
  document.getElementById("stop_form_status").value = "ACTIVE";

  const modal = new bootstrap.Modal(document.getElementById("stopModal"));
  modal.show();
}

function openEditStopModal(id, code, name, address, area, lat, lng, status) {
  document.getElementById("stopModalTitle").textContent = `Edit Stop: ${name}`;
  document.getElementById("stop_form_id").value = id;
  document.getElementById("stop_form_code").value = code;
  document.getElementById("stop_form_name").value = name;
  document.getElementById("stop_form_address").value = address;
  document.getElementById("stop_form_area").value = area;
  document.getElementById("stop_form_lat").value = lat;
  document.getElementById("stop_form_lng").value = lng;
  document.getElementById("stop_form_status").value = status;

  const modal = new bootstrap.Modal(document.getElementById("stopModal"));
  modal.show();
}

function setupAdminStopForms() {
  const form = document.getElementById("stop-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("stop_form_id").value;
    const body = {
      stop_code: document.getElementById("stop_form_code").value.trim(),
      stop_name: document.getElementById("stop_form_name").value.trim(),
      address: document.getElementById("stop_form_address").value.trim(),
      area: document.getElementById("stop_form_area").value.trim(),
      latitude: parseFloat(document.getElementById("stop_form_lat").value),
      longitude: parseFloat(document.getElementById("stop_form_lng").value),
      status: document.getElementById("stop_form_status").value
    };

    showLoading();
    try {
      if (id) {
        await apiRequest(`/api/stops/${id}`, { method: "PUT", body: JSON.stringify(body) });
        showToast("Stop updated successfully.", "success");
      } else {
        await apiRequest("/api/stops", { method: "POST", body: JSON.stringify(body) });
        showToast("Stop added successfully.", "success");
      }
      bootstrap.Modal.getInstance(document.getElementById("stopModal")).hide();
      await loadAdminStops();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      hideLoading();
    }
  });
}

async function deleteAdminStop(id, name) {
  if (!confirm(`Delete transit stop '${name}'?`)) return;
  showLoading();
  try {
    await apiRequest(`/api/stops/${id}`, { method: "DELETE" });
    showToast(`Stop '${name}' deleted.`, "info");
    await loadAdminStops();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    hideLoading();
  }
}

// ==========================================
// 5. SCHEDULE ADMINISTRATION
// ==========================================
async function loadAdminSchedules() {
  showLoading();
  try {
    const schedules = await apiRequest("/api/schedules");
    const routes = await apiRequest("/api/routes");
    const tbody = document.getElementById("admin-schedules-table-body");
    const countBadge = document.getElementById("admin-schedules-count");
    if (countBadge) countBadge.textContent = `${schedules.length} Schedules`;

    // Populate route selector in modal
    const routeSelect = document.getElementById("sched_form_route");
    if (routeSelect) {
      routeSelect.innerHTML = `<option value="">Select Route</option>` + routes.map(r => `
        <option value="${r.id}">${r.route_number} - ${r.route_name}</option>
      `).join("");
    }

    if (!tbody) return;

    tbody.innerHTML = schedules.map(s => `
      <tr>
        <td>#${s.id}</td>
        <td><span class="badge bg-dark">${s.route_number}</span></td>
        <td><strong>${s.route_name}</strong></td>
        <td><strong class="text-primary">${s.departure_time}</strong></td>
        <td><strong class="text-success">${s.arrival_time}</strong></td>
        <td>${s.frequency}</td>
        <td>${s.operating_days}</td>
        <td>${getStatusBadge(s.status)}</td>
        <td>
          <button class="btn btn-xs btn-outline-primary me-1" onclick="openEditScheduleModal(${s.id}, ${s.route_id}, '${s.departure_time}', '${s.arrival_time}', '${s.frequency}', '${s.operating_days}', '${s.status}')">
            <i class="fa-solid fa-pen-to-square"></i>
          </button>
          <button class="btn btn-xs btn-outline-danger" onclick="deleteAdminSchedule(${s.id})">
            <i class="fa-solid fa-trash"></i>
          </button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    showToast("Failed to load schedules: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

function openCreateScheduleModal() {
  document.getElementById("scheduleModalTitle").textContent = "Create New Timetable Schedule";
  document.getElementById("sched_form_id").value = "";
  document.getElementById("sched_form_departure").value = "09:00 AM";
  document.getElementById("sched_form_arrival").value = "09:30 AM";
  document.getElementById("sched_form_freq").value = "15 minutes";
  document.getElementById("sched_form_days").value = "Monday - Sunday";
  document.getElementById("sched_form_status").value = "ON TIME";

  const modal = new bootstrap.Modal(document.getElementById("scheduleModal"));
  modal.show();
}

function openEditScheduleModal(id, routeId, dep, arr, freq, days, status) {
  document.getElementById("scheduleModalTitle").textContent = "Edit Schedule";
  document.getElementById("sched_form_id").value = id;
  document.getElementById("sched_form_route").value = routeId;
  document.getElementById("sched_form_departure").value = dep;
  document.getElementById("sched_form_arrival").value = arr;
  document.getElementById("sched_form_freq").value = freq;
  document.getElementById("sched_form_days").value = days;
  document.getElementById("sched_form_status").value = status;

  const modal = new bootstrap.Modal(document.getElementById("scheduleModal"));
  modal.show();
}

function setupAdminScheduleForms() {
  const form = document.getElementById("schedule-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("sched_form_id").value;
    const body = {
      route_id: parseInt(document.getElementById("sched_form_route").value),
      departure_time: document.getElementById("sched_form_departure").value.trim(),
      arrival_time: document.getElementById("sched_form_arrival").value.trim(),
      frequency: document.getElementById("sched_form_freq").value.trim(),
      operating_days: document.getElementById("sched_form_days").value.trim(),
      status: document.getElementById("sched_form_status").value
    };

    showLoading();
    try {
      if (id) {
        await apiRequest(`/api/schedules/${id}`, { method: "PUT", body: JSON.stringify(body) });
        showToast("Schedule updated successfully.", "success");
      } else {
        await apiRequest("/api/schedules", { method: "POST", body: JSON.stringify(body) });
        showToast("Schedule created successfully.", "success");
      }
      bootstrap.Modal.getInstance(document.getElementById("scheduleModal")).hide();
      await loadAdminSchedules();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      hideLoading();
    }
  });
}

async function deleteAdminSchedule(id) {
  if (!confirm("Are you sure you want to delete this schedule?")) return;
  showLoading();
  try {
    await apiRequest(`/api/schedules/${id}`, { method: "DELETE" });
    showToast("Schedule deleted.", "info");
    await loadAdminSchedules();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    hideLoading();
  }
}

// ==========================================
// 6. FARE ADMINISTRATION
// ==========================================
async function loadAdminFares() {
  showLoading();
  try {
    const fares = await apiRequest("/api/fares");
    const routes = await apiRequest("/api/routes");
    const tbody = document.getElementById("admin-fares-table-body");
    const countBadge = document.getElementById("admin-fares-count");
    if (countBadge) countBadge.textContent = `${fares.length} Tariffs`;

    const routeSelect = document.getElementById("fare_form_route");
    if (routeSelect) {
      routeSelect.innerHTML = `<option value="">Select Route</option>` + routes.map(r => `
        <option value="${r.id}">${r.route_number} - ${r.route_name}</option>
      `).join("");
    }

    if (!tbody) return;

    tbody.innerHTML = fares.map(f => `
      <tr>
        <td>#${f.id}</td>
        <td><span class="badge bg-dark">${f.route_number}</span></td>
        <td><strong>${f.route_name}</strong></td>
        <td class="fw-bold text-primary">₹${f.base_fare}</td>
        <td class="text-success">₹${f.student_fare}</td>
        <td class="text-info">₹${f.senior_fare}</td>
        <td>${f.effective_date}</td>
        <td>${getStatusBadge(f.status)}</td>
        <td>
          <button class="btn btn-xs btn-outline-primary me-1" onclick="openEditFareModal(${f.id}, ${f.route_id}, ${f.base_fare}, ${f.student_fare}, ${f.senior_fare}, '${f.effective_date}', '${f.status}')">
            <i class="fa-solid fa-pen-to-square"></i>
          </button>
          <button class="btn btn-xs btn-outline-danger" onclick="deleteAdminFare(${f.id})">
            <i class="fa-solid fa-trash"></i>
          </button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    showToast("Failed to load fares: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

function openCreateFareModal() {
  document.getElementById("fareModalTitle").textContent = "Add New Fare Tariff";
  document.getElementById("fare_form_id").value = "";
  document.getElementById("fare_form_base").value = "20";
  document.getElementById("fare_form_student").value = "10";
  document.getElementById("fare_form_senior").value = "12";
  document.getElementById("fare_form_date").value = "2026-01-01";
  document.getElementById("fare_form_status").value = "ACTIVE";

  const modal = new bootstrap.Modal(document.getElementById("fareModal"));
  modal.show();
}

function openEditFareModal(id, routeId, base, student, senior, date, status) {
  document.getElementById("fareModalTitle").textContent = "Edit Fare Tariff";
  document.getElementById("fare_form_id").value = id;
  document.getElementById("fare_form_route").value = routeId;
  document.getElementById("fare_form_base").value = base;
  document.getElementById("fare_form_student").value = student;
  document.getElementById("fare_form_senior").value = senior;
  document.getElementById("fare_form_date").value = date;
  document.getElementById("fare_form_status").value = status;

  const modal = new bootstrap.Modal(document.getElementById("fareModal"));
  modal.show();
}

function setupAdminFareForms() {
  const form = document.getElementById("fare-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("fare_form_id").value;
    const body = {
      route_id: parseInt(document.getElementById("fare_form_route").value),
      base_fare: parseFloat(document.getElementById("fare_form_base").value),
      student_fare: parseFloat(document.getElementById("fare_form_student").value),
      senior_fare: parseFloat(document.getElementById("fare_form_senior").value),
      effective_date: document.getElementById("fare_form_date").value.trim(),
      status: document.getElementById("fare_form_status").value
    };

    showLoading();
    try {
      if (id) {
        await apiRequest(`/api/fares/${id}`, { method: "PUT", body: JSON.stringify(body) });
        showToast("Fare tariff updated.", "success");
      } else {
        await apiRequest("/api/fares", { method: "POST", body: JSON.stringify(body) });
        showToast("Fare tariff added.", "success");
      }
      bootstrap.Modal.getInstance(document.getElementById("fareModal")).hide();
      await loadAdminFares();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      hideLoading();
    }
  });
}

async function deleteAdminFare(id) {
  if (!confirm("Are you sure you want to delete this fare record?")) return;
  showLoading();
  try {
    await apiRequest(`/api/fares/${id}`, { method: "DELETE" });
    showToast("Fare record deleted.", "info");
    await loadAdminFares();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    hideLoading();
  }
}

// ==========================================
// 7. SERVICE ALERT ADMINISTRATION
// ==========================================
async function loadAdminAlerts() {
  showLoading();
  try {
    const alerts = await apiRequest("/api/alerts");
    const routes = await apiRequest("/api/routes");
    const tbody = document.getElementById("admin-alerts-table-body");
    const countBadge = document.getElementById("admin-alerts-count");
    if (countBadge) countBadge.textContent = `${alerts.length} Alerts`;

    const routeSelect = document.getElementById("alert_form_route");
    if (routeSelect) {
      routeSelect.innerHTML = `<option value="0">All Routes / System-Wide</option>` + routes.map(r => `
        <option value="${r.id}">${r.route_number} - ${r.route_name}</option>
      `).join("");
    }

    if (!tbody) return;

    tbody.innerHTML = alerts.map(a => `
      <tr>
        <td>#${a.id}</td>
        <td>${getPriorityBadge(a.priority)}</td>
        <td><strong>${a.title}</strong><br><small class="text-muted">${a.description}</small></td>
        <td><span class="badge bg-secondary">${a.route_number || 'All Routes'}</span></td>
        <td><small class="text-muted">${a.start_date || 'Ongoing'} ${a.end_date ? 'to ' + a.end_date : ''}</small></td>
        <td>${getStatusBadge(a.status)}</td>
        <td>
          <button class="btn btn-xs btn-outline-primary me-1" onclick="openEditAlertModal(${a.id}, '${escapeHtml(a.title)}', '${escapeHtml(a.description)}', ${a.route_id || 0}, '${a.priority}', '${a.start_date || ''}', '${a.end_date || ''}', '${a.status}')">
            <i class="fa-solid fa-pen-to-square"></i>
          </button>
          <button class="btn btn-xs btn-outline-danger" onclick="deleteAdminAlert(${a.id})">
            <i class="fa-solid fa-trash"></i>
          </button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    showToast("Failed to load alerts: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

function openCreateAlertModal() {
  document.getElementById("alertModalTitle").textContent = "Publish Service Alert";
  document.getElementById("alert_form_id").value = "";
  document.getElementById("alert_form_title").value = "";
  document.getElementById("alert_form_desc").value = "";
  document.getElementById("alert_form_route").value = "0";
  document.getElementById("alert_form_priority").value = "MEDIUM";
  document.getElementById("alert_form_start").value = new Date().toISOString().split('T')[0];
  document.getElementById("alert_form_end").value = "";
  document.getElementById("alert_form_status").value = "ACTIVE";

  const modal = new bootstrap.Modal(document.getElementById("alertModal"));
  modal.show();
}

function openEditAlertModal(id, title, desc, routeId, priority, start, end, status) {
  document.getElementById("alertModalTitle").textContent = "Edit Service Alert";
  document.getElementById("alert_form_id").value = id;
  document.getElementById("alert_form_title").value = title;
  document.getElementById("alert_form_desc").value = desc;
  document.getElementById("alert_form_route").value = routeId;
  document.getElementById("alert_form_priority").value = priority;
  document.getElementById("alert_form_start").value = start;
  document.getElementById("alert_form_end").value = end;
  document.getElementById("alert_form_status").value = status;

  const modal = new bootstrap.Modal(document.getElementById("alertModal"));
  modal.show();
}

function setupAdminAlertForms() {
  const form = document.getElementById("alert-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("alert_form_id").value;
    const routeVal = parseInt(document.getElementById("alert_form_route").value);
    const body = {
      title: document.getElementById("alert_form_title").value.trim(),
      description: document.getElementById("alert_form_desc").value.trim(),
      route_id: routeVal > 0 ? routeVal : null,
      priority: document.getElementById("alert_form_priority").value,
      start_date: document.getElementById("alert_form_start").value || null,
      end_date: document.getElementById("alert_form_end").value || null,
      status: document.getElementById("alert_form_status").value
    };

    showLoading();
    try {
      if (id) {
        await apiRequest(`/api/alerts/${id}`, { method: "PUT", body: JSON.stringify(body) });
        showToast("Alert updated successfully.", "success");
      } else {
        await apiRequest("/api/alerts", { method: "POST", body: JSON.stringify(body) });
        showToast("Service alert broadcasted.", "success");
      }
      bootstrap.Modal.getInstance(document.getElementById("alertModal")).hide();
      await loadAdminAlerts();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      hideLoading();
    }
  });
}

async function deleteAdminAlert(id) {
  if (!confirm("Are you sure you want to delete this alert?")) return;
  showLoading();
  try {
    await apiRequest(`/api/alerts/${id}`, { method: "DELETE" });
    showToast("Alert deleted.", "info");
    await loadAdminAlerts();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    hideLoading();
  }
}

// Escape helper for safe html injection
function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/'/g, "\\'").replace(/"/g, "&quot;");
}
