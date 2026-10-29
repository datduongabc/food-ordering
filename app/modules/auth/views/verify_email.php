<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Email - DaTeNO Restaurant</title>
    <!-- CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="<?= base_url('css/auth/auth.css') ?>">
    <!-- JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js" defer></script>
    <script src="<?= base_url('js/auth/verify_email.js') ?>" defer></script>
</head>

<body>
    <main class="auth-wrapper">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-12 col-md-6 col-lg-5">
                    <div class="auth-card shadow-lg">
                        <header class="text-center mb-4">
                            <h2 class="fw-bold">Verify Your Email</h2>
                            <p class="text-muted small mb-0">
                                Your account is not verified yet. Please click the button below to receive a secure token via email.
                            </p>
                        </header>

                        <?php if (isset($_SESSION['auth_error'])): ?>
                            <div class="mb-3">
                                <div class="alert alert-danger text-center small py-2 mb-0">
                                    <?= e($_SESSION['auth_error']); ?>
                                    <?php unset($_SESSION['auth_error']); ?>
                                </div>
                            </div>
                        <?php endif; ?>

                        <form id="verifyEmailForm" action="index.php?page=verify_email" method="POST">
                            <?= csrf_field() ?>
                            <button type="submit" class="btn btn-auth w-100">
                                Send Verification Code
                            </button>
                        </form>

                        <footer class="text-center mt-4">
                            <a href="index.php" class="auth-link small text-decoration-none fw-bold">
                                <i class="bi bi-arrow-left me-1"></i>Back to Home
                            </a>
                        </footer>
                    </div>
                </div>
            </div>
        </div>
    </main>
</body>

</html>
