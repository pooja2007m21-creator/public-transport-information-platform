/**
 * Public Transport Information Platform - API Client & Global Helpers
 */

const API_CONFIG = {
  // Automatically detect if running directly on FastAPI port (8000) or Live Server (5500/etc.)
  BASE_URL: (window.location.port === "8000") 
    ? "" 
    : (localStorage.getItem("API_BASE_URL") || "http://127.0.0.1:8000")
};

// --- Storage Keys ---
const TOKEN_KEY = "pts_token";
const USER_KEY = "pts_user";

// --- Auth Token Helpers ---
function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setAuthToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

function getStoredUser() {
  const u = localStorage.getItem(USER_KEY);
  try {
    return u ? JSON.parse(u) : null;
  } catch (e) {
    return null;
  }
}

function setStoredUser(user) {
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(USER_KEY);
  }
}

function logoutUser(redirectUrl = "/login.html") {
  setAuthToken(null);
  setStoredUser(null);
  showToast("Logged out successfully.", "info");
  setTimeout(() => {
    window.location.href = redirectUrl;
  }, 500);
}

function isAuthenticated() {
  return !!getAuthToken();
}

// --- Unified API Fetch Wrapper ---
async function apiRequest(endpoint, options = {}) {
  const url = `${API_CONFIG.BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  const token = getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const fetchOptions = {
    ...options,
    headers
  };

  try {
    const response = await fetch(url, fetchOptions);
    
    // Check if unauthorized
    if (response.status === 401) {
      // If unauthorized on protected endpoint, clear local session
      if (token && !endpoint.includes("/api/auth/login")) {
        setAuthToken(null);
        setStoredUser(null);
        showToast("Session expired. Please login again.", "warning");
        setTimeout(() => {
          if (!window.location.pathname.includes("login.html")) {
            window.location.href = "/login.html";
          }
        }, 1200);
      }
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMsg = (data && (data.detail || data.message)) || `Error: ${response.status} ${response.statusText}`;
      throw new Error(errorMsg);
    }

    return data;
  } catch (err) {
    console.error(`API Request Error [${endpoint}]:`, err);
    throw err;
  }
}

// --- Toast Notifications ---
function showToast(message, type = "info") {
  let container = document.getElementById("toast-container-global");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container-global";
    container.className = "toast-container position-fixed bottom-0 end-0 p-3";
    container.style.zIndex = "10000";
    document.body.appendChild(container);
  }

  const toastEl = document.createElement("div");
  const bgClass = {
    success: "text-bg-success",
    error: "text-bg-danger",
    danger: "text-bg-danger",
    warning: "text-bg-warning",
    info: "text-bg-primary"
  }[type] || "text-bg-primary";

  const iconClass = {
    success: "fa-check-circle",
    error: "fa-circle-exclamation",
    danger: "fa-triangle-exclamation",
    warning: "fa-triangle-exclamation",
    info: "fa-circle-info"
  }[type] || "fa-circle-info";

  toastEl.className = `toast align-items-center ${bgClass} border-0 shadow-lg`;
  toastEl.setAttribute("role", "alert");
  toastEl.setAttribute("aria-live", "assertive");
  toastEl.setAttribute("aria-atomic", "true");

  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body d-flex align-items-center gap-2">
        <i class="fa-solid ${iconClass}"></i>
        <div>${message}</div>
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `;

  container.appendChild(toastEl);
  if (window.bootstrap && bootstrap.Toast) {
    const bsToast = new bootstrap.Toast(toastEl, { delay: 4000 });
    bsToast.show();
    toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
  } else {
    setTimeout(() => toastEl.remove(), 4000);
  }
}

// --- Loading Overlay ---
function showLoading() {
  let overlay = document.getElementById("global-loading-overlay");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "global-loading-overlay";
    overlay.className = "loading-spinner-overlay";
    overlay.innerHTML = `
      <div class="text-center text-white">
        <div class="spinner-border text-light mb-3" style="width: 3rem; height: 3rem;" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <div class="fw-semibold">Loading transit data...</div>
      </div>
    `;
    document.body.appendChild(overlay);
  }
  overlay.style.display = "flex";
}

