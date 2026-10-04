/**
 * Authentication JavaScript - Login, Register, Role Redirection
 */

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const adminLoginForm = document.getElementById("admin-login-form");

  // Handle Passenger / General Login
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const identifier = document.getElementById("username_or_email").value.trim();
      const password = document.getElementById("password").value;
      const errorAlert = document.getElementById("auth-error-alert");

      if (errorAlert) errorAlert.classList.add("d-none");

      if (!identifier || !password) {
        if (errorAlert) {
          errorAlert.textContent = "Please provide both username/email and password.";
          errorAlert.classList.remove("d-none");
        }
        return;
      }

      showLoading();
      try {
        const response = await apiRequest("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({ username_or_email: identifier, password })
        });

        setAuthToken(response.access_token);
        setStoredUser(response.user);
        showToast(`Welcome back, ${response.user.full_name}!`, "success");

        // Role-based redirection
        setTimeout(() => {
          if (response.user.role === "ADMIN") {
            window.location.href = "/admin/dashboard.html";
          } else if (response.user.role === "OPERATOR") {
            window.location.href = "/operator/dashboard.html";
          } else {
            window.location.href = "/dashboard.html";
          }
        }, 600);
      } catch (err) {
        if (errorAlert) {
          errorAlert.textContent = err.message || "Login failed. Check your credentials.";
          errorAlert.classList.remove("d-none");
        }
        showToast(err.message, "error");
      } finally {
        hideLoading();
      }
    });
  }

  // Handle Admin Dedicated Login
  if (adminLoginForm) {
    adminLoginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const identifier = document.getElementById("admin_username").value.trim();
      const password = document.getElementById("admin_password").value;
      const errorAlert = document.getElementById("admin-error-alert");

      if (errorAlert) errorAlert.classList.add("d-none");

      showLoading();
      try {
        const response = await apiRequest("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({ username_or_email: identifier, password })
        });

        if (response.user.role !== "ADMIN" && response.user.role !== "OPERATOR") {
          throw new Error("Access denied. Admin or Operator credentials required.");
        }

        setAuthToken(response.access_token);
        setStoredUser(response.user);
        showToast("Administrative session authenticated.", "success");

        setTimeout(() => {
          if (response.user.role === "ADMIN") {
            window.location.href = "/admin/dashboard.html";
          } else {
            window.location.href = "/operator/dashboard.html";
          }
        }, 600);
      } catch (err) {
        if (errorAlert) {
          errorAlert.textContent = err.message || "Administrative login failed.";
          errorAlert.classList.remove("d-none");
        }
        showToast(err.message, "error");
      } finally {
        hideLoading();
      }
    });
  }

  // Handle Passenger Registration
  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fullName = document.getElementById("reg_fullname").value.trim();
      const username = document.getElementById("reg_username").value.trim();
      const email = document.getElementById("reg_email").value.trim();
      const phone = document.getElementById("reg_phone").value.trim();
      const password = document.getElementById("reg_password").value;
      const confirmPassword = document.getElementById("reg_confirm_password").value;
      const errorAlert = document.getElementById("register-error-alert");

      if (errorAlert) errorAlert.classList.add("d-none");

      // Frontend Form Validation
      if (!fullName || !username || !email || !password) {
        if (errorAlert) {
          errorAlert.textContent = "Please fill in all required fields.";
          errorAlert.classList.remove("d-none");
        }
        return;
      }

      if (password.length < 6) {
        if (errorAlert) {
          errorAlert.textContent = "Password must be at least 6 characters long.";
          errorAlert.classList.remove("d-none");
        }
        return;
      }

      if (password !== confirmPassword) {
        if (errorAlert) {
          errorAlert.textContent = "Passwords do not match. Please recheck.";
          errorAlert.classList.remove("d-none");
        }
        return;
      }

      showLoading();
      try {
        const response = await apiRequest("/api/auth/register", {
          method: "POST",
          body: JSON.stringify({
            full_name: fullName,
            username,
            email,
            phone,
            password
          })
        });

        setAuthToken(response.access_token);
        setStoredUser(response.user);
        showToast("Registration successful! Welcome aboard.", "success");

        setTimeout(() => {
          window.location.href = "/dashboard.html";
        }, 800);
      } catch (err) {
        if (errorAlert) {
          errorAlert.textContent = err.message || "Registration failed.";
          errorAlert.classList.remove("d-none");
        }
        showToast(err.message, "error");
      } finally {
        hideLoading();
      }
    });
  }
});
