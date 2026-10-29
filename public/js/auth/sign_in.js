document.addEventListener("DOMContentLoaded", () => {
  const signinForm = document.getElementById("signinForm");
  const toggleIcon = document.getElementById("togglePasswordIcon");
  const passwordInput = document.getElementById("password");

  if (signinForm && passwordInput) {
    signinForm.addEventListener("submit", (event) => {
      if (passwordInput.value.length < 8) {
        event.preventDefault();
        alert("Password must be at least 8 characters long.");
        passwordInput.focus();
      }
    });
  }

  if (toggleIcon && passwordInput) {
    toggleIcon.addEventListener("click", () => {
      const isPassword = passwordInput.getAttribute("type") === "password";
      passwordInput.setAttribute("type", isPassword ? "text" : "password");
      toggleIcon.classList.toggle("fa-eye");
      toggleIcon.classList.toggle("fa-eye-slash");
    });
  }
});
