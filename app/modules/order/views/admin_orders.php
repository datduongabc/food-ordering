<?php
$statusFilter = $_GET['status'] ?? null;
if (!isset($orders)) {
    require_once ROOT_PATH . '/app/modules/order/admin_order_controller.php';
    $admin_order_controller = new AdminOrderController();
    $orders = $admin_order_controller->getAllOrdersForAdmin($statusFilter);
}
$statuses = ['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED'];
?>

<div class="container-fluid px-0">
    <div class="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3">
        <div>
            <h2 class="fw-bold mb-1" style="color: #1f1712;">Order Management</h2>
            <p class="text-muted small mb-0">Track customer food orders and update fulfillment status</p>
        </div>

        <div class="d-flex gap-2">
            <a href="index.php?page=admin_orders"
                class="btn btn-sm rounded-pill px-3 <?= empty($statusFilter) ? 'btn-teal-dark' : 'btn-outline-secondary' ?>">
                All
            </a>
            <?php foreach ($statuses as $st): ?>
                <a href="index.php?page=admin_orders&status=<?= $st ?>"
                    class="btn btn-sm rounded-pill px-3 <?= $statusFilter === $st ? 'btn-teal-dark' : 'btn-outline-secondary' ?>">
                    <?= $st ?>
                </a>
            <?php endforeach; ?>
        </div>
    </div>

    <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0" style="min-width: 980px;">
                <thead class="table-dark">
                    <tr>
                        <th class="ps-4" style="width: 80px;">Order ID</th>
                        <th style="min-width: 200px;">Customer</th>
                        <th style="width: 100px;">Items</th>
                        <th style="width: 110px;">Total Price</th>
                        <th style="min-width: 160px;">Payment</th>
                        <th style="width: 140px;">Created At</th>
                        <th style="width: 160px;">Status</th>
                        <th class="pe-4 text-end" style="width: 130px;">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (empty($orders)): ?>
                        <tr>
                            <td colspan="8" class="text-center text-muted py-5">No orders found.</td>
                        </tr>
                    <?php else: ?>
                        <?php foreach ($orders as $order): ?>
                            <?php
                            $badgeClass = match ($order['status']) {
                                'COMPLETED' => 'bg-success',
                                'CONFIRMED' => 'bg-info text-dark',
                                'CANCELLED' => 'bg-danger',
                                default     => 'bg-warning text-dark'
                            };
                            $payMethod = $order['payment_method'] ?? 'COD';
                            $payStatus = $order['payment_status'] ?? 'UNPAID';
                            $payBadge = match ($payStatus) {
                                'PAID'   => 'bg-success',
                                'FAILED' => 'bg-danger',
                                default  => 'bg-warning text-dark'
                            };
                            $formattedDate = !empty($order['created_at'])
                                ? date('Y-m-d H:i', strtotime($order['created_at']))
                                : '—';
                            ?>
                            <tr>
                                <td class="ps-4 fw-bold">#<?= (int)$order['id'] ?></td>
                                <td>
                                    <div class="fw-bold" style="color: #1f1712;">
                                        <?= e($order['customer_name'] ?? 'User #' . $order['user_id']) ?>
                                    </div>
                                    <div class="text-muted small">
                                        <?= e($order['customer_phone'] ?? '') ?>
                                        <?= !empty($order['customer_email']) ? '• ' . e($order['customer_email']) : '' ?>
                                    </div>
                                </td>
                                <td>
                                    <span class="badge bg-secondary bg-opacity-10 text-dark px-2 py-1">
                                        <?= count($order['items'] ?? []) ?> dishes
                                    </span>
                                </td>
                                <td class="fw-bold text-nowrap" style="color: #d9381e;">
                                    <?= format_price($order['total_price']) ?>
                                </td>
                                <td class="text-nowrap">
                                    <span class="badge rounded-pill px-2 py-1" style="<?= $payMethod === 'MOMO' ? 'background-color:#a50064;color:#fff;' : 'background-color:#6c757d;color:#fff;' ?>">
                                        <?= e($payMethod) ?>
                                    </span>
                                    <span class="badge <?= $payBadge ?> rounded-pill px-2 py-1 ms-1">
                                        <?= e($payStatus) ?>
                                    </span>
                                </td>
                                <td class="text-muted small text-nowrap"><?= e($formattedDate) ?></td>
                                <td>
                                    <form action="index.php?page=admin_orders&action=update_status" method="POST" class="d-inline-flex align-items-center gap-1 mb-0">
                                        <?= csrf_field() ?>
                                        <input type="hidden" name="order_id" value="<?= (int)$order['id'] ?>">
                                        <select name="status" class="form-select form-select-sm fw-semibold" style="width: 140px;" onchange="this.form.submit()">
                                            <?php foreach ($statuses as $st): ?>
                                                <option value="<?= $st ?>" <?= $order['status'] === $st ? 'selected' : '' ?>>
                                                    <?= $st ?>
                                                </option>
                                            <?php endforeach; ?>
                                        </select>
                                    </form>
                                </td>
                                <td class="pe-4 text-end text-nowrap">
                                    <button type="button" class="btn btn-sm btn-info text-white me-1"
                                        data-bs-toggle="modal" data-bs-target="#viewOrderModal<?= (int)$order['id'] ?>">
                                        <i class="bi bi-eye me-1"></i>Details
                                    </button>
                                    <form action="index.php?page=admin_orders&action=delete" method="POST" class="d-inline"
                                        onsubmit="return confirm('Delete Order #<?= (int)$order['id'] ?> permanently?');">
                                        <?= csrf_field() ?>
                                        <input type="hidden" name="order_id" value="<?= (int)$order['id'] ?>">
                                        <button type="submit" class="btn btn-sm btn-danger">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    </form>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Order Details Modals (Placed OUTSIDE table for valid HTML5 DOM structure) -->
