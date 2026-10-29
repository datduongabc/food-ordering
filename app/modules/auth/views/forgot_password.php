<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Forgot Password - DaTeNO Restaurant</title>
    <!-- CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="<?= base_url('css/auth/auth.css') ?>">
    <!-- JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js" defer></script>
    <script src="<?= base_url('js/auth/forgot_password.js') ?>" defer></script>
</head>

<body>
    <main class="auth-wrapper">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-12 col-md-6 col-lg-5">
                    <div class="auth-card shadow-lg">
                        <header class="text-center mb-4">
                            <h2 class="fw-bold">Forgot Password</h2>
                            <p class="text-muted small mb-0">Enter your email to receive a secure token</p>
                        </header>

                        <?php if (isset($_SESSION['auth_error']) || isset($_SESSION['auth_success'])): ?>
                            <div class="mb-3">
                                <div class="alert alert-<?= isset($_SESSION['auth_success']) ? 'success' : 'danger' ?> text-center small py-2 mb-0">
                                    <?= e($_SESSION['auth_success'] ?? $_SESSION['auth_error']) ?>
                                    <?php unset($_SESSION['auth_success'], $_SESSION['auth_error']); ?>
                                </div>
                            </div>
                        <?php endif; ?>

                        <form id="forgotPasswordForm" action="index.php?page=forgot_password" method="POST">
                            <?= csrf_field() ?>
                            <div class="mb-4">
                                <label for="email" class="form-label">Email Address</label>
                                <input id="email" type="email" name="email" class="form-control" placeholder="example@mail.com" required>
                            </div>
                            <button type="submit" class="btn btn-auth w-100">Send Token</button>
                        </form>

                        <footer class="text-center mt-4">
                            <a href="index.php?page=signin" class="auth-link small text-decoration-none">
                                <i class="bi bi-arrow-left me-1"></i>Back to Sign In
                            </a>
                        </footer>
                    </div>
                </div>
            </div>
        </div>
    </main>
</body>

</html>
