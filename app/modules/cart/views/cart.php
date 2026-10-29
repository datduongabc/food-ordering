<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Cart - DaTeNO Restaurant</title>
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
                    <li class="breadcrumb-item"><a href="index.php?page=home#menu-list">Menu</a></li>
                    <li class="breadcrumb-item active" aria-current="page">Shopping Cart</li>
                </ol>
            </nav>

            <?php if (empty($cartItems)): ?>
                <div class="panel empty-panel">
                    <div class="empty-icon"><i class="bi bi-bag"></i></div>
                    <h3>Your cart is empty</h3>
                    <p>Looks like you haven't added anything yet. Explore our starters and main dishes to start your order.</p>
                    <a href="index.php?page=home#menu-list" class="btn btn-custom-primary rounded-pill px-4 py-2">
                        <i class="bi bi-book-half me-2"></i>Browse Menu
                    </a>
                </div>
            <?php else: ?>
                <ol class="checkout-steps" aria-label="Checkout progress">
                    <li class="is-active"><span class="step-dot">1</span>Cart</li>
                    <li><span class="step-dot">2</span>Payment</li>
                    <li><span class="step-dot">3</span>Done</li>
                </ol>

                <div class="row g-4">
                    <!-- Cart items -->
                    <div class="col-lg-8">
                        <div class="panel">
                            <div class="d-flex justify-content-between align-items-center px-4 pt-4 pb-3 border-bottom" style="border-color: var(--warm-border) !important;">
                                <h1 class="page-title fs-4">Your cart <small><?= (int)$totalCount ?> item<?= (int)$totalCount === 1 ? '' : 's' ?></small></h1>
                                <form action="index.php?page=cart&action=clear" method="POST" onsubmit="return confirm('Clear all items from your cart?');">
                                    <?= csrf_field() ?>
                                    <button type="submit" class="btn btn-sm btn-soft-danger rounded-pill px-3">
                                        <i class="bi bi-trash3 me-1"></i>Clear all
                                    </button>
                                </form>
                            </div>

                            <?php foreach ($cartItems as $item): ?>
                                <div class="cart-line">
                                    <a href="index.php?page=detail&slug=<?= e($item['slug']) ?>">
                                        <img src="<?= e($item['image_path']) ?>" alt="<?= e($item['name']) ?>" class="cart-thumb">
                                    </a>

                                    <div class="cart-line-info">
                                        <a href="index.php?page=detail&slug=<?= e($item['slug']) ?>" class="cart-line-name">
                                            <?= e($item['name']) ?>
                                        </a>
                                        <div class="d-flex flex-wrap align-items-center gap-2 mt-1">
                                            <span class="chip-soft"><?= e($item['category_name'] ?? 'Dish') ?></span>
                                            <span class="cart-line-unit"><?= format_price($item['price']) ?> each</span>
                                        </div>
                                    </div>

                                    <div class="cart-line-actions d-flex align-items-center gap-3">
                                        <form action="index.php?page=cart&action=update" method="POST" class="qty-stepper">
                                            <?= csrf_field() ?>
                                            <input type="hidden" name="product_id" value="<?= (int)$item['product_id'] ?>">
                                            <button type="submit" name="quantity" value="<?= (int)$item['quantity'] - 1 ?>" aria-label="Decrease quantity">
                                                <i class="bi bi-dash"></i>
                                            </button>
                                            <span><?= (int)$item['quantity'] ?></span>
                                            <button type="submit" name="quantity" value="<?= (int)$item['quantity'] + 1 ?>" aria-label="Increase quantity">
                                                <i class="bi bi-plus"></i>
                                            </button>
                                        </form>

                                        <span class="cart-line-total"><?= format_price($item['subtotal']) ?></span>

                                        <form action="index.php?page=cart&action=remove" method="POST" class="d-inline">
                                            <?= csrf_field() ?>
                                            <input type="hidden" name="product_id" value="<?= (int)$item['product_id'] ?>">
                                            <button type="submit" class="btn-icon-ghost" title="Remove dish" aria-label="Remove <?= e($item['name']) ?>">
                                                <i class="bi bi-trash3"></i>
                                            </button>
                                        </form>
                                    </div>
                                </div>
                            <?php endforeach; ?>
                        </div>

                        <a href="index.php?page=home#menu-list" class="d-inline-flex align-items-center gap-1 mt-3 text-decoration-none fw-semibold small text-teal-dark">
                            <i class="bi bi-arrow-left"></i>Continue adding dishes
                        </a>
                    </div>

                    <!-- Order summary -->
                    <div class="col-lg-4">
                        <div class="panel panel-pad summary-card">
                            <h2 class="panel-title">Order summary</h2>

                            <div class="summary-row"><span>Subtotal (<?= (int)$totalCount ?> items)</span><strong><?= format_price($totalPrice) ?></strong></div>
                            <div class="summary-row"><span>Delivery fee</span><strong class="text-success">Free</strong></div>
                            <div class="summary-row"><span>Service fee</span><strong class="text-success">Free</strong></div>

                            <div class="summary-total mb-4">
                                <span>Total</span>
                                <strong><?= format_price($totalPrice) ?></strong>
                            </div>

                            <?php if (isset($_SESSION['user_id'])): ?>
                                <div class="info-box mb-4">
                                    <i class="bi bi-person-check"></i>
                                    <div>
                                        <div class="fw-bold text-teal-dark"><?= e($_SESSION['name']) ?></div>
                                        <?php if (!empty($_SESSION['phone'])): ?>
                                            <div class="text-muted small"><?= e($_SESSION['phone']) ?></div>
                                        <?php endif; ?>
                                    </div>
                                </div>

                                <form action="index.php?page=cart&action=checkout" method="POST">
                                    <?= csrf_field() ?>

                                    <div class="fw-bold text-teal-dark small mb-2">Payment method</div>

                                    <label class="pay-option">
                                        <input type="radio" name="payment_method" value="MOMO" checked>
                                        <span class="pay-option-body">
                                            <span class="pay-logo pay-logo-momo">MoMo</span>
                                            <span>
                                                <strong class="d-block text-teal-dark">MoMo e-wallet</strong>
                                                <small class="text-muted">QR or app · ~<?= number_format(max(1000, (int)round($totalPrice * 25000))) ?>đ</small>
                                            </span>
                                            <span class="pay-check"></span>
                                        </span>
                                    </label>

                                    <label class="pay-option">
                                        <input type="radio" name="payment_method" value="COD">
                                        <span class="pay-option-body">
                                            <span class="pay-logo pay-logo-cod"><i class="bi bi-cash-coin"></i></span>
                                            <span>
                                                <strong class="d-block text-teal-dark">Cash on delivery</strong>
                                                <small class="text-muted">Pay when your food arrives</small>
                                            </span>
                                            <span class="pay-check"></span>
                                        </span>
                                    </label>

                                    <button type="submit" class="btn btn-custom-primary w-100 py-3 rounded-pill mt-2 d-flex justify-content-between align-items-center px-4">
                                        <span><i class="bi bi-lock-fill me-2"></i>Place order</span>
                                        <span><?= format_price($totalPrice) ?></span>
                                    </button>
                                    <p class="secure-note"><i class="bi bi-shield-check me-1"></i>Secure checkout · Your data is protected</p>
                                </form>
                            <?php else: ?>
                                <div class="info-box mb-3">
                                    <i class="bi bi-info-circle"></i>
                                    <span>Sign in to place your order. Your cart will be saved automatically.</span>
                                </div>
                                <a href="index.php?page=signin" class="btn btn-custom-primary w-100 py-3 rounded-pill">
                                    <i class="bi bi-box-arrow-in-right me-2"></i>Sign in to checkout
                                </a>
                                <p class="secure-note">New here? <a href="index.php?page=signup" class="text-primary-orange fw-semibold text-decoration-none">Create an account</a></p>
                            <?php endif; ?>
                        </div>
                    </div>
                </div>
            <?php endif; ?>
        </div>
    </main>

    <?php include ROOT_PATH . '/app/core/views/layouts/footer.php'; ?>
</body>

</html>
