<?php
if (!isset($products)) {
    require_once ROOT_PATH . '/app/modules/product/product_controller.php';
    $product_controller = new ProductController();
    $p = isset($_GET['p']) ? (int)$_GET['p'] : 1;
    $limit = 12;
    $sort = isset($_GET['sort']) ? $_GET['sort'] : 'default';

    $data = $product_controller->getProductsPaginated($p, $limit, $sort);
    $products = $data['products'];
    $current_page = $data['current_page'];
    $total_pages = $data['total_pages'];
}
$current_sort = $_GET['sort'] ?? 'default';
$category_tabs = [
    'default'     => ['label' => 'All dishes',  'icon' => 'bi-grid'],
    'starters'    => ['label' => 'Starters',    'icon' => 'bi-egg-fried'],
    'main_dishes' => ['label' => 'Main dishes', 'icon' => 'bi-fire'],
    'rating_desc' => ['label' => 'Top rated',   'icon' => 'bi-star'],
    'price_asc'   => ['label' => 'Budget picks', 'icon' => 'bi-tag'],
];
?>

<!-- Menu List -->
<section class="menu-section" id="menu-list">
    <div class="container">
        <div class="section-heading d-flex flex-column flex-md-row justify-content-between align-items-md-end gap-3">
            <div>
                <span class="section-eyebrow">Our menu</span>
                <h2 class="section-title font-serif-bistro">What would you like to eat today?</h2>
                <p class="section-subtitle mb-0">Handcrafted dishes made with fresh ingredients every day.</p>
            </div>

            <div class="sort-container d-flex align-items-center gap-2">
                <label for="sort-dropdown" class="text-muted small fw-semibold text-nowrap mb-0">
                    <i class="bi bi-sliders2 me-1"></i>Sort by
                </label>
                <select name="sort" id="sort-dropdown" class="form-select form-select-sm">
                    <option value="default" <?= $current_sort === 'default' ? 'selected' : '' ?>>Recommended</option>
                    <optgroup label="Price">
                        <option value="price_asc" <?= $current_sort === 'price_asc' ? 'selected' : '' ?>>Price: Low to High</option>
                        <option value="price_desc" <?= $current_sort === 'price_desc' ? 'selected' : '' ?>>Price: High to Low</option>
                    </optgroup>
                    <optgroup label="Rating">
                        <option value="rating_desc" <?= $current_sort === 'rating_desc' ? 'selected' : '' ?>>Rating: High to Low</option>
                        <option value="rating_asc" <?= $current_sort === 'rating_asc' ? 'selected' : '' ?>>Rating: Low to High</option>
                    </optgroup>
                    <optgroup label="Category">
                        <option value="starters" <?= $current_sort === 'starters' ? 'selected' : '' ?>>Starters</option>
                        <option value="main_dishes" <?= $current_sort === 'main_dishes' ? 'selected' : '' ?>>Main Dishes</option>
                    </optgroup>
                </select>
            </div>
        </div>

        <!-- Sticky horizontal category tabs (Uber Eats / GrabFood pattern) -->
        <div class="category-tabs-wrap">
            <div class="category-pills-bar" role="tablist" aria-label="Filter dishes">
                <?php foreach ($category_tabs as $value => $tab): ?>
                    <button type="button" class="btn-filter-pill <?= $current_sort === $value ? 'active' : '' ?>"
                        data-sort="<?= e($value) ?>" role="tab" aria-selected="<?= $current_sort === $value ? 'true' : 'false' ?>">
                        <i class="bi <?= e($tab['icon']) ?>"></i><?= e($tab['label']) ?>
                    </button>
                <?php endforeach; ?>
            </div>
        </div>

        <div class="row g-4" id="ajax-product-container" aria-live="polite">
            <?php include ROOT_PATH . '/app/modules/product/views/menu_list_pagination.php' ?>
        </div>
    </div>
</section>

<!-- How it works -->
<section class="how-section">
    <div class="container">
        <div class="text-center mb-5">
            <span class="section-eyebrow">How it works</span>
            <h2 class="section-title font-serif-bistro">Your meal in 3 simple steps</h2>
        </div>
        <div class="row g-4">
            <div class="col-md-4">
                <div class="how-step">
                    <span class="how-num">01</span>
                    <span class="how-icon"><i class="bi bi-search-heart"></i></span>
                    <h3>Choose your dishes</h3>
                    <p>Browse the menu, filter by category and add favourites to your cart.</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="how-step">
                    <span class="how-num">02</span>
                    <span class="how-icon"><i class="bi bi-wallet2"></i></span>
                    <h3>Checkout securely</h3>
                    <p>Pay with MoMo e-wallet or cash on delivery – fast and safe.</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="how-step">
                    <span class="how-num">03</span>
                    <span class="how-icon"><i class="bi bi-emoji-smile"></i></span>
                    <h3>Enjoy your meal</h3>
                    <p>Track your order status and enjoy hot food at your doorstep.</p>
                </div>
            </div>
        </div>
    </div>
</section>