function hideLoading() {
  const overlay = document.getElementById("global-loading-overlay");
  if (overlay) {
    overlay.style.display = "none";
  }
}

// --- Status & Badge Formatters ---
function getStatusBadge(status) {
  if (!status) return `<span class="badge bg-secondary">UNKNOWN</span>`;
  const s = status.toUpperCase();
  if (s === "ON TIME" || s === "ACTIVE") {
    return `<span class="badge-status badge-on-time"><i class="fa-solid fa-circle-check"></i> ${status}</span>`;
  }
  if (s === "DELAYED") {
    return `<span class="badge-status badge-delayed"><i class="fa-solid fa-clock"></i> ${status}</span>`;
  }
  if (s === "SUSPENDED" || s === "CANCELLED" || s === "INACTIVE") {
    return `<span class="badge-status badge-suspended"><i class="fa-solid fa-circle-xmark"></i> ${status}</span>`;
  }
  if (s === "MAINTENANCE") {
    return `<span class="badge-status badge-maintenance"><i class="fa-solid fa-wrench"></i> ${status}</span>`;
  }
  return `<span class="badge bg-secondary">${status}</span>`;
}

function getPriorityBadge(priority) {
  const p = (priority || "MEDIUM").toUpperCase();
  const map = {
    LOW: "badge-priority-low",
    MEDIUM: "badge-priority-medium",
    HIGH: "badge-priority-high",
    CRITICAL: "badge-priority-critical"
  };
  return `<span class="badge ${map[p] || 'badge-priority-medium'} px-2 py-1">${p}</span>`;
}

// --- Dynamic Navbar State ---
function setupPublicNavbar() {
  const navContainer = document.getElementById("navbar-auth-links");
  if (!navContainer) return;

  const user = getStoredUser();
  if (user && isAuthenticated()) {
    let dashboardLink = "/dashboard.html";
    if (user.role === "ADMIN") dashboardLink = "/admin/dashboard.html";
    else if (user.role === "OPERATOR") dashboardLink = "/operator/dashboard.html";

    navContainer.innerHTML = `
      <div class="dropdown">
        <button class="btn btn-outline-light dropdown-toggle d-flex align-items-center gap-2" type="button" data-bs-toggle="dropdown">
          <i class="fa-solid fa-circle-user text-info"></i>
          <span>${user.full_name.split(' ')[0]}</span>
          <span class="badge bg-primary text-uppercase fs-xs">${user.role}</span>
        </button>
        <ul class="dropdown-menu dropdown-menu-end shadow-sm">
          <li><a class="dropdown-item" href="${dashboardLink}"><i class="fa-solid fa-gauge me-2 text-primary"></i> Dashboard</a></li>
          <li><a class="dropdown-item" href="/profile.html"><i class="fa-solid fa-user-gear me-2 text-secondary"></i> My Profile</a></li>
          <li><a class="dropdown-item" href="/favorites.html"><i class="fa-solid fa-heart me-2 text-danger"></i> Saved Items</a></li>
          <li><hr class="dropdown-divider"></li>
          <li><a class="dropdown-item text-danger" href="javascript:void(0)" onclick="logoutUser()"><i class="fa-solid fa-arrow-right-from-bracket me-2"></i> Logout</a></li>
        </ul>
      </div>
    `;
  } else {
    navContainer.innerHTML = `
      <a href="/login.html" class="btn btn-outline-light me-2"><i class="fa-solid fa-right-to-bracket me-1"></i> Login</a>
      <a href="/register.html" class="btn btn-primary-custom"><i class="fa-solid fa-user-plus me-1"></i> Register</a>
    `;
  }
}

// Run on page DOMContentLoaded
document.addEventListener("DOMContentLoaded", () => {
  setupPublicNavbar();
});
