document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("forgotPasswordForm");
  if (!form) return;

  form.addEventListener("submit", (event) => {
    const emailInput = document.getElementById("email");
    const emailVal = emailInput ? emailInput.value.trim() : "";
    const btn = form.querySelector('button[type="submit"]');

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(emailVal)) {
      event.preventDefault();
      alert("Please enter a valid email address.");
      if (emailInput) emailInput.focus();
      return;
    }

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Sending...';
    }
  });
});
