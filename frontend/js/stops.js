/**
 * Bus Stops JavaScript & Map Explorer
 */

let stopsMap = null;
let allStopsData = [];

document.addEventListener("DOMContentLoaded", async () => {
  await loadStops();
  setupStopSearch();
});

async function loadStops(search = "") {
  showLoading();
  try {
    const stops = await apiRequest(`/api/stops${search ? `?search=${encodeURIComponent(search)}` : ''}`);
    allStopsData = stops;
    renderStopsList(stops);
    initStopsMap(stops);
  } catch (err) {
    showToast("Failed to load transport stops: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

function renderStopsList(stops) {
  const container = document.getElementById("stops-list-container");
  const countBadge = document.getElementById("stops-count-badge");
  if (countBadge) countBadge.textContent = `${stops.length} Stops`;

  if (!container) return;

  if (!stops || stops.length === 0) {
    container.innerHTML = `
      <div class="col-12 text-center py-5">
        <i class="fa-solid fa-map-location-dot text-muted display-4 mb-3"></i>
        <h5>No Stops Found</h5>
        <p class="text-muted">No transit stops matched your search.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = stops.map(s => `
    <div class="col-md-6 mb-4">
      <div class="card card-custom card-lift h-100 p-3">
        <div class="d-flex justify-content-between align-items-start mb-2">
          <div class="d-flex align-items-center gap-2">
            <div class="feature-icon-wrapper icon-teal mb-0" style="width: 42px; height: 42px; font-size: 1.1rem;">
              <i class="fa-solid fa-bus-stop"></i>
            </div>
            <div>
              <h5 class="fw-bold mb-0">${s.stop_name}</h5>
              <span class="badge bg-light text-dark border">Code: ${s.stop_code}</span>
            </div>
          </div>
          ${getStatusBadge(s.status)}
        </div>

        <p class="text-muted small mb-3">
          <i class="fa-solid fa-location-dot text-danger me-1"></i> ${s.address || s.area || 'Metro Area'}
        </p>

        <div class="d-flex justify-content-between align-items-center mt-auto pt-2 border-top">
          <button class="btn btn-sm btn-outline-primary" onclick="viewStopDetailsModal(${s.id})">
            <i class="fa-solid fa-clock me-1"></i> Upcoming Buses
          </button>
          <button class="btn btn-sm btn-outline-danger" onclick="saveStopFavorite(${s.id})" title="Save Stop">
            <i class="fa-regular fa-heart"></i>
          </button>
        </div>
      </div>
    </div>
  `).join("");
}

function initStopsMap(stops) {
  const mapEl = document.getElementById("all-stops-map");
  if (!mapEl || typeof L === "undefined") return;

  if (stopsMap) stopsMap.remove();

  if (!stops || stops.length === 0) {
    stopsMap = L.map("all-stops-map").setView([18.5204, 73.8567], 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(stopsMap);
    return;
  }

  stopsMap = L.map("all-stops-map").setView([stops[0].latitude, stops[0].longitude], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(stopsMap);

  const markerGroup = L.featureGroup();

  stops.forEach(s => {
    const marker = L.circleMarker([s.latitude, s.longitude], {
      radius: 8,
      fillColor: "#0f766e",
      color: "#ffffff",
      weight: 2,
      opacity: 1,
      fillOpacity: 0.9
    }).addTo(markerGroup);

    marker.bindPopup(`
      <div class="p-2">
        <strong class="fs-6 text-primary">${s.stop_name}</strong>
        <div class="small text-muted mb-1">Code: ${s.stop_code}</div>
        <div class="small mb-2">${s.area || s.address || ''}</div>
        <button class="btn btn-xs btn-primary w-100 py-1" onclick="viewStopDetailsModal(${s.id})">
          View Buses
        </button>
      </div>
    `);
  });

  markerGroup.addTo(stopsMap);
  stopsMap.fitBounds(markerGroup.getBounds(), { padding: [30, 30] });
}

async function viewStopDetailsModal(stopId) {
  showLoading();
  try {
    const detail = await apiRequest(`/api/stops/${stopId}`);
    
    document.getElementById("modal-stop-name").textContent = detail.stop_name;
    document.getElementById("modal-stop-code").textContent = detail.stop_code;
    document.getElementById("modal-stop-area").textContent = detail.area || detail.address || "Metro Area";

    // Passing routes
    const routesBox = document.getElementById("modal-stop-routes");
    if (routesBox) {
      if (!detail.passing_routes || detail.passing_routes.length === 0) {
        routesBox.innerHTML = `<span class="text-muted small">No scheduled routes passing.</span>`;
      } else {
        routesBox.innerHTML = detail.passing_routes.map(r => `
          <a href="/route-details.html?id=${r.route_id}" class="badge bg-primary text-white text-decoration-none p-2 fs-6">
            ${r.route_number} (${r.start_point} &rarr; ${r.destination})
          </a>
        `).join(" ");
      }
    }

    // Upcoming buses
    const busesBox = document.getElementById("modal-stop-upcoming-buses");
    if (busesBox) {
      if (!detail.upcoming_buses || detail.upcoming_buses.length === 0) {
        busesBox.innerHTML = `<tr><td colspan="4" class="text-center text-muted">No upcoming bus arrivals found for this stop.</td></tr>`;
      } else {
        busesBox.innerHTML = detail.upcoming_buses.map(b => `
          <tr>
            <td><strong class="text-primary">${b.route_number}</strong></td>
            <td>${b.departure_time}</td>
            <td>${b.frequency}</td>
            <td>${getStatusBadge(b.status)}</td>
          </tr>
        `).join("");
      }
    }

    const modal = new bootstrap.Modal(document.getElementById("stopDetailModal"));
    modal.show();
  } catch (err) {
    showToast("Error loading stop details: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

async function saveStopFavorite(stopId) {
  if (!isAuthenticated()) {
    showToast("Please login to save stops to your profile.", "info");
    setTimeout(() => window.location.href = "/login.html", 1000);
    return;
  }
  try {
    const res = await apiRequest("/api/favorites", {
      method: "POST",
      body: JSON.stringify({ stop_id: stopId, favorite_type: "STOP" })
    });
    showToast(res.message || "Stop saved to favorites!", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

function setupStopSearch() {
  const searchInput = document.getElementById("stops_search_input");
  if (!searchInput) return;

  searchInput.addEventListener("input", debounce(() => {
    loadStops(searchInput.value.trim());
  }, 400));
}
