<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Orders & Reservations - DaTeNO Restaurant</title>
    <!-- Bootstrap -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js" defer></script>
    <!-- Custom CSS -->
    <link rel="stylesheet" href="<?= base_url('css/style.css') ?>">
    <link rel="stylesheet" href="<?= base_url('css/header.css') ?>">
    <link rel="stylesheet" href="<?= base_url('css/pages.css') ?>">
    <link rel="stylesheet" href="<?= base_url('css/footer.css') ?>">
    <script src="<?= base_url('js/header/search.js') ?>" defer></script>
    <script src="<?= base_url('js/cart/cart.js') ?>" defer></script>
</head>

<body class="d-flex flex-column min-vh-100 page-shell">
    <?php include ROOT_PATH . '/app/core/views/layouts/header.php'; ?>

    <main class="flex-grow-1 page-main">
        <div class="container">
            <!-- Breadcrumb -->
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb breadcrumb-warm">
                    <li class="breadcrumb-item"><a href="index.php?page=home">Home</a></li>
                    <li class="breadcrumb-item active" aria-current="page">My Orders & Reservations</li>
                </ol>
            </nav>

            <div class="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3">
                <h1 class="page-title">My Activity</h1>

                <!-- Segmented Tabs Navigation -->
                <ul class="nav seg-tabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link <?= $activeTab === 'orders' ? 'active' : '' ?>"
                            id="orders-tab" data-bs-toggle="pill" data-bs-target="#orders-pane" type="button" role="tab">
                            <i class="bi bi-bag me-1"></i>Orders <span class="count"><?= count($orders) ?></span>
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link <?= $activeTab === 'reservations' ? 'active' : '' ?>"
                            id="reservations-tab" data-bs-toggle="pill" data-bs-target="#reservations-pane" type="button" role="tab">
                            <i class="bi bi-calendar-check me-1"></i>Bookings <span class="count"><?= count($reservations) ?></span>
                        </button>
                    </li>
                </ul>
            </div>

            <div class="tab-content">
                <!-- Food Orders Pane -->
                <div class="tab-pane fade <?= $activeTab === 'orders' ? 'show active' : '' ?>" id="orders-pane" role="tabpanel">
                    <?php if (empty($orders)): ?>
                        <div class="panel empty-panel">
                            <div class="empty-icon"><i class="bi bi-receipt"></i></div>
                            <h3>You haven't placed any orders yet</h3>
                            <p>Discover our signature dishes and place your first order today.</p>
                            <a href="index.php?page=home#menu-list" class="btn btn-custom-primary rounded-pill px-4 py-2">
                                <i class="bi bi-book-half me-2"></i>Explore Menu
                            </a>
                        </div>
                    <?php else: ?>
                        <div class="d-flex flex-column gap-3">
                            <?php foreach ($orders as $order): ?>
                                <?php
                                $statusClass = match ($order['status']) {
                                    'COMPLETED' => 'status-completed',
                                    'CONFIRMED' => 'status-confirmed',
                                    'CANCELLED' => 'status-cancelled',
                                    default     => 'status-pending'
                                };
                                $paymentMethod = $order['payment_method'] ?? 'COD';
                                $paymentStatus = $order['payment_status'] ?? 'UNPAID';
                                $payStatusClass = match ($paymentStatus) {
                                    'PAID'     => 'status-paid',
                                    'FAILED'   => 'status-failed',
                                    'REFUNDED' => 'status-refunded',
                                    default    => 'status-pending'
                                };
                                ?>
                                <div class="panel order-card">
                                    <div class="order-card-head">
                                        <div>
                                            <span class="order-id">Order #<?= (int)$order['id'] ?></span>
                                            <span class="order-meta ms-2">
                                                <i class="bi bi-clock me-1"></i><?= e($order['created_at']) ?>
                                            </span>
                                            <?php if (!empty($order['momo_trans_id'])): ?>
                                                <span class="badge bg-light text-dark border ms-2 small">
                                                    Trans ID: <?= e($order['momo_trans_id']) ?>
                                                </span>
                                            <?php endif; ?>
                                        </div>
                                        <div class="d-flex flex-wrap align-items-center gap-2">
                                            <?php if ($paymentMethod === 'MOMO'): ?>
                                                <span class="method-badge momo">
                                                    <i class="bi bi-wallet2 me-1"></i>MoMo
                                                </span>
                                            <?php else: ?>
                                                <span class="method-badge">
                                                    <i class="bi bi-cash me-1"></i>COD
                                                </span>
                                            <?php endif; ?>

                                            <span class="status-badge <?= $payStatusClass ?>">
                                                <?= e($paymentStatus) ?>
                                            </span>

                                            <span class="status-badge <?= $statusClass ?>">
                                                <?= e($order['status']) ?>
                                            </span>

                                            <?php if ($order['status'] !== 'CANCELLED' && $paymentStatus !== 'PAID'): ?>
                                                <a href="index.php?page=orders&action=momo_pay&order_id=<?= (int)$order['id'] ?>"
                                                    class="btn btn-momo btn-sm rounded-pill px-3">
                                                    <i class="bi bi-qr-code me-1"></i>Pay with MoMo
                                                </a>
                                            <?php endif; ?>

                                            <?php if ($order['status'] === 'PENDING'): ?>
                                                <form action="index.php?page=orders&action=cancel" method="POST" onsubmit="return confirm('Cancel Order #<?= (int)$order['id'] ?>?');">
                                                    <?= csrf_field() ?>
                                                    <input type="hidden" name="order_id" value="<?= (int)$order['id'] ?>">
                                                    <button type="submit" class="btn btn-soft-danger btn-sm rounded-pill px-3">
                                                        Cancel
                                                    </button>
                                                </form>
                                            <?php endif; ?>
                                        </div>
                                    </div>

                                    <div class="order-items">
                                        <?php if (empty($order['items'])): ?>
                                            <p class="text-muted small py-3 mb-0">No item details recorded for this order.</p>
                                        <?php else: ?>
                                            <?php foreach ($order['items'] as $item): ?>
                                                <div class="order-item">
                                                    <?php if (!empty($item['image_url'])): ?>
                                                        <img src="<?= e($item['image_path']) ?>" alt="<?= e($item['product_name']) ?>">
                                                    <?php endif; ?>
                                                    <div class="flex-grow-1">
                                                        <a href="index.php?page=detail&slug=<?= e($item['product_slug'] ?? '') ?>" class="fw-bold text-teal-dark text-decoration-none">
                                                            <?= e($item['product_name'] ?? 'Dish #' . $item['product_id']) ?>
                                                        </a>
                                                        <div class="text-muted small">
                                                            Unit price: <?= format_price($item['price_at_purchase']) ?>
                                                        </div>
                                                    </div>
                                                    <div class="text-muted fw-semibold">
                                                        x<?= (int)$item['quantity'] ?>
                                                    </div>
                                                    <div class="text-end fw-bold text-teal-dark" style="min-width: 90px;">
                                                        <?= format_price((float)$item['price_at_purchase'] * (int)$item['quantity']) ?>
                                                    </div>
                                                </div>
                                            <?php endforeach; ?>
                                        <?php endif; ?>
                                    </div>

                                    <div class="order-card-foot">
                                        <span class="text-muted small">Total amount</span>
                                        <span class="fs-5 fw-bold text-primary-orange"><?= format_price($order['total_price']) ?></span>
                                    </div>
                                </div>
                            <?php endforeach; ?>
                        </div>
                    <?php endif; ?>
                </div>

                <!-- Table Reservations Pane -->
                <div class="tab-pane fade <?= $activeTab === 'reservations' ? 'show active' : '' ?>" id="reservations-pane" role="tabpanel">
                    <?php if (empty($reservations)): ?>
                        <div class="panel empty-panel">
                            <div class="empty-icon"><i class="bi bi-calendar2-week"></i></div>
                            <h3>No table reservations found</h3>
                            <p>Book a table in advance for a seamless dining experience at any of our branches.</p>
                            <a href="index.php?page=home#reservation" class="btn btn-custom-teal rounded-pill px-4 py-2">
                                Book a Table
                            </a>
                        </div>
                    <?php else: ?>
                        <div class="row g-4">
                            <?php foreach ($reservations as $res): ?>
                                <?php
                                $resStatusClass = match ($res['status']) {
                                    'COMPLETED' => 'status-completed',
                                    'CONFIRMED' => 'status-confirmed',
                                    'CANCELLED' => 'status-cancelled',
                                    default     => 'status-pending'
                                };
                                $dateObj = strtotime($res['reservation_date'] ?? 'now');
                                ?>
                                <div class="col-md-6">
                                    <div class="panel booking-card">
                                        <div class="d-flex justify-content-between align-items-start mb-3">
                                            <div class="d-flex gap-3 align-items-center">
                                                <div class="booking-date">
                                                    <span class="m"><?= date('M', $dateObj) ?></span>
                                                    <span class="d"><?= date('d', $dateObj) ?></span>
                                                </div>
                                                <div>
                                                    <h5 class="fw-bold text-teal-dark mb-0">
                                                        <?= e($res['branch_title'] ?? 'DaTeNO Branch') ?>
                                                    </h5>
                                                    <p class="text-muted small mb-0">
                                                        <i class="bi bi-geo-alt me-1 text-primary-orange"></i><?= e($res['branch_name'] ?? '') ?>
                                                    </p>
                                                </div>
                                            </div>
                                            <span class="status-badge <?= $resStatusClass ?>">
                                                <?= e($res['status']) ?>
                                            </span>
                                        </div>

                                        <div class="info-box mb-3">
                                            <div class="booking-facts w-100">
                                                <span><i class="bi bi-clock"></i><?= e($res['reservation_time']) ?></span>
                                                <span><i class="bi bi-people"></i><?= (int)$res['guest_count'] ?> guests</span>
                                                <span><i class="bi bi-telephone"></i><?= e($res['customer_phone']) ?></span>
                                            </div>
                                        </div>

                                        <?php if (!empty($res['special_requests'])): ?>
                                            <p class="small text-muted mb-3">
                                                <strong>Special requests:</strong> <?= e($res['special_requests']) ?>
                                            </p>
                                        <?php endif; ?>

                                        <?php if ($res['status'] === 'PENDING'): ?>
                                            <div class="mt-auto text-end pt-2">
                                                <form action="index.php?page=reservation&action=cancel" method="POST" onsubmit="return confirm('Cancel this table reservation?');">
                                                    <?= csrf_field() ?>
                                                    <input type="hidden" name="reservation_id" value="<?= (int)$res['id'] ?>">
                                                    <button type="submit" class="btn btn-soft-danger btn-sm rounded-pill px-3">
                                                        Cancel booking
                                                    </button>
                                                </form>
                                            </div>
                                        <?php endif; ?>
                                    </div>
                                </div>
                            <?php endforeach; ?>
                        </div>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    </main>

    <?php include ROOT_PATH . '/app/core/views/layouts/footer.php'; ?>
</body>

</html>
