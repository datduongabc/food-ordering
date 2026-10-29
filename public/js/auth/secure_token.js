document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("secureTokenForm");
  if (!form) return;

  form.addEventListener("submit", (event) => {
    const tokenInput = document.getElementById("secureToken");
    const tokenVal = tokenInput ? tokenInput.value.trim() : "";
    const btn = form.querySelector('button[type="submit"]');

    if (tokenVal.length !== 64) {
      event.preventDefault();
      alert("Invalid token length. Please check your email again.");
      if (tokenInput) tokenInput.focus();
      return;
    }

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Verifying...';
    }
  });
});
