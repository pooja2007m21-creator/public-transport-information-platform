/**
 * Transport Operator JavaScript
 */

function checkOperatorAccess() {
  const user = getStoredUser();
  if (!user || (user.role !== "OPERATOR" && user.role !== "ADMIN")) {
    window.location.href = "/admin/login.html";
    return false;
  }
  const opNameEl = document.getElementById("operator-user-display");
  if (opNameEl) opNameEl.textContent = `${user.full_name} (Transit Operator)`;
  return true;
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!checkOperatorAccess()) return;
  await loadOperatorRoutes();
  setupOperatorForms();
});

async function loadOperatorRoutes() {
  showLoading();
  try {
    const routes = await apiRequest("/api/operator/routes");
    const tbody = document.getElementById("operator-routes-table-body");
    const countBadge = document.getElementById("operator-routes-count");
    if (countBadge) countBadge.textContent = `${routes.length} Active Corridors`;

    // Populate route select in quick updater
    const select = document.getElementById("op_route_select");
    if (select) {
      select.innerHTML = `<option value="">Choose Corridor / Route</option>` + routes.map(r => `
        <option value="${r.id}">${r.route_number} - ${r.route_name}</option>
      `).join("");
    }

    if (!tbody) return;

    tbody.innerHTML = routes.map(r => `
      <tr>
        <td><span class="route-number-badge fs-6 py-1 px-2">${r.route_number}</span></td>
        <td><strong>${r.route_name}</strong><br><small class="text-muted">${r.bus_type}</small></td>
        <td>${r.start_point} &rarr; ${r.destination}</td>
        <td>${getStatusBadge(r.status)}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary" onclick="quickUpdateRouteStatus(${r.id}, '${r.route_number}', '${r.status}')">
            <i class="fa-solid fa-pen me-1"></i> Update Status
          </button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    showToast("Failed to load operator routes: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

function quickUpdateRouteStatus(routeId, routeNumber, currentStatus) {
  const select = document.getElementById("op_route_select");
  const statusSelect = document.getElementById("op_status_select");
  if (select) select.value = routeId;
  if (statusSelect) statusSelect.value = currentStatus;

  // Scroll to status form
  const formCard = document.getElementById("operator-status-form-card");
  if (formCard) formCard.scrollIntoView({ behavior: "smooth" });
}

function setupOperatorForms() {
  const form = document.getElementById("operator-status-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const routeId = parseInt(document.getElementById("op_route_select").value);
    const status = document.getElementById("op_status_select").value;
    const alertTitle = document.getElementById("op_alert_title").value.trim();
    const alertDesc = document.getElementById("op_alert_desc").value.trim();
    const priority = document.getElementById("op_alert_priority").value;

    if (!routeId) {
      showToast("Please select a route to update.", "warning");
      return;
    }

    showLoading();
    try {
      const res = await apiRequest("/api/operator/update-status", {
        method: "POST",
        body: JSON.stringify({
          route_id: routeId,
          status,
          alert_title: alertTitle || null,
          alert_description: alertDesc || null,
          priority
        })
      });

      showToast(res.message || "Transit status updated and broadcasted!", "success");
      form.reset();
      await loadOperatorRoutes();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      hideLoading();
    }
  });
}
