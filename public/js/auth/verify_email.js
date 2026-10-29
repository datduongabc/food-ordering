document.addEventListener("DOMContentLoaded", () => {
  const verifyForm = document.getElementById("verifyEmailForm");
  if (!verifyForm) return;

  verifyForm.addEventListener("submit", () => {
    const submitBtn = verifyForm.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.style.width = `${submitBtn.offsetWidth}px`;
      submitBtn.disabled = true;
      submitBtn.innerHTML =
        '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Sending Email...';
    }
  });
});
