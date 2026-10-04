/**
 * User Profile JavaScript
 */

document.addEventListener("DOMContentLoaded", async () => {
  if (!isAuthenticated()) {
    window.location.href = "/login.html";
    return;
  }

  await loadUserProfile();
  setupProfileForms();
});

async function loadUserProfile() {
  showLoading();
  try {
    const user = await apiRequest("/api/users/me");
    setStoredUser(user);

    document.getElementById("profile-display-name").textContent = user.full_name;
    document.getElementById("profile-display-username").textContent = `@${user.username}`;
    document.getElementById("profile-display-role").textContent = user.role;
    document.getElementById("profile-display-status").textContent = user.status;
    document.getElementById("profile-display-created").textContent = new Date(user.created_at).toLocaleDateString();

    // Fill Form inputs
    document.getElementById("profile_fullname").value = user.full_name;
    document.getElementById("profile_email").value = user.email;
    document.getElementById("profile_phone").value = user.phone || "";
    document.getElementById("profile_username").value = user.username;

  } catch (err) {
    showToast("Failed to load profile: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

function setupProfileForms() {
  const profileForm = document.getElementById("edit-profile-form");
  const passwordForm = document.getElementById("change-password-form");

  if (profileForm) {
    profileForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fullName = document.getElementById("profile_fullname").value.trim();
      const email = document.getElementById("profile_email").value.trim();
      const phone = document.getElementById("profile_phone").value.trim();

      showLoading();
      try {
        const updated = await apiRequest("/api/users/me", {
          method: "PUT",
          body: JSON.stringify({
            full_name: fullName,
            email,
            phone
          })
        });

        setStoredUser(updated);
        showToast("Profile details updated successfully!", "success");
        await loadUserProfile();
      } catch (err) {
        showToast(err.message, "error");
      } finally {
        hideLoading();
      }
    });
  }

  if (passwordForm) {
    passwordForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const oldPassword = document.getElementById("pwd_old").value;
      const newPassword = document.getElementById("pwd_new").value;
      const confirmPassword = document.getElementById("pwd_confirm").value;

      if (newPassword !== confirmPassword) {
        showToast("New passwords do not match.", "warning");
        return;
      }

      if (newPassword.length < 6) {
        showToast("New password must be at least 6 characters.", "warning");
        return;
      }

      showLoading();
      try {
        await apiRequest("/api/users/me/password", {
          method: "PUT",
          body: JSON.stringify({
            old_password: oldPassword,
            new_password: newPassword
          })
        });

        showToast("Password updated successfully!", "success");
        passwordForm.reset();
      } catch (err) {
        showToast(err.message, "error");
      } finally {
        hideLoading();
      }
    });
  }
}

async function deleteUserAccount() {
  if (!confirm("Are you sure you want to permanently delete your account? This action cannot be undone.")) return;
  
  showLoading();
  try {
    await apiRequest("/api/users/me", { method: "DELETE" });
    showToast("Account deleted successfully.", "info");
    setAuthToken(null);
    setStoredUser(null);
    setTimeout(() => window.location.href = "/register.html", 1000);
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    hideLoading();
  }
}
