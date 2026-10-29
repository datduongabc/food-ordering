<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Token - DaTeNO Restaurant</title>
    <!-- CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="<?= base_url('css/auth/auth.css') ?>">
    <!-- JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js" defer></script>
    <script src="<?= base_url('js/auth/secure_token.js') ?>" defer></script>
</head>

<body>
    <main class="auth-wrapper">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-12 col-md-6 col-lg-5">
                    <div class="auth-card shadow-lg">
                        <header class="text-center mb-4">
                            <h2 class="fw-bold">Verify Token</h2>
                            <p class="text-muted small mb-0">
                                Token sent to: <strong><?= e($_SESSION['email'] ?? 'your email') ?></strong>
                            </p>
                        </header>

                        <?php if (isset($_SESSION['auth_error'])): ?>
                            <div class="alert alert-danger text-center small py-2 mb-3">
                                <?= e($_SESSION['auth_error']);
                                unset($_SESSION['auth_error']); ?>
                            </div>
                        <?php endif; ?>

                        <?php if (!empty($_SESSION['dev_otp_token'])): ?>
                            <div class="alert alert-info small py-3 mb-3 border-0 shadow-sm">
                                <div class="fw-bold mb-1">
                                    <i class="bi bi-envelope-paper me-1"></i><?= e($_SESSION['dev_otp_notice'] ?? 'Sandbox Security Token:') ?>
                                </div>
                                <div class="bg-white rounded p-2 my-2 text-break font-monospace fw-bold text-center border" id="devTokenDisplay" style="font-size: 0.8rem;">
                                    <?= e($_SESSION['dev_otp_token']) ?>
                                </div>
                                <button type="button" class="btn btn-sm btn-outline-primary w-100 mt-1"
                                    onclick="document.getElementById('secureToken').value = '<?= e($_SESSION['dev_otp_token']) ?>';">
                                    <i class="bi bi-clipboard-check me-1"></i>Click to Auto-Fill Token
                                </button>
                            </div>
                        <?php endif; ?>

                        <form id="secureTokenForm" action="index.php?page=secure_token" method="POST">
                            <?= csrf_field() ?>
                            <div class="mb-4">
                                <label for="secureToken" class="form-label d-block text-center">Enter Secure Token</label>
                                <input id="secureToken" type="text" name="secure_token" class="form-control text-center" placeholder="Paste 64-character token here" required>
                            </div>
                            <button type="submit" class="btn btn-auth w-100">Verify & Continue</button>
                        </form>

                        <footer class="text-center mt-4">
                            <span class="small text-muted">Didn't receive code?
                                <?php
                                $resendPage = ($_SESSION['auth_type'] ?? '') === 'EMAIL_VERIFICATION' ? 'verify_email' : 'forgot_password';
                                ?>
                                <a href="index.php?page=<?= $resendPage ?>" class="auth-link">Resend</a>
                            </span>
                        </footer>
                    </div>
                </div>
            </div>
        </div>
    </main>
</body>

</html>
