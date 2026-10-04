/**
 * Routes & Journey Planner JavaScript with Leaflet.js Map Integration
 */

let globalMap = null;
let currentRouteId = null;

document.addEventListener("DOMContentLoaded", async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const routeIdParam = urlParams.get("id");
  const fromParam = urlParams.get("from");
  const toParam = urlParams.get("to");

  // If on Route Details page
  if (document.getElementById("route-detail-container") && routeIdParam) {
    currentRouteId = parseInt(routeIdParam);
    await loadRouteDetails(currentRouteId);
    return;
  }

  // If on Routes Listing / Journey Search page
  if (document.getElementById("routes-list-container")) {
    if (fromParam && toParam) {
      // Pre-fill journey search inputs
      const fromInput = document.getElementById("search_from");
      const toInput = document.getElementById("search_to");
      if (fromInput) fromInput.value = fromParam;
      if (toInput) toInput.value = toParam;
      await executeJourneySearch(fromParam, toParam);
    } else {
      await loadRoutesCatalog();
    }
    setupRouteFiltersAndSearch();
  }
});

// --- Catalog & Filter Search ---
async function loadRoutesCatalog(filters = {}) {
  showLoading();
  try {
    let queryParams = new URLSearchParams();
    if (filters.search) queryParams.append("search", filters.search);
    if (filters.status && filters.status !== "ALL") queryParams.append("status", filters.status);
    if (filters.bus_type && filters.bus_type !== "ALL") queryParams.append("bus_type", filters.bus_type);

    const routes = await apiRequest(`/api/routes?${queryParams.toString()}`);
    renderRoutesList(routes);
  } catch (err) {
    showToast("Failed to load routes: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

function renderRoutesList(routes) {
  const container = document.getElementById("routes-list-container");
  const countEl = document.getElementById("routes-count-badge");
  if (countEl) countEl.textContent = `${routes.length} Available`;

  if (!container) return;

  if (!routes || routes.length === 0) {
    container.innerHTML = `
      <div class="col-12 text-center py-5">
        <div class="feature-icon-wrapper icon-amber mx-auto mb-3"><i class="fa-solid fa-bus-simple"></i></div>
        <h5 class="fw-bold">No Routes Found</h5>
        <p class="text-muted">No transport routes matched your search criteria. Try a different query.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = routes.map(r => `
    <div class="col-md-6 col-lg-4 mb-4">
      <div class="route-card h-100 d-flex flex-direction-column justify-content-between">
        <div>
          <div class="d-flex justify-content-between align-items-center mb-3">
            <span class="route-number-badge">${r.route_number}</span>
            ${getStatusBadge(r.status)}
          </div>
          <h5 class="fw-bold mb-2">${r.route_name}</h5>
          
          <div class="route-stops-path mb-3">
            <span>${r.start_point}</span>
            <i class="fa-solid fa-arrow-right-long text-primary"></i>
            <span>${r.destination}</span>
          </div>

          <div class="d-flex flex-wrap gap-2 mb-3">
            <span class="route-meta-pill"><i class="fa-solid fa-route"></i> ${r.distance || 10} km</span>
            <span class="route-meta-pill"><i class="fa-regular fa-clock"></i> ~${r.estimated_duration} mins</span>
            <span class="route-meta-pill"><i class="fa-solid fa-indian-rupee-sign"></i> ₹${r.fare}</span>
            <span class="route-meta-pill"><i class="fa-solid fa-bus"></i> ${r.bus_type}</span>
          </div>
        </div>

        <div class="pt-3 border-top d-flex justify-content-between align-items-center">
          <a href="/route-details.html?id=${r.id}" class="btn btn-sm btn-primary-custom">
            <i class="fa-solid fa-map-location-dot me-1"></i> View Route & Map
          </a>
          <button class="btn btn-sm btn-outline-secondary" onclick="toggleSaveRoute(${r.id}, event)" title="Save to Favorites">
            <i class="fa-regular fa-heart"></i>
          </button>
        </div>
      </div>
    </div>
  `).join("");
}

// --- Journey Search (From / To) ---
async function executeJourneySearch(from, to, date = null, time = null) {
  showLoading();
  try {
    const results = await apiRequest("/api/search/routes", {
      method: "POST",
      body: JSON.stringify({
        from_stop: from,
        to_stop: to,
        travel_date: date,
        travel_time: time
      })
    });

    const resultsContainer = document.getElementById("journey-results-container");
    const catalogSection = document.getElementById("routes-catalog-section");

    if (resultsContainer) {
      resultsContainer.classList.remove("d-none");
      if (catalogSection) catalogSection.classList.add("d-none");

      const countEl = document.getElementById("journey-match-count");
      if (countEl) countEl.textContent = `${results.length} Matches Found`;

      if (results.length === 0) {
        resultsContainer.innerHTML = `
          <div class="card card-custom p-5 text-center">
            <i class="fa-solid fa-triangle-exclamation text-warning display-4 mb-3"></i>
            <h4>No Direct Routes Found</h4>
            <p class="text-muted">We couldn't locate a direct route from "<strong>${from}</strong>" to "<strong>${to}</strong>". Check spelling or explore individual stops.</p>
            <button class="btn btn-outline-primary mx-auto" onclick="resetJourneySearch()">View All Available Routes</button>
          </div>
        `;
      } else {
        resultsContainer.innerHTML = `
          <div class="d-flex justify-content-between align-items-center mb-4">
            <h4 class="fw-bold mb-0">Journey Options: ${from} &rarr; ${to}</h4>
            <button class="btn btn-sm btn-outline-secondary" onclick="resetJourneySearch()"><i class="fa-solid fa-rotate-left me-1"></i> Reset Search</button>
          </div>
          <div class="row">
            ${results.map(r => `
              <div class="col-lg-6 mb-4">
                <div class="journey-step-card shadow-sm h-100">
                  <div class="d-flex justify-content-between align-items-start mb-3">
                    <div>
                      <span class="route-number-badge me-2">${r.route_number}</span>
                      <span class="badge bg-light text-dark border">${r.bus_type}</span>
                    </div>
                    ${getStatusBadge(r.status)}
                  </div>

                  <h5 class="fw-bold mb-3">${r.route_name}</h5>

                  <div class="row g-2 mb-3 bg-light p-3 rounded">
                    <div class="col-6">
                      <small class="text-muted d-block">Boarding (${r.from_stop})</small>
                      <strong class="text-primary fs-5">${r.departure_time}</strong>
                    </div>
                    <div class="col-6">
                      <small class="text-muted d-block">Destination (${r.to_stop})</small>
                      <strong class="text-success fs-5">${r.arrival_time}</strong>
                    </div>
                  </div>

                  <div class="d-flex flex-wrap gap-2 mb-3">
                    <span class="route-meta-pill"><i class="fa-regular fa-clock"></i> ${r.duration_min} mins</span>
                    <span class="route-meta-pill"><i class="fa-solid fa-indian-rupee-sign"></i> ₹${r.fare} Fare</span>
                    <span class="route-meta-pill"><i class="fa-solid fa-location-dot"></i> ${r.stops_count} intermediate stops</span>
                  </div>

                  <div class="d-flex justify-content-between align-items-center pt-2 border-top">
                    <a href="/route-details.html?id=${r.route_id}" class="btn btn-sm btn-primary-custom">
                      <i class="fa-solid fa-circle-info me-1"></i> View Route & Map
                    </a>
                    <button class="btn btn-sm btn-outline-primary" onclick="toggleSaveRoute(${r.route_id}, event)">
                      <i class="fa-solid fa-heart me-1"></i> Save Route
                    </button>
                  </div>
                </div>
              </div>
            `).join("")}
          </div>
        `;
      }
    }
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    hideLoading();
  }
}

function resetJourneySearch() {
  const resultsContainer = document.getElementById("journey-results-container");
  const catalogSection = document.getElementById("routes-catalog-section");
  if (resultsContainer) resultsContainer.classList.add("d-none");
  if (catalogSection) catalogSection.classList.remove("d-none");
  loadRoutesCatalog();
}

function setupRouteFiltersAndSearch() {
  const journeyForm = document.getElementById("journey-planner-form");
  if (journeyForm) {
    journeyForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const from = document.getElementById("search_from").value.trim();
      const to = document.getElementById("search_to").value.trim();
      const date = document.getElementById("search_date") ? document.getElementById("search_date").value : null;
      const time = document.getElementById("search_time") ? document.getElementById("search_time").value : null;

      if (!from || !to) {
        showToast("Please enter both starting point and destination.", "warning");
        return;
      }
      await executeJourneySearch(from, to, date, time);
    });
  }

  // Live filter inputs for catalog
  const searchInput = document.getElementById("catalog_search");
  const statusSelect = document.getElementById("filter_status");
  const typeSelect = document.getElementById("filter_bus_type");

  const triggerFilter = () => {
    loadRoutesCatalog({
      search: searchInput ? searchInput.value.trim() : "",
      status: statusSelect ? statusSelect.value : "ALL",
      bus_type: typeSelect ? typeSelect.value : "ALL"
    });
  };

  if (searchInput) searchInput.addEventListener("input", debounce(triggerFilter, 400));
  if (statusSelect) statusSelect.addEventListener("change", triggerFilter);
  if (typeSelect) typeSelect.addEventListener("change", triggerFilter);
}

// --- Route Details & Map ---
async function loadRouteDetails(routeId) {
  showLoading();
  try {
    const route = await apiRequest(`/api/routes/${routeId}`);

    // Populate header info
    document.getElementById("rd-number").textContent = route.route_number;
    document.getElementById("rd-name").textContent = route.route_name;
    document.getElementById("rd-status").innerHTML = getStatusBadge(route.status);
    document.getElementById("rd-start").textContent = route.start_point;
    document.getElementById("rd-dest").textContent = route.destination;
    document.getElementById("rd-type").textContent = route.bus_type;
    document.getElementById("rd-distance").textContent = `${route.distance} km`;
    document.getElementById("rd-duration").textContent = `${route.estimated_duration} mins`;
    document.getElementById("rd-fare").textContent = `₹${route.fare}`;
    document.getElementById("rd-operating-days").textContent = route.operating_days;
    document.getElementById("rd-description").textContent = route.description || "Regular scheduled public transport route.";

    // Render Timeline Stops
    const stopsList = document.getElementById("rd-stops-timeline");
    if (stopsList && route.stops) {
      stopsList.innerHTML = route.stops.map((s, idx) => `
        <li class="timeline-stop-item ${idx === 0 ? 'start' : (idx === route.stops.length - 1 ? 'end' : '')}">
          <div class="fw-bold fs-6">${s.stop_name}</div>
          <small class="text-muted">Stop Code: ${s.stop_code} | Area: ${s.area || 'Downtown'}</small>
        </li>
      `).join("");
    }

    // Render Schedules Table
    const schedTable = document.getElementById("rd-schedules-body");
    if (schedTable && route.schedules) {
      schedTable.innerHTML = route.schedules.map(sc => `
        <tr>
          <td><i class="fa-solid fa-arrow-right text-primary me-2"></i> ${sc.departure_time}</td>
          <td>${sc.arrival_time}</td>
          <td>${sc.frequency}</td>
          <td>${getStatusBadge(sc.status)}</td>
        </tr>
      `).join("");
    }

    // Render Alerts
    const alertsBox = document.getElementById("rd-alerts-box");
    if (alertsBox) {
      if (!route.alerts || route.alerts.length === 0) {
        alertsBox.innerHTML = `<div class="text-success small"><i class="fa-solid fa-circle-check me-1"></i> No active alerts for this route. Operating on schedule.</div>`;
      } else {
        alertsBox.innerHTML = route.alerts.map(al => `
          <div class="alert alert-warning py-2 px-3 small mb-2 d-flex align-items-center gap-2">
            ${getPriorityBadge(al.priority)}
            <span><strong>${al.title}:</strong> ${al.description}</span>
          </div>
        `).join("");
      }
    }

    // Initialize Leaflet Map
    initLeafletRouteMap(route.stops);

  } catch (err) {
    showToast("Error loading route details: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

function initLeafletRouteMap(stops) {
  const mapElement = document.getElementById("route-leaflet-map");
  if (!mapElement || typeof L === "undefined") return;

  if (globalMap) {
    globalMap.remove();
  }

  if (!stops || stops.length === 0) {
    globalMap = L.map("route-leaflet-map").setView([18.5204, 73.8567], 13);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors"
    }).addTo(globalMap);
    return;
  }

  const coordinates = stops.map(s => [s.latitude, s.longitude]);
  globalMap = L.map("route-leaflet-map").setView(coordinates[0], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(globalMap);

  // Add Polyline connecting stops
  const polyline = L.polyline(coordinates, {
    color: "#2563eb",
    weight: 5,
    opacity: 0.8,
    smoothFactor: 1
  }).addTo(globalMap);

  // Add Stop Markers
  stops.forEach((s, idx) => {
    const isStart = idx === 0;
    const isEnd = idx === stops.length - 1;
    const markerColor = isStart ? "#10b981" : (isEnd ? "#ef4444" : "#2563eb");

    const marker = L.circleMarker([s.latitude, s.longitude], {
      radius: isStart || isEnd ? 9 : 7,
      fillColor: markerColor,
      color: "#ffffff",
      weight: 2,
      opacity: 1,
      fillOpacity: 0.95
    }).addTo(globalMap);

    marker.bindPopup(`
      <div class="p-1">
        <strong class="d-block">${s.stop_name}</strong>
        <small class="text-muted">Code: ${s.stop_code}</small><br>
        <small class="text-muted">Sequence: Stop #${s.stop_order}</small>
      </div>
    `);
  });

  // Fit bounds to show all stops
  globalMap.fitBounds(polyline.getBounds(), { padding: [40, 40] });
}

// --- Toggle Save Route ---
async function toggleSaveRoute(routeId, event) {
  if (event) event.stopPropagation();
  if (!isAuthenticated()) {
    showToast("Please login to save routes to your favorites.", "info");
    setTimeout(() => window.location.href = "/login.html", 1000);
    return;
  }

  try {
    const res = await apiRequest("/api/favorites", {
      method: "POST",
      body: JSON.stringify({ route_id: routeId, favorite_type: "ROUTE" })
    });
    showToast(res.message || "Route saved to your favorites!", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Helper: Debounce function
function debounce(func, delay) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => func.apply(this, args), delay);
  };
}
