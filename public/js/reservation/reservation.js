document.addEventListener("DOMContentLoaded", () => {
  const reservationForm = document.getElementById("reservationForm");
  if (!reservationForm) return;

  reservationForm.addEventListener("submit", (event) => {
    const phoneInput = document.getElementById("phone");
    const dateInput = document.getElementById("bookingDate");
    const submitBtn = reservationForm.querySelector('button[type="submit"]');

    const phoneRegex = /^[0-9]{10}$/;
    if (phoneInput && !phoneRegex.test(phoneInput.value.trim())) {
      event.preventDefault();
      alert("Phone number must be exactly 10 digits.");
      phoneInput.focus();
      return;
    }

    if (dateInput && dateInput.value) {
      const selectedDate = new Date(dateInput.value + "T00:00:00");
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      if (selectedDate < today) {
        event.preventDefault();
        alert("Reservation date cannot be in the past.");
        dateInput.focus();
        return;
      }
    }

    if (submitBtn) {
      submitBtn.style.width = `${submitBtn.offsetWidth}px`;
      submitBtn.disabled = true;
      submitBtn.innerHTML =
        '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Confirming...';
    }
  });
});
