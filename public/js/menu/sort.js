document.addEventListener("DOMContentLoaded", () => {
  const sortDropdown = document.getElementById("sort-dropdown");
  const productContainer = document.getElementById("ajax-product-container");
  const filterPills = document.querySelectorAll(".btn-filter-pill[data-sort]");

  if (!productContainer) return;

  let activeController = null;

  // Keep the pill bar and the dropdown in sync with the current sort value
  const syncActiveState = (sort) => {
    filterPills.forEach((pill) => {
      const isActive = pill.dataset.sort === sort;
      pill.classList.toggle("active", isActive);
      pill.setAttribute("aria-selected", isActive ? "true" : "false");
    });
    if (sortDropdown && sortDropdown.value !== sort) {
      sortDropdown.value = sort;
    }
  };

  // Skeleton placeholders (perceived performance, as used by Uber Eats / DoorDash)
  const renderSkeleton = (count = 8) => {
    const card = `
      <div class="col-6 col-md-4 col-lg-3">
        <div class="dish-card skeleton-card">
          <div class="skeleton skeleton-img"></div>
          <div class="dish-body">
            <div class="skeleton skeleton-line w-75"></div>
            <div class="skeleton skeleton-line w-100"></div>
            <div class="skeleton skeleton-line w-50"></div>
          </div>
        </div>
      </div>`;
    productContainer.innerHTML = card.repeat(count);
  };

  const scrollToMenuTop = () => {
    const section = document.getElementById("menu-list");
    if (!section) return;
    const top = section.getBoundingClientRect().top + window.scrollY - 90;
    if (window.scrollY > top) {
      window.scrollTo({ top, behavior: "smooth" });
    }
  };

  const loadMenu = async (page, sort, pushHistory = true) => {
    // Cancel any previous in-flight menu request
    if (activeController) {
      activeController.abort();
    }
    activeController = new AbortController();

    syncActiveState(sort);
    renderSkeleton();

    try {
      const params = new URLSearchParams({
        page: "product_sort",
        p: page,
        sort: sort,
      });

      const response = await fetch(`index.php?${params.toString()}`, {
        method: "GET",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
        signal: activeController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }

      const html = await response.text();
      productContainer.innerHTML = html;

      if (pushHistory) {
        const newUrl = `?page=home&p=${encodeURIComponent(page)}&sort=${encodeURIComponent(sort)}`;
        window.history.pushState({ page, sort }, "", newUrl);
      }
    } catch (error) {
      if (error.name === "AbortError") {
        return;
      }
      productContainer.innerHTML = `
        <div class="col-12">
          <div class="empty-state">
            <i class="bi bi-wifi-off"></i>
            <h3>Could not load the menu</h3>
            <p>Please check your connection and try again.</p>
          </div>
        </div>`;
    }
  };

  if (sortDropdown) {
    sortDropdown.addEventListener("change", (e) => {
      loadMenu(1, e.target.value, true);
    });
  }

  filterPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      if (pill.classList.contains("active")) return;
      loadMenu(1, pill.dataset.sort, true);
    });
  });

  // Event delegation for pagination links
  document.addEventListener("click", (e) => {
    const pageLink = e.target.closest(".custom-pagination .page-link");
    if (!pageLink) return;

    e.preventDefault();
    const href = pageLink.getAttribute("href") || "";
    const queryString = href.includes("?") ? href.split("?")[1] : "";
    const urlParams = new URLSearchParams(queryString);
    const pageNumber = urlParams.get("p");
    const sortValue = sortDropdown ? sortDropdown.value : "default";

    if (pageNumber) {
      scrollToMenuTop();
      loadMenu(pageNumber, sortValue, true);
    }
  });

  // Handle browser Back/Forward navigation smoothly
  window.addEventListener("popstate", () => {
    const params = new URLSearchParams(window.location.search);
    const page = params.get("p") || 1;
    const sort = params.get("sort") || "default";
    loadMenu(page, sort, false);
  });
});
