/**
 * Service Status & Alerts JavaScript
 */

document.addEventListener("DOMContentLoaded", async () => {
  await loadServiceStatusOverview();
  await loadAlertsList();
  setupAlertFilters();
});

async function loadServiceStatusOverview() {
  try {
    const routes = await apiRequest("/api/routes");
    const container = document.getElementById("service-status-routes-grid");
    if (!container) return;

    if (!routes || routes.length === 0) {
      container.innerHTML = `<div class="col-12 text-center text-muted py-4">No active routes found.</div>`;
      return;
    }

    container.innerHTML = routes.map(r => `
      <div class="col-md-6 col-lg-4 mb-3">
        <div class="card card-custom p-3 h-100 d-flex flex-column justify-content-between">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="route-number-badge">${r.route_number}</span>
            ${getStatusBadge(r.status)}
          </div>
          <div class="fw-bold mb-1">${r.route_name}</div>
          <small class="text-muted mb-2">${r.start_point} &rarr; ${r.destination}</small>
          <div class="pt-2 border-top d-flex justify-content-between align-items-center">
            <small class="text-muted"><i class="fa-solid fa-bus me-1"></i> ${r.bus_type}</small>
            <a href="/route-details.html?id=${r.id}" class="btn btn-xs btn-outline-primary py-1 px-2">Details</a>
          </div>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Failed to load service status overview:", err);
  }
}

async function loadAlertsList(filters = {}) {
  showLoading();
  try {
    let queryParams = new URLSearchParams();
    if (filters.priority && filters.priority !== "ALL") queryParams.append("priority", filters.priority);
    if (filters.status && filters.status !== "ALL") queryParams.append("status", filters.status);
    if (filters.search) queryParams.append("search", filters.search);

    const alerts = await apiRequest(`/api/alerts?${queryParams.toString()}`);
    renderAlertsFeed(alerts);
  } catch (err) {
    showToast("Failed to load service alerts: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

function renderAlertsFeed(alerts) {
  const container = document.getElementById("alerts-feed-container");
  const countBadge = document.getElementById("alerts-count-badge");
  if (countBadge) countBadge.textContent = `${alerts.length} Active Alerts`;

  if (!container) return;

  if (!alerts || alerts.length === 0) {
    container.innerHTML = `
      <div class="card card-custom p-5 text-center">
        <i class="fa-solid fa-circle-check text-success display-4 mb-3"></i>
        <h4>Network Normal</h4>
        <p class="text-muted">All transport corridors and fleets are operating on normal schedule.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = alerts.map(a => `
    <div class="card card-custom p-4 mb-3 border-start border-4 ${getBorderColorClass(a.priority)}">
      <div class="d-flex justify-content-between align-items-start mb-2">
        <div class="d-flex align-items-center gap-2">
          ${getPriorityBadge(a.priority)}
          <span class="badge bg-dark">${a.route_number || 'All Routes'}</span>
          <h5 class="fw-bold mb-0">${a.title}</h5>
        </div>
        <span class="badge bg-light text-dark border">${a.status}</span>
      </div>
      <p class="text-secondary mb-3">${a.description}</p>
      <div class="d-flex justify-content-between align-items-center small text-muted pt-2 border-top">
        <span><i class="fa-regular fa-calendar me-1"></i> Effective: ${a.start_date || 'Ongoing'} ${a.end_date ? `to ${a.end_date}` : ''}</span>
        <span><i class="fa-solid fa-circle-info me-1"></i> Reported by Transit Control</span>
      </div>
    </div>
  `).join("");
}

function getBorderColorClass(priority) {
  switch ((priority || "").toUpperCase()) {
    case "CRITICAL": return "border-danger";
    case "HIGH": return "border-warning";
    case "MEDIUM": return "border-info";
    default: return "border-primary";
  }
}

function setupAlertFilters() {
  const prioritySelect = document.getElementById("alert_filter_priority");
  const statusSelect = document.getElementById("alert_filter_status");
  const searchInput = document.getElementById("alert_search_input");

  const filterHandler = () => {
    loadAlertsList({
      priority: prioritySelect ? prioritySelect.value : null,
      status: statusSelect ? statusSelect.value : null,
      search: searchInput ? searchInput.value.trim() : null
    });
  };

  if (prioritySelect) prioritySelect.addEventListener("change", filterHandler);
  if (statusSelect) statusSelect.addEventListener("change", filterHandler);
  if (searchInput) searchInput.addEventListener("input", debounce(filterHandler, 400));
}
