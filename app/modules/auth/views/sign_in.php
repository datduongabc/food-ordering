<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign In - DaTeNO Restaurant</title>
    <!-- CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="<?= base_url('css/auth/auth.css') ?>">
    <!-- JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js" defer></script>
    <script src="<?= base_url('js/auth/sign_in.js') ?>" defer></script>
</head>

<body>
    <main class="auth-wrapper">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-12 col-md-6 col-lg-5">
                    <div class="auth-card shadow-lg">
                        <header class="text-center mb-4">
                            <a href="index.php" class="text-decoration-none d-inline-flex align-items-center gap-2 mb-2">
                                <span class="brand-icon-badge" style="width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg, #d9381e, #f59e0b);color:#fff;display:inline-flex;align-items:center;justify-content:center;"><i class="bi bi-fire"></i></span>
                                <span class="fs-3 fw-bold"><span style="color: #d9381e;">DaT</span><span style="color: #1f1712;">eNO</span></span>
                            </a>
                            <h2 class="fw-bold">Welcome Back</h2>
                            <p class="text-muted small mb-0">Please enter your details to sign in</p>
                        </header>

                        <?php if (isset($_SESSION['auth_success']) || isset($_SESSION['auth_error'])): ?>
                            <div class="mb-3">
                                <div class="alert alert-<?= isset($_SESSION['auth_success']) ? 'success' : 'danger' ?> text-center small py-2 mb-0">
                                    <?= e($_SESSION['auth_success'] ?? $_SESSION['auth_error']) ?>
                                    <?php unset($_SESSION['auth_success'], $_SESSION['auth_error']); ?>
                                </div>
                            </div>
                        <?php endif; ?>

                        <form id="signinForm" action="index.php?page=signin" method="POST">
                            <?= csrf_field() ?>
                            <div class="mb-3">
                                <label for="email" class="form-label">Email Address</label>
                                <input id="email" type="email" name="email" class="form-control" placeholder="example@mail.com" required>
                            </div>

                            <div class="mb-3">
                                <div class="d-flex justify-content-between align-items-center mb-1">
                                    <label for="password" class="form-label mb-0">Password</label>
                                    <a href="index.php?page=forgot_password" class="auth-link small">Forgot password?</a>
                                </div>
                                <div class="password-field">
                                    <input id="password" type="password" name="password" class="form-control" placeholder="••••••••" minlength="8" required>
                                    <i class="fa-solid fa-eye toggle-password" id="togglePasswordIcon"></i>
                                </div>
                            </div>

                            <div class="mb-4 form-check">
                                <input id="remember" type="checkbox" name="remember" class="form-check-input">
                                <label for="remember" class="form-check-label small text-muted">Remember me for 7 days</label>
                            </div>

                            <button type="submit" class="btn btn-auth w-100">Sign In</button>
                        </form>

                        <footer class="text-center mt-4">
                            <div class="mb-2">
                                <span class="small text-muted">Don't have an account?
                                    <a href="index.php?page=signup" class="auth-link">Sign Up</a>
                                </span>
                            </div>
                            <a href="index.php?page=home" class="small text-muted text-decoration-none">
                                <i class="bi bi-arrow-left me-1"></i>Back to Restaurant Menu
                            </a>
                        </footer>
                    </div>
                </div>
            </div>
        </div>
    </main>
</body>

</html>
