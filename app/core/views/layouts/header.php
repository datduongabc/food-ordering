<?php
$cartCount = function_exists('get_cart_count') ? get_cart_count() : 0;
$currentPage = $_GET['page'] ?? 'home';
?>
<!-- Global CSRF token used by asynchronous (fetch) POST requests -->
<input type="hidden" name="csrf_token" id="globalCsrfToken" value="<?= e(csrf_token()) ?>">

<header class="site-header sticky-top">
    <nav class="navbar navbar-expand-lg">
        <div class="container">
            <a class="navbar-brand fw-bold" href="index.php?page=home" aria-label="DaTeNO home">
                <span class="brand-icon-badge"><i class="bi bi-fire"></i></span>
                <span class="brand-wordmark"><span class="text-primary-orange">DaT</span><span class="text-teal-dark">eNO</span></span>
            </a>

            <div class="d-flex align-items-center gap-2 d-lg-none ms-auto">
                <a class="btn-icon-round position-relative" href="index.php?page=cart" aria-label="View cart">
                    <i class="bi bi-bag"></i>
                    <span class="cart-dot <?= $cartCount > 0 ? '' : 'd-none' ?>" data-cart-count><?= (int)$cartCount ?></span>
                </a>
                <button class="navbar-toggler border-0 shadow-none" type="button" data-bs-toggle="collapse"
                    data-bs-target="#navbarContent" aria-controls="navbarContent" aria-expanded="false" aria-label="Toggle navigation">
                    <i class="bi bi-list fs-3 text-teal-dark"></i>
                </button>
            </div>

            <div class="collapse navbar-collapse" id="navbarContent">
                <ul class="navbar-nav main-nav mb-2 mb-lg-0 ms-lg-3">
                    <li class="nav-item"><a class="nav-link <?= $currentPage === 'home' ? 'active' : '' ?>" href="index.php?page=home">Home</a></li>
                    <li class="nav-item"><a class="nav-link" href="index.php?page=home#menu-list">Menu</a></li>
                    <li class="nav-item"><a class="nav-link" href="index.php?page=home#feedback">Reviews</a></li>
                    <li class="nav-item"><a class="nav-link" href="index.php?page=home#reservation">Book a Table</a></li>
                </ul>

                <div class="search-wrapper flex-grow-1 position-relative mx-lg-4 my-3 my-lg-0">
                    <i class="bi bi-search search-icon"></i>
                    <input id="ajaxSearch" class="form-control" type="search"
                        placeholder="Search for dishes, e.g. “pho”, “steak”..." autocomplete="off" aria-label="Search dishes">
                    <div id="searchResults" class="search-results-dropdown shadow-lg rounded-4 d-none"></div>
                </div>

                <div class="d-flex align-items-center gap-2 header-actions">
                    <a class="btn-cart-pill d-none d-lg-inline-flex" href="index.php?page=cart" aria-label="View cart">
                        <i class="bi bi-bag-fill"></i>
                        <span>Cart</span>
                        <span id="headerCartBadge" class="cart-count-badge <?= $cartCount > 0 ? '' : 'd-none' ?>"><?= (int)$cartCount ?></span>
                    </a>

                    <?php if (isset($_SESSION['user_id'])): ?>
                        <div class="dropdown">
                            <a class="user-chip dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                                <span class="user-avatar"><?= e(mb_strtoupper(mb_substr($_SESSION['name'] ?? 'U', 0, 1))) ?></span>
                                <span class="d-none d-xl-inline fw-semibold text-truncate" style="max-width: 120px;"><?= e($_SESSION['name']); ?></span>
                            </a>
                            <ul class="dropdown-menu dropdown-menu-end shadow mt-2">
                                <li class="px-3 pt-1 pb-2">
                                    <div class="small text-muted">Signed in as</div>
                                    <div class="fw-bold text-teal-dark text-truncate"><?= e($_SESSION['name']); ?></div>
                                </li>
                                <li><hr class="dropdown-divider"></li>
                                <?php if (($_SESSION['role'] ?? '') === 'ADMIN'): ?>
                                    <li><a class="dropdown-item" href="index.php?page=admin_dashboard"><i class="bi bi-speedometer2 me-2 text-primary-orange"></i>Admin Dashboard</a></li>
                                <?php endif; ?>
                                <?php if (empty($_SESSION['is_email_verified'])): ?>
                                    <li><a class="dropdown-item text-warning" href="index.php?page=verify_email"><i class="bi bi-exclamation-triangle-fill me-2"></i>Verify Account</a></li>
                                <?php endif; ?>
                                <li><a class="dropdown-item" href="index.php?page=orders"><i class="bi bi-receipt me-2"></i>My Orders &amp; Bookings</a></li>
                                <li><a class="dropdown-item" href="index.php?page=change_password"><i class="bi bi-shield-lock me-2"></i>Change Password</a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item text-danger" href="index.php?page=signout"><i class="bi bi-box-arrow-right me-2"></i>Sign Out</a></li>
                            </ul>
                        </div>
                    <?php else: ?>
                        <a href="index.php?page=signin" class="btn btn-link text-teal-dark fw-semibold text-decoration-none d-none d-lg-inline">Log in</a>
                        <a href="index.php?page=signup" class="btn btn-custom-primary rounded-pill px-4">Sign up</a>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    </nav>
</header>

<!-- Mobile floating cart bar (DoorDash / GrabFood pattern) -->
<a href="index.php?page=cart" class="mobile-cart-bar d-lg-none <?= $cartCount > 0 && $currentPage !== 'cart' ? '' : 'd-none' ?>" id="mobileCartBar">
    <span class="d-flex align-items-center gap-2">
        <span class="mobile-cart-count" data-cart-count><?= (int)$cartCount ?></span>
        <span class="fw-bold">View your cart</span>
    </span>
    <i class="bi bi-arrow-right-circle-fill fs-4"></i>
</a>

<?php
$flashSuccess = $_SESSION['flash_success'] ?? $_SESSION['auth_success'] ?? null;
$flashError = $_SESSION['flash_error'] ?? null;
unset($_SESSION['flash_success'], $_SESSION['auth_success'], $_SESSION['flash_error']);
?>
<?php if ($flashSuccess || $flashError): ?>
    <div class="container mt-3">
        <div class="alert alert-<?= $flashSuccess ? 'success' : 'danger' ?> alert-dismissible fade show rounded-4 px-4 py-3 shadow-sm mb-0 d-flex align-items-center" role="alert">
            <i class="bi <?= $flashSuccess ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill' ?> me-2 fs-5"></i>
            <span><?= e($flashSuccess ?? $flashError) ?></span>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    </div>
<?php endif; ?>
