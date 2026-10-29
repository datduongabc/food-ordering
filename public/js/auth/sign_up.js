document.addEventListener("DOMContentLoaded", () => {
  const signupForm = document.getElementById("signupForm");
  const toggleIcon = document.getElementById("togglePasswordIcon");
  const passwordInput = document.getElementById("password");
  const phoneInput = document.getElementById("phone");

  if (signupForm) {
    signupForm.addEventListener("submit", (event) => {
      const phoneVal = phoneInput ? phoneInput.value.trim() : "";
      const passVal = passwordInput ? passwordInput.value : "";

      if (!/^[0-9]{10}$/.test(phoneVal)) {
        event.preventDefault();
        alert("Phone number is invalid. Must have exactly 10 digits.");
        if (phoneInput) phoneInput.focus();
        return;
      }

      if (passVal.length < 8) {
        event.preventDefault();
        alert("The password must contain at least 8 characters.");
        if (passwordInput) passwordInput.focus();
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
