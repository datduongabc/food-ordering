document.addEventListener("DOMContentLoaded", () => {
  // Ensure toast container exists
  let toastContainer = document.getElementById("datenoToastContainer");
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "datenoToastContainer";
    toastContainer.className = "toast-container position-fixed bottom-0 end-0 p-3";
    toastContainer.style.zIndex = "1090";
    document.body.appendChild(toastContainer);
  }

  const escapeHtml = (str) => {
    const div = document.createElement("div");
    div.textContent = str ?? "";
    return div.innerHTML;
  };

  const showToast = (message, isSuccess = true) => {
    const bgClass = isSuccess ? "bg-teal-dark text-white" : "bg-danger text-white";
    const icon = isSuccess
      ? "bi-check-circle-fill text-warning"
      : "bi-exclamation-triangle-fill";

    const toastEl = document.createElement("div");
    toastEl.className = `toast align-items-center ${bgClass} border-0 shadow-lg rounded-3 mb-2`;
    toastEl.setAttribute("role", "alert");
    toastEl.setAttribute("aria-live", "assertive");
    toastEl.setAttribute("aria-atomic", "true");
    toastEl.innerHTML = `
      <div class="d-flex">
        <div class="toast-body fw-semibold">
          <i class="bi ${icon} me-2"></i>${escapeHtml(message)}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;

    toastContainer.appendChild(toastEl);

    if (typeof bootstrap !== "undefined" && bootstrap.Toast) {
      const bsToast = new bootstrap.Toast(toastEl, { delay: 3000 });
      bsToast.show();
      toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
    } else {
      toastEl.classList.add("show");
      setTimeout(() => toastEl.remove(), 3000);
    }
  };

  const updateHeaderCartBadge = (count) => {
    const badges = [
      document.getElementById("headerCartBadge"),
      ...document.querySelectorAll("[data-cart-count]"),
    ].filter(Boolean);
    badges.forEach((badge) => {
      badge.textContent = count;
      badge.classList.toggle("d-none", !(count > 0));
      badge.classList.remove("cart-bump");
      void badge.offsetWidth; // restart the bump animation
      badge.classList.add("cart-bump");
    });
    const mobileBar = document.getElementById("mobileCartBar");
    if (mobileBar) mobileBar.classList.toggle("d-none", !(count > 0));
  };

  // Handle Add to Cart buttons using modern Fetch API + async/await
  document.addEventListener("click", async (e) => {
    const btn = e.target.closest(".js-add-to-cart");
    if (!btn) return;

    e.preventDefault();
    const productId = btn.dataset.productId;
    const quantity = btn.dataset.quantity || "1";
    const originalHtml = btn.innerHTML;

    if (!productId || btn.disabled) return;

    const isCompact = btn.classList.contains("btn-add-round");
    btn.disabled = true;
    btn.innerHTML = isCompact
      ? '<span class="spinner-border spinner-border-sm"></span>'
      : '<span class="spinner-border spinner-border-sm me-1"></span>Adding...';

    try {
      const formData = new FormData();
      formData.append("product_id", productId);
      formData.append("quantity", quantity);
      formData.append("ajax", "1");

      const csrfInput = document.querySelector('input[name="csrf_token"]');
      const csrfToken = csrfInput ? csrfInput.value : "";
      formData.append("csrf_token", csrfToken);

      const response = await fetch("index.php?page=cart&action=add", {
        method: "POST",
        headers: {
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRF-Token": csrfToken,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }

      const res = await response.json();

      if (res && res.success) {
        updateHeaderCartBadge(res.cart_count);
        showToast(res.message, true);
        btn.innerHTML = isCompact
          ? '<i class="bi bi-check-lg"></i>'
          : '<i class="bi bi-check2 me-1"></i>Added!';
        btn.classList.add("is-added");
        setTimeout(() => {
          btn.disabled = false;
          btn.classList.remove("is-added");
          btn.innerHTML = originalHtml;
        }, 900);
      } else {
        showToast((res && res.message) || "Could not add item.", false);
        btn.disabled = false;
        btn.innerHTML = originalHtml;
      }
    } catch (error) {
      showToast("Network error while adding to cart.", false);
      btn.disabled = false;
      btn.innerHTML = originalHtml;
    }
  });

  // Handle quantity +/- buttons on Menu Detail page
  document.addEventListener("click", (e) => {
    const qtyBtn = e.target.closest(".js-qty-btn");
    if (!qtyBtn) return;

    const input = document.getElementById("qty-input");
    if (!input) return;

    const current = parseInt(input.value, 10) || 1;
    const step = parseInt(qtyBtn.dataset.step, 10) || 0;
    const min = parseInt(input.getAttribute("min"), 10) || 1;
    const max = parseInt(input.getAttribute("max"), 10) || 20;
    input.value = Math.min(max, Math.max(min, current + step));
  });
});
