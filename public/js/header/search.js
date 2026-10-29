document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("ajaxSearch");
  const searchResults = document.getElementById("searchResults");

  if (!searchInput || !searchResults) return;

  let debounceTimer = null;
  let activeController = null;

  const escapeHtml = (str) => {
    const div = document.createElement("div");
    div.textContent = str ?? "";
    return div.innerHTML;
  };

  const performSearch = async (query) => {
    // Cancel any previous in-flight search request to prevent race conditions
    if (activeController) {
      activeController.abort();
    }
    activeController = new AbortController();

    try {
      const params = new URLSearchParams({
        page: "product_search",
        query: query,
      });

      const response = await fetch(`index.php?${params.toString()}`, {
        method: "GET",
        headers: {
          Accept: "application/json",
          "X-Requested-With": " fetch",
        },
        signal: activeController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }

      const data = await response.json();
      searchResults.innerHTML = "";
      searchResults.classList.remove("d-none");

      if (Array.isArray(data) && data.length > 0) {
        const fragment = document.createDocumentFragment();

        data.forEach((item) => {
          const imgPath = `images/${encodeURIComponent(item.category_slug || "starters")}/${encodeURIComponent(item.image_url || "")}`;
          const priceFormatted = "$" + parseFloat(item.price || 0).toFixed(2);
          const ratingBadge = item.average_rating
            ? `<span class="badge bg-warning text-dark ms-2">★ ${parseFloat(item.average_rating).toFixed(1)}</span>`
            : "";

          const link = document.createElement("a");
          link.href = `index.php?page=detail&slug=${encodeURIComponent(item.slug)}`;
          link.className = "dropdown-item d-flex align-items-center py-2 px-3 border-bottom";
          link.innerHTML = `
            <img src="${imgPath}"
              alt="${escapeHtml(item.name)}"
              class="rounded-3 shadow-sm flex-shrink-0"
              style="width: 56px; height: 56px; object-fit: cover">
            <div class="ms-3 d-flex flex-column justify-content-between align-items-start overflow-hidden">
              <div class="fw-bold text-teal-dark text-truncate w-100" style="font-size: 1rem;">
                ${escapeHtml(item.name)}${ratingBadge}
              </div>
              <p class="fw-bold text-primary-orange mb-0" style="font-size: 0.95rem;">
                ${priceFormatted}
              </p>
            </div>
          `;
          fragment.appendChild(link);
        });

        searchResults.appendChild(fragment);
      } else {
        searchResults.innerHTML =
          '<div class="p-3 text-muted text-center small">No matching dishes found.</div>';
      }
    } catch (error) {
      if (error.name === "AbortError") {
        // Request was intentionally aborted by newer keystroke
        return;
      }
      searchResults.innerHTML =
        '<p class="p-3 text-danger text-center small mb-0">Error loading search results.</p>';
      searchResults.classList.remove("d-none");
    }
  };

  searchInput.addEventListener("input", (e) => {
    const query = e.target.value.trim();
    clearTimeout(debounceTimer);

    if (query.length > 0) {
      debounceTimer = setTimeout(() => {
        performSearch(query);
      }, 300);
    } else {
      if (activeController) {
        activeController.abort();
      }
      searchResults.classList.add("d-none");
      searchResults.innerHTML = "";
    }
  });

  // Hide dropdown when clicking outside
  document.addEventListener("click", (e) => {
    if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
      searchResults.classList.add("d-none");
    }
  });

  // Re-open dropdown on focus if results already exist
  searchInput.addEventListener("focus", () => {
    if (searchInput.value.trim().length > 0 && searchResults.children.length > 0) {
      searchResults.classList.remove("d-none");
    }
  });
});
