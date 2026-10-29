<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Password - DaTeNO Restaurant</title>
    <!-- CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="<?= base_url('css/auth/auth.css') ?>">
    <!-- JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js" defer></script>
    <script src="<?= base_url('js/auth/reset_password.js') ?>" defer></script>
</head>

<body>
    <main class="auth-wrapper">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-12 col-md-6 col-lg-5">
                    <div class="auth-card shadow-lg">
                        <header class="text-center mb-4">
                            <h2 class="fw-bold">New Password</h2>
                            <p class="text-muted small mb-0">Set a strong new password for your account</p>
                        </header>

                        <?php if (isset($_SESSION['auth_error'])): ?>
                            <div class="alert alert-danger text-center small py-2 mb-3">
                                <?= e($_SESSION['auth_error']);
                                unset($_SESSION['auth_error']); ?>
                            </div>
                        <?php endif; ?>

                        <form id="resetPasswordForm" action="index.php?page=reset_password" method="POST">
                            <?= csrf_field() ?>
                            <div class="mb-4">
                                <label for="newPassword" class="form-label">New Password</label>
                                <input id="newPassword" type="password" name="new_password" class="form-control" placeholder="••••••••" minlength="8" required>
                            </div>
                            <button type="submit" class="btn btn-auth w-100">Update Password</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </main>
</body>

</html>
