/**
 * Transport Schedules JavaScript
 */

let allRoutesForSelect = [];

document.addEventListener("DOMContentLoaded", async () => {
  await loadRouteOptions();
  await loadSchedules();
  setupScheduleFilters();
});

async function loadRouteOptions() {
  try {
    const routes = await apiRequest("/api/routes");
    allRoutesForSelect = routes;
    const select = document.getElementById("schedule_route_select");
    if (select) {
      routes.forEach(r => {
        const opt = document.createElement("option");
        opt.value = r.id;
        opt.textContent = `${r.route_number} - ${r.route_name}`;
        select.appendChild(opt);
      });
    }
  } catch (err) {
    console.error("Failed to load routes for filter:", err);
  }
}

async function loadSchedules(filters = {}) {
  showLoading();
  try {
    let queryParams = new URLSearchParams();
    if (filters.route_id) queryParams.append("route_id", filters.route_id);
    if (filters.search) queryParams.append("search", filters.search);

    const schedules = await apiRequest(`/api/schedules?${queryParams.toString()}`);
    renderSchedulesTable(schedules);
  } catch (err) {
    showToast("Failed to load schedules: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

function renderSchedulesTable(schedules) {
  const tbody = document.getElementById("schedules-table-body");
  const countBadge = document.getElementById("schedule-count-badge");
  if (countBadge) countBadge.textContent = `${schedules.length} Timetables`;

  if (!tbody) return;

  if (!schedules || schedules.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-5 text-muted"><i class="fa-regular fa-clock display-6 mb-2 d-block"></i> No schedule entries found matching your query.</td></tr>`;
    return;
  }

  tbody.innerHTML = schedules.map(s => `
    <tr>
      <td>
        <span class="badge bg-dark fs-6">${s.route_number}</span>
      </td>
      <td>
        <div class="fw-bold">${s.route_name}</div>
        <small class="text-muted">Terminal: ${s.stop_name || 'Central Stand'}</small>
      </td>
      <td>
        <strong class="text-primary"><i class="fa-regular fa-clock me-1"></i> ${s.departure_time}</strong>
      </td>
      <td>
        <strong class="text-success">${s.arrival_time}</strong>
      </td>
      <td>
        <span class="badge bg-light text-dark border">${s.frequency}</span>
      </td>
      <td>
        <small class="text-muted">${s.operating_days}</small>
      </td>
      <td>
        ${getStatusBadge(s.status)}
      </td>
    </tr>
  `).join("");
}

function setupScheduleFilters() {
  const routeSelect = document.getElementById("schedule_route_select");
  const searchInput = document.getElementById("schedule_search_input");

  const filterHandler = () => {
    loadSchedules({
      route_id: routeSelect ? routeSelect.value : null,
      search: searchInput ? searchInput.value.trim() : null
    });
  };

  if (routeSelect) routeSelect.addEventListener("change", filterHandler);
  if (searchInput) searchInput.addEventListener("input", debounce(filterHandler, 400));
}
