<?php
$currentPage = $page ?? ($_GET['page'] ?? 'admin_dashboard');
?>
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - DaTeNO Restaurant</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <link rel="stylesheet" href="<?= base_url('css/admin/admin.css') ?>">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js" defer></script>
</head>

<body class="bg-light">
    <div class="d-flex min-vh-100">
        <aside class="admin-sidebar bg-teal-dark text-white p-3 shadow-lg d-flex flex-column">
            <h4 class="fw-bold text-center mb-4 py-3 border-bottom border-secondary">
                <span class="text-primary-orange">DaT</span>eNO Admin
            </h4>

            <div class="px-3 py-2 mb-3 rounded-3 bg-white bg-opacity-10 small">
                <div class="text-white-50">Signed in as</div>
                <div class="fw-bold text-truncate"><?= e($_SESSION['name'] ?? 'Administrator') ?></div>
            </div>

            <nav class="nav flex-column gap-2 flex-grow-1">
                <a
                    href="index.php?page=admin_dashboard"
                    class="nav-link text-white rounded <?= $currentPage === 'admin_dashboard' ? 'active-link' : '' ?>">
                    <i class="bi bi-speedometer2 me-2"></i> Dashboard
                </a>
                <a
                    href="index.php?page=admin_products"
                    class="nav-link text-white rounded <?= $currentPage === 'admin_products' ? 'active-link' : '' ?>">
                    <i class="bi bi-box-seam me-2"></i> Product Management
                </a>
                <a
                    href="index.php?page=admin_orders"
                    class="nav-link text-white rounded <?= $currentPage === 'admin_orders' ? 'active-link' : '' ?>">
                    <i class="bi bi-receipt-cutoff me-2"></i> Order Management
                </a>
                <a
                    href="index.php?page=admin_reservations"
                    class="nav-link text-white rounded <?= $currentPage === 'admin_reservations' ? 'active-link' : '' ?>">
                    <i class="bi bi-calendar2-check me-2"></i> Reservation Management
                </a>
                <a
                    href="index.php?page=admin_users"
                    class="nav-link text-white rounded <?= $currentPage === 'admin_users' ? 'active-link' : '' ?>">
                    <i class="bi bi-people me-2"></i> User Management
                </a>

                <hr class="opacity-25 my-3">

                <a
                    href="index.php?page=home&view=store"
                    class="nav-link text-white rounded">
                    <i class="bi bi-shop me-2 text-warning"></i> View Storefront
                </a>
                <a href="index.php?page=signout" class="nav-link text-danger fw-bold mt-auto">
                    <i class="bi bi-box-arrow-right me-2"></i> Sign Out
                </a>
            </nav>
        </aside>

        <main class="flex-grow-1 p-4 p-md-5 overflow-auto">
            <?php if (isset($_SESSION['admin_success']) || isset($_SESSION['admin_error'])): ?>
                <div class="alert alert-<?= isset($_SESSION['admin_success']) ? 'success' : 'danger' ?> alert-dismissible fade show shadow-sm rounded-3 mb-4" role="alert">
                    <i class="bi <?= isset($_SESSION['admin_success']) ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill' ?> me-2"></i>
                    <?= e($_SESSION['admin_success'] ?? $_SESSION['admin_error']) ?>
                    <?php unset($_SESSION['admin_success'], $_SESSION['admin_error']); ?>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            <?php endif; ?>

            <?php
            if ($currentPage === 'admin_products') {
                include ROOT_PATH . '/app/modules/product/views/admin_products.php';
            } elseif ($currentPage === 'admin_users') {
                include ROOT_PATH . '/app/modules/user/views/admin_users.php';
            } elseif ($currentPage === 'admin_orders') {
                include ROOT_PATH . '/app/modules/order/views/admin_orders.php';
            } elseif ($currentPage === 'admin_reservations') {
                include ROOT_PATH . '/app/modules/reservation/views/admin_reservations.php';
            } else {
                include ROOT_PATH . '/app/modules/user/views/admin_dashboard.php';
            }
            ?>
        </main>
    </div>
</body>

</html>
