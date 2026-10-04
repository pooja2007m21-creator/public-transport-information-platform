/**
 * Passenger Dashboard JavaScript
 */

document.addEventListener("DOMContentLoaded", async () => {
  if (!isAuthenticated()) {
    window.location.href = "/login.html";
    return;
  }

  const user = getStoredUser();
  const userNameEl = document.getElementById("dashboard-user-name");
  if (userNameEl && user) {
    userNameEl.textContent = user.full_name;
  }

  await loadDashboardData();
  setupQuickJourneySearch();
});

async function loadDashboardData() {
  showLoading();
  try {
    const stats = await apiRequest("/api/dashboard/user");

    // Counters
    document.getElementById("stat-favorites").textContent = stats.total_favorites;
    document.getElementById("stat-saved-stops").textContent = stats.total_saved_stops;
    document.getElementById("stat-recent-searches").textContent = stats.recent_searches_count;
    document.getElementById("stat-active-alerts").textContent = stats.active_alerts_count;

    // Render Recent Searches
    const searchesContainer = document.getElementById("dashboard-recent-searches");
    if (searchesContainer) {
      if (!stats.recent_searches || stats.recent_searches.length === 0) {
        searchesContainer.innerHTML = `<div class="p-4 text-center text-muted">No recent journey searches yet. Plan a trip above!</div>`;
      } else {
        searchesContainer.innerHTML = stats.recent_searches.map(s => `
          <div class="list-group-item d-flex justify-content-between align-items-center py-3">
            <div>
              <div class="fw-bold"><i class="fa-solid fa-location-dot text-primary me-2"></i> ${s.from_stop} <i class="fa-solid fa-arrow-right-long text-muted mx-2"></i> ${s.to_stop}</div>
              <small class="text-muted"><i class="fa-regular fa-clock me-1"></i> ${s.search_date || 'Today'} ${s.search_time || ''}</small>
            </div>
            <button class="btn btn-sm btn-outline-primary" onclick="reRunSearch('${encodeURIComponent(s.from_stop)}', '${encodeURIComponent(s.to_stop)}')">
              <i class="fa-solid fa-magnifying-glass me-1"></i> Search Again
            </button>
          </div>
        `).join("");
      }
    }

    // Render Favorite Routes
    const favRoutesContainer = document.getElementById("dashboard-fav-routes");
    if (favRoutesContainer) {
      if (!stats.favorite_routes || stats.favorite_routes.length === 0) {
        favRoutesContainer.innerHTML = `<div class="p-4 text-center text-muted">No saved favorite routes yet. <a href="/routes.html">Browse Routes</a></div>`;
      } else {
        favRoutesContainer.innerHTML = stats.favorite_routes.map(r => `
          <div class="list-group-item d-flex justify-content-between align-items-center py-3">
            <div class="d-flex align-items-center gap-3">
              <span class="badge bg-dark fs-6">${r.route_number}</span>
              <div>
                <div class="fw-bold">${r.route_name}</div>
                <small class="text-muted">${r.start_point} &rarr; ${r.destination} | ₹${r.fare}</small>
              </div>
            </div>
            <div class="d-flex gap-2">
              <a href="/route-details.html?id=${r.route_id}" class="btn btn-sm btn-outline-primary">View</a>
              <button class="btn btn-sm btn-outline-danger" onclick="removeFavoriteItem(${r.id})"><i class="fa-solid fa-trash"></i></button>
            </div>
          </div>
        `).join("");
      }
    }

    // Render Saved Stops
    const favStopsContainer = document.getElementById("dashboard-saved-stops");
    if (favStopsContainer) {
      if (!stats.saved_stops || stats.saved_stops.length === 0) {
        favStopsContainer.innerHTML = `<div class="p-4 text-center text-muted">No saved stops yet. <a href="/stops.html">Explore Stops</a></div>`;
      } else {
        favStopsContainer.innerHTML = stats.saved_stops.map(s => `
          <div class="list-group-item d-flex justify-content-between align-items-center py-3">
            <div class="d-flex align-items-center gap-3">
              <div class="feature-icon-wrapper icon-teal mb-0" style="width:38px; height:38px; font-size:1rem;"><i class="fa-solid fa-map-pin"></i></div>
              <div>
                <div class="fw-bold">${s.stop_name}</div>
                <small class="text-muted">Code: ${s.stop_code} | ${s.area || 'City Area'}</small>
              </div>
            </div>
            <div class="d-flex gap-2">
              <a href="/stops.html?id=${s.stop_id}" class="btn btn-sm btn-outline-teal">Schedule</a>
              <button class="btn btn-sm btn-outline-danger" onclick="removeFavoriteItem(${s.id})"><i class="fa-solid fa-trash"></i></button>
            </div>
          </div>
        `).join("");
      }
    }

    // Render Active Alerts
    const alertsContainer = document.getElementById("dashboard-active-alerts");
    if (alertsContainer) {
      if (!stats.active_alerts || stats.active_alerts.length === 0) {
        alertsContainer.innerHTML = `<div class="p-3 text-center text-success"><i class="fa-solid fa-circle-check me-2"></i> All transit services operating normally. No active disruptions.</div>`;
      } else {
        alertsContainer.innerHTML = stats.active_alerts.map(a => `
          <div class="p-3 mb-2 border rounded bg-light d-flex justify-content-between align-items-center">
            <div>
              <div class="d-flex align-items-center gap-2 mb-1">
                ${getPriorityBadge(a.priority)}
                <span class="fw-bold">${a.title}</span>
              </div>
              <small class="text-muted">${a.description}</small>
            </div>
            <span class="badge bg-secondary">${a.route_number || 'All Routes'}</span>
          </div>
        `).join("");
      }
    }

  } catch (err) {
    showToast("Failed to load dashboard data: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

function setupQuickJourneySearch() {
  const form = document.getElementById("dashboard-search-form");
  if (!form) return;

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const from = document.getElementById("dash_from").value.trim();
    const to = document.getElementById("dash_to").value.trim();
    if (!from || !to) {
      showToast("Please enter both starting point and destination.", "warning");
      return;
    }
    window.location.href = `/routes.html?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`;
  });
}

function reRunSearch(from, to) {
  window.location.href = `/routes.html?from=${from}&to=${to}`;
}

async function removeFavoriteItem(favId) {
  if (!confirm("Remove this item from your favorites?")) return;
  try {
    await apiRequest(`/api/favorites/${favId}`, { method: "DELETE" });
    showToast("Removed from favorites.", "info");
    await loadDashboardData();
  } catch (err) {
    showToast("Failed to remove: " + err.message, "error");
  }
}

async function clearSearchHistory() {
  if (!confirm("Are you sure you want to clear your journey search history?")) return;
  try {
    await apiRequest("/api/search/history", { method: "DELETE" });
    showToast("Search history cleared.", "success");
    await loadDashboardData();
  } catch (err) {
    showToast("Failed to clear search history: " + err.message, "error");
  }
}
