<?php
if (!isset($stats)) {
    require_once ROOT_PATH . '/app/modules/order/admin_order_controller.php';
    $adminOrderCtrl = new AdminOrderController();
    $stats = $adminOrderCtrl->getDashboardStats();
    $recentOrders = array_slice($adminOrderCtrl->getAllOrdersForAdmin(), 0, 5);
}
if (!isset($recentReservations)) {
    require_once ROOT_PATH . '/app/modules/reservation/admin_reservation_controller.php';
    $adminResCtrl = new AdminReservationController();
    $recentReservations = array_slice($adminResCtrl->getAllReservationsForAdmin(), 0, 5);
}
?>

<div class="container-fluid px-0">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h2 class="fw-bold mb-1" style="color: #1f1712;">Dashboard Overview</h2>
            <p class="text-muted small mb-0">Real-time metrics for DaTeNO Restaurant operations</p>
        </div>
        <a href="index.php?page=home&view=store" class="btn btn-custom-primary rounded-pill px-4">
            <i class="bi bi-box-arrow-up-right me-1"></i>Open Customer Storefront
        </a>
    </div>

    <!-- KPI Cards -->
    <div class="row g-4 mb-5">
        <div class="col-sm-6 col-xl-3">
            <div class="card border-0 shadow-sm rounded-4 p-4 bg-white h-100">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="text-muted fw-semibold small text-uppercase">Completed Revenue</span>
                    <span class="badge bg-success bg-opacity-10 text-success p-2 rounded-3">
                        <i class="bi bi-currency-dollar fs-5"></i>
                    </span>
                </div>
                <h3 class="fw-bold mb-1" style="color: #d9381e;">
                    <?= format_price($stats['total_revenue'] ?? 0) ?>
                </h3>
                <span class="text-muted small">From completed food orders</span>
            </div>
        </div>

        <div class="col-sm-6 col-xl-3">
            <div class="card border-0 shadow-sm rounded-4 p-4 bg-white h-100">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="text-muted fw-semibold small text-uppercase">Total Orders</span>
                    <span class="badge bg-primary bg-opacity-10 text-primary p-2 rounded-3">
                        <i class="bi bi-bag-check fs-5"></i>
                    </span>
                </div>
                <h3 class="fw-bold mb-1" style="color: #1f1712;">
                    <?= (int)($stats['total_orders'] ?? 0) ?>
                </h3>
                <span class="small text-warning fw-semibold">
                    <?= (int)($stats['pending_orders'] ?? 0) ?> pending approval
                </span>
            </div>
        </div>

        <div class="col-sm-6 col-xl-3">
            <div class="card border-0 shadow-sm rounded-4 p-4 bg-white h-100">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="text-muted fw-semibold small text-uppercase">Table Reservations</span>
                    <span class="badge bg-info bg-opacity-10 text-info p-2 rounded-3">
                        <i class="bi bi-calendar2-week fs-5"></i>
                    </span>
                </div>
                <h3 class="fw-bold mb-1" style="color: #1f1712;">
                    <?= (int)($stats['total_reservations'] ?? 0) ?>
                </h3>
                <span class="small text-warning fw-semibold">
                    <?= (int)($stats['pending_reservations'] ?? 0) ?> awaiting confirmation
                </span>
            </div>
        </div>

        <div class="col-sm-6 col-xl-3">
            <div class="card border-0 shadow-sm rounded-4 p-4 bg-white h-100">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="text-muted fw-semibold small text-uppercase">Active Menu & Users</span>
                    <span class="badge bg-warning bg-opacity-10 text-warning p-2 rounded-3">
                        <i class="bi bi-people fs-5"></i>
                    </span>
                </div>
                <h3 class="fw-bold mb-1" style="color: #1f1712;">
                    <?= (int)($stats['total_products'] ?? 0) ?> Dishes
                </h3>
                <span class="text-muted small">
                    <?= (int)($stats['total_users'] ?? 0) ?> registered accounts
                </span>
            </div>
        </div>
    </div>

    <!-- Recent Orders & Recent Reservations -->
    <div class="row g-4">
        <div class="col-lg-6">
            <div class="card border-0 shadow-sm rounded-4 bg-white h-100">
                <div class="card-header bg-white border-bottom px-4 py-3 d-flex justify-content-between align-items-center">
                    <h5 class="fw-bold mb-0" style="color: #1f1712;">Recent Food Orders</h5>
                    <a href="index.php?page=admin_orders" class="btn btn-sm btn-outline-secondary rounded-pill px-3">View All</a>
                </div>
                <div class="table-responsive">
                    <table class="table align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th class="ps-4">ID</th>
                                <th>Customer</th>
                                <th>Total</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php if (empty($recentOrders)): ?>
                                <tr>
                                    <td colspan="4" class="text-center text-muted py-4">No orders yet.</td>
                                </tr>
                            <?php else: ?>
                                <?php foreach ($recentOrders as $ord): ?>
                                    <?php
                                    $bClass = match ($ord['status']) {
                                        'COMPLETED' => 'bg-success',
                                        'CONFIRMED' => 'bg-info text-dark',
                                        'CANCELLED' => 'bg-danger',
                                        default     => 'bg-warning text-dark'
                                    };
                                    ?>
                                    <tr>
                                        <td class="ps-4 fw-bold">#<?= (int)$ord['id'] ?></td>
                                        <td><?= e($ord['customer_name'] ?? 'User #' . $ord['user_id']) ?></td>
                                        <td class="fw-bold" style="color: #d9381e;"><?= format_price($ord['total_price']) ?></td>
                                        <td><span class="badge <?= $bClass ?> rounded-pill"><?= e($ord['status']) ?></span></td>
                                    </tr>
                                <?php endforeach; ?>
                            <?php endif; ?>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="col-lg-6">
            <div class="card border-0 shadow-sm rounded-4 bg-white h-100">
                <div class="card-header bg-white border-bottom px-4 py-3 d-flex justify-content-between align-items-center">
                    <h5 class="fw-bold mb-0" style="color: #1f1712;">Recent Table Bookings</h5>
                    <a href="index.php?page=admin_reservations" class="btn btn-sm btn-outline-secondary rounded-pill px-3">View All</a>
                </div>
                <div class="table-responsive">
                    <table class="table align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th class="ps-4">Guest</th>
                                <th>Date & Time</th>
                                <th>Guests</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php if (empty($recentReservations)): ?>
                                <tr>
                                    <td colspan="4" class="text-center text-muted py-4">No reservations yet.</td>
                                </tr>
                            <?php else: ?>
                                <?php foreach ($recentReservations as $res): ?>
                                    <?php
                                    $rClass = match ($res['status']) {
                                        'COMPLETED' => 'bg-success',
                                        'CONFIRMED' => 'bg-info text-dark',
                                        'CANCELLED' => 'bg-danger',
                                        default     => 'bg-warning text-dark'
                                    };
                                    ?>
                                    <tr>
                                        <td class="ps-4">
                                            <div class="fw-semibold"><?= e($res['customer_name']) ?></div>
                                            <small class="text-muted"><?= e($res['customer_phone']) ?></small>
                                        </td>
                                        <td>
                                            <div><?= e($res['reservation_date']) ?></div>
                                            <small class="text-muted"><?= e($res['reservation_time']) ?></small>
                                        </td>
                                        <td><?= (int)$res['guest_count'] ?></td>
                                        <td><span class="badge <?= $rClass ?> rounded-pill"><?= e($res['status']) ?></span></td>
                                    </tr>
                                <?php endforeach; ?>
                            <?php endif; ?>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
