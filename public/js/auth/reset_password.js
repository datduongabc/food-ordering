document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("resetPasswordForm");
  if (!form) return;

  form.addEventListener("submit", (event) => {
    const newPass = document.getElementById("newPassword");
    const btn = form.querySelector('button[type="submit"]');

    if (newPass && newPass.value.length < 8) {
      event.preventDefault();
      alert("Password must be at least 8 characters long.");
      newPass.focus();
      return;
    }

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Updating...';
    }
  });
});
