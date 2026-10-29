<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MoMo Payment - Order #<?= (int)$paymentIntent['order_id'] ?> - DaTeNO</title>
    <!-- Bootstrap -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js" defer></script>
    <!-- Custom CSS -->
    <link rel="stylesheet" href="<?= base_url('css/style.css') ?>">
    <link rel="stylesheet" href="<?= base_url('css/header.css') ?>">
    <link rel="stylesheet" href="<?= base_url('css/pages.css') ?>">
    <link rel="stylesheet" href="<?= base_url('css/footer.css') ?>">
</head>

<body class="d-flex flex-column min-vh-100 page-shell">
    <?php include ROOT_PATH . '/app/core/views/layouts/header.php'; ?>

    <main class="flex-grow-1 page-main">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-lg-9 col-xl-8">
                    <ol class="checkout-steps mx-auto mb-4" aria-label="Checkout progress">
                        <li class="is-done"><span class="step-dot"><i class="bi bi-check"></i></span>Cart</li>
                        <li class="is-active"><span class="step-dot">2</span>Payment</li>
                        <li><span class="step-dot">3</span>Done</li>
                    </ol>

                    <div class="panel overflow-hidden">
                        <!-- MoMo Top Bar -->
                        <div class="momo-head">
                            <div class="d-flex align-items-center gap-3">
                                <span class="momo-logo">mo<span style="color:#d82d8b;">mo</span></span>
                                <div>
                                    <div class="fw-bold fs-5">MoMo E-Wallet Payment</div>
                                    <div class="small opacity-75">Instant &amp; secure transaction</div>
                                </div>
                            </div>
                            <span class="momo-timer">
                                <i class="bi bi-stopwatch me-1"></i>Expires in <span id="momoTimer">15:00</span>
                            </span>
                        </div>

                        <div class="p-4 p-md-5">
                            <div class="row g-4 align-items-center">
                                <!-- QR Frame -->
                                <div class="col-md-6 text-center">
                                    <div class="qr-frame mb-3">
                                        <svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="MoMo Payment QR Code">
                                            <rect width="200" height="200" fill="#ffffff"/>
                                            <!-- Finder Patterns -->
                                            <rect x="12" y="12" width="52" height="52" fill="none" stroke="#a50064" stroke-width="8"/>
                                            <rect x="26" y="26" width="24" height="24" fill="#a50064"/>
                                            <rect x="136" y="12" width="52" height="52" fill="none" stroke="#a50064" stroke-width="8"/>
                                            <rect x="150" y="26" width="24" height="24" fill="#a50064"/>
                                            <rect x="12" y="136" width="52" height="52" fill="none" stroke="#a50064" stroke-width="8"/>
                                            <rect x="26" y="150" width="24" height="24" fill="#a50064"/>
                                            <!-- Data Modules -->
                                            <g fill="#231f20">
                                                <rect x="76" y="14" width="10" height="10"/><rect x="96" y="14" width="10" height="10"/><rect x="114" y="14" width="10" height="10"/>
                                                <rect x="76" y="32" width="18" height="10"/><rect x="104" y="32" width="18" height="10"/>
                                                <rect x="76" y="50" width="10" height="14"/><rect x="96" y="50" width="12" height="14"/><rect x="116" y="50" width="10" height="14"/>
                                                <rect x="14" y="76" width="14" height="10"/><rect x="38" y="76" width="20" height="10"/><rect x="68" y="76" width="12" height="10"/><rect x="124" y="76" width="18" height="10"/><rect x="154" y="76" width="32" height="10"/>
                                                <rect x="14" y="96" width="24" height="10"/><rect x="48" y="96" width="14" height="10"/><rect x="134" y="96" width="20" height="10"/><rect x="164" y="96" width="22" height="10"/>
                                                <rect x="14" y="116" width="12" height="10"/><rect x="34" y="116" width="28" height="10"/><rect x="134" y="116" width="14" height="10"/><rect x="158" y="116" width="28" height="10"/>
                                                <rect x="76" y="136" width="16" height="10"/><rect x="102" y="136" width="22" height="10"/><rect x="136" y="136" width="20" height="10"/><rect x="166" y="136" width="20" height="10"/>
                                                <rect x="76" y="156" width="24" height="10"/><rect x="110" y="156" width="14" height="10"/><rect x="136" y="156" width="30" height="10"/><rect x="174" y="156" width="12" height="10"/>
                                                <rect x="76" y="176" width="12" height="12"/><rect x="98" y="176" width="24" height="12"/><rect x="132" y="176" width="18" height="12"/><rect x="160" y="176" width="26" height="12"/>
                                            </g>
                                            <!-- Center MoMo Emblem -->
                                            <rect x="76" y="76" width="48" height="48" rx="10" fill="#a50064"/>
                                            <text x="100" y="105" text-anchor="middle" fill="#ffffff" font-family="Arial, sans-serif" font-weight="bold" font-size="14">MoMo</text>
                                        </svg>
                                    </div>
                                    <div class="small text-muted">Scan with MoMo App to pay</div>
                                </div>

                                <!-- Order Details & Actions -->
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <div class="small text-muted">Total amount to pay</div>
                                        <div class="momo-amount"><?= e($paymentIntent['amount_vnd_label']) ?></div>
                                        <div class="text-muted small">≈ <?= format_price($paymentIntent['amount_usd']) ?> (Rate: 1 USD = <?= number_format($paymentIntent['exchange_rate']) ?> VND)</div>
                                    </div>

                                    <div class="mb-4">
                                        <div class="kv-row">
                                            <span>Order reference</span>
                                            <strong>Order #<?= (int)$paymentIntent['order_id'] ?></strong>
                                        </div>
                                        <div class="kv-row">
                                            <span>Merchant</span>
                                            <strong>DaTeNO Restaurant</strong>
                                        </div>
                                        <div class="kv-row">
                                            <span>MoMo Order ID</span>
                                            <code><?= e($paymentIntent['momo_order_id']) ?></code>
                                        </div>
                                    </div>

                                    <?php if (!empty($paymentIntent['sandbox'])): ?>
                                        <div class="info-box mb-3 py-2">
                                            <i class="bi bi-info-circle fs-5"></i>
                                            <span class="small"><strong>Sandbox Mode:</strong> Click below to simulate instant payment confirmation.</span>
                                        </div>

                                        <form action="index.php?page=orders&action=momo_return" method="POST" class="mb-2">
                                            <?= csrf_field() ?>
                                            <input type="hidden" name="internal_order_id" value="<?= (int)$paymentIntent['order_id'] ?>">
                                            <input type="hidden" name="orderId" value="<?= e($paymentIntent['momo_order_id']) ?>">
                                            <input type="hidden" name="requestId" value="<?= e($paymentIntent['request_id']) ?>">
                                            <input type="hidden" name="amount" value="<?= (int)$paymentIntent['amount_vnd'] ?>">
                                            <input type="hidden" name="resultCode" value="0">
                                            <input type="hidden" name="transId" value="MOMO<?= time() ?>">
                                            <input type="hidden" name="signature" value="<?= e($paymentIntent['success_signature']) ?>">
                                            <button type="submit" class="btn btn-momo w-100 py-3 rounded-pill">
                                                <i class="bi bi-check-circle-fill me-2"></i>Confirm MoMo Payment (<?= e($paymentIntent['amount_vnd_label']) ?>)
                                            </button>
                                        </form>

                                        <form action="index.php?page=orders&action=momo_return" method="POST">
                                            <?= csrf_field() ?>
                                            <input type="hidden" name="internal_order_id" value="<?= (int)$paymentIntent['order_id'] ?>">
                                            <input type="hidden" name="orderId" value="<?= e($paymentIntent['momo_order_id']) ?>">
                                            <input type="hidden" name="requestId" value="<?= e($paymentIntent['request_id']) ?>">
                                            <input type="hidden" name="amount" value="<?= (int)$paymentIntent['amount_vnd'] ?>">
                                            <input type="hidden" name="resultCode" value="1006">
                                            <input type="hidden" name="signature" value="<?= e($paymentIntent['cancel_signature']) ?>">
                                            <button type="submit" class="btn btn-soft-danger w-100 py-2 rounded-pill small">
                                                Cancel payment
                                            </button>
                                        </form>
                                    <?php else: ?>
                                        <div class="alert alert-info small">
                                            Please open your MoMo application and scan the QR code to complete payment.
                                        </div>
                                    <?php endif; ?>

                                    <div class="text-center mt-3">
                                        <a href="index.php?page=orders" class="text-decoration-none small text-muted">
                                            <i class="bi bi-arrow-left me-1"></i>Back to My Orders (pay later)
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            let seconds = 15 * 60;
            const timerEl = document.getElementById('momoTimer');
            if (!timerEl) return;
            setInterval(() => {
                if (seconds <= 0) return;
                seconds--;
                const m = String(Math.floor(seconds / 60)).padStart(2, '0');
                const s = String(seconds % 60).padStart(2, '0');
                timerEl.textContent = `${m}:${s}`;
            }, 1000);
        });
    </script>

    <?php include ROOT_PATH . '/app/core/views/layouts/footer.php'; ?>
</body>

</html>