<?php if (!empty($orders)): ?>
    <?php foreach ($orders as $order): ?>
        <?php
        $badgeClass = match ($order['status']) {
            'COMPLETED' => 'bg-success',
            'CONFIRMED' => 'bg-info text-dark',
            'CANCELLED' => 'bg-danger',
            default     => 'bg-warning text-dark'
        };
        ?>
        <div class="modal fade" id="viewOrderModal<?= (int)$order['id'] ?>" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content rounded-4 border-0 shadow">
                    <div class="modal-header border-bottom">
                        <h5 class="modal-title fw-bold" style="color: #1f1712;">
                            Order #<?= (int)$order['id'] ?> Details
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-4">
                        <div class="row mb-3 small bg-light p-3 rounded-3">
                            <div class="col-md-4">
                                <span class="text-muted d-block">Customer</span>
                                <strong><?= e($order['customer_name'] ?? 'N/A') ?></strong>
                            </div>
                            <div class="col-md-4">
                                <span class="text-muted d-block">Phone / Email</span>
                                <strong><?= e($order['customer_phone'] ?? '') ?></strong>
                            </div>
                            <div class="col-md-4">
                                <span class="text-muted d-block">Status</span>
                                <span class="badge <?= $badgeClass ?>"><?= e($order['status']) ?></span>
                            </div>
                        </div>

                        <?php if (empty($order['items'])): ?>
                            <p class="text-muted text-center py-3 mb-0">No items recorded for this order.</p>
                        <?php else: ?>
                            <table class="table align-middle mb-0">
                                <thead class="table-light">
                                    <tr>
                                        <th>Dish</th>
                                        <th class="text-center">Price</th>
                                        <th class="text-center">Quantity</th>
                                        <th class="text-end">Subtotal</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <?php foreach ($order['items'] as $item): ?>
                                        <tr>
                                            <td>
                                                <div class="d-flex align-items-center gap-2">
                                                    <?php if (!empty($item['image_url'])): ?>
                                                        <img src="<?= e($item['image_path']) ?>"
                                                            class="rounded-2"
                                                            style="width: 44px; height: 44px; object-fit: cover;">
                                                    <?php endif; ?>
                                                    <span class="fw-semibold"><?= e($item['product_name'] ?? 'Dish #' . $item['product_id']) ?></span>
                                                </div>
                                            </td>
                                            <td class="text-center"><?= format_price($item['price_at_purchase']) ?></td>
                                            <td class="text-center">x<?= (int)$item['quantity'] ?></td>
                                            <td class="text-end fw-bold"><?= format_price((float)$item['price_at_purchase'] * (int)$item['quantity']) ?></td>
                                        </tr>
                                    <?php endforeach; ?>
                                </tbody>
                                <tfoot>
                                    <tr>
                                        <th colspan="3" class="text-end">Total Amount:</th>
                                        <th class="text-end fs-5" style="color: #d9381e;"><?= format_price($order['total_price']) ?></th>
                                    </tr>
                                </tfoot>
                            </table>
                        <?php endif; ?>
                    </div>
                    <div class="modal-footer border-top">
                        <button type="button" class="btn btn-secondary rounded-pill px-4" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    <?php endforeach; ?>
<?php endif; ?>
