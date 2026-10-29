<?php

require_once ROOT_PATH . '/app/modules/auth/auth_service.php';

class AuthController
{
    private $authService;

    public function __construct()
    {
        $this->authService = new AuthService();
    }

    /**
     * Populate user session and merge any guest cart items into database cart
     */
    private function setUserSession(array $userInfo): void
    {
        // Prevent session fixation: issue a fresh session ID on privilege change
        if (session_status() === PHP_SESSION_ACTIVE && !headers_sent()) {
            session_regenerate_id(true);
        }

        $_SESSION['user_id'] = $userInfo['id'];
        $_SESSION['name'] = $userInfo['name'];
        $_SESSION['email'] = $userInfo['email'] ?? '';
        $_SESSION['phone'] = $userInfo['phone'] ?? '';
        $_SESSION['role'] = $userInfo['role'];
        $_SESSION['is_email_verified'] = (int)$userInfo['is_email_verified'];

        // Merge guest cart into DB cart if present
        if (!empty($_SESSION['guest_cart']) && is_array($_SESSION['guest_cart'])) {
            if (file_exists(ROOT_PATH . '/app/modules/cart/cart_service.php')) {
                require_once ROOT_PATH . '/app/modules/cart/cart_service.php';
                $cartService = new CartService();
                $cartService->mergeGuestCartToUser((int)$userInfo['id'], $_SESSION['guest_cart']);
                unset($_SESSION['guest_cart']);
            }
        }
    }

    // Sign up
    public function signUp()
    {
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            $name     = trim($_POST['name'] ?? '');
            $email    = trim($_POST['email'] ?? '');
            $password = $_POST['password'] ?? '';
            $phone    = trim($_POST['phone'] ?? '');

            $result = $this->authService->signUpLogic($name, $email, $password, $phone);

            if ($result['success']) {
                $_SESSION['auth_success'] = $result['message'];
                header("Location: index.php?page=signin");
            } else {
                $_SESSION['auth_error'] = $result['message'];
                header("Location: index.php?page=signup");
            }
            exit();
        }

        require_once ROOT_PATH . '/app/modules/auth/views/sign_up.php';
    }

    // Sign in
    public function signIn()
    {
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            $email       = trim($_POST['email'] ?? '');
            $password    = $_POST['password'] ?? '';
            $remember_me = isset($_POST['remember']);

            $result = $this->authService->signInLogic($email, $password);

            if ($result['success']) {
                $this->setUserSession($result['userInfo']);

                if ($remember_me) {
                    $this->authService->rememberMeLogic($result['userInfo']['id']);
                }

                $_SESSION['auth_success'] = $result['message'];
                if ($result['userInfo']['role'] === 'ADMIN') {
                    header("Location: index.php?page=admin_dashboard");
                } else {
                    header("Location: index.php");
                }
            } else {
                $_SESSION['auth_error'] = $result['message'];
                header("Location: index.php?page=signin");
            }
            exit();
        }

        require_once ROOT_PATH . '/app/modules/auth/views/sign_in.php';
    }

    // Auto sign in if user has valid remember_me cookie
    public function signInWithToken()
    {
        if (!isset($_SESSION['user_id']) && isset($_COOKIE['remember_me'])) {
            $result = $this->authService->signInWithToken($_COOKIE['remember_me']);

            if ($result["success"]) {
                $this->setUserSession($result['userInfo']);
            }
        }
    }

    // Sign out
    public function signOut()
    {
        if (isset($_COOKIE['remember_me'])) {
            $this->authService->revokeToken($_COOKIE['remember_me']);
            setcookie('remember_me', '', time() - 3600, '/');
        }

        session_unset();
        session_regenerate_id(true);
        header("Location: index.php?page=signin");
        exit();
    }

    // Forgot password
    public function forgotPassword()
    {
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            $email = trim($_POST['email'] ?? '');

            $result = $this->authService->initiateSecureProcess($email, 'FORGOT_PASSWORD');

            if (!$result['success']) {
                $_SESSION['auth_error'] = $result['message'];
                header("Location: index.php?page=forgot_password");
                exit();
            }

            $_SESSION["email"] = $email;
            $_SESSION["auth_type"] = 'FORGOT_PASSWORD';
            header("Location: index.php?page=secure_token");
            exit();
        }

        require_once ROOT_PATH . '/app/modules/auth/views/forgot_password.php';
    }

    public function secureToken()
    {
        if (!isset($_SESSION['email']) || !isset($_SESSION['auth_type'])) {
            header("Location: index.php?page=forgot_password");
            exit();
        }

        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            $email = $_SESSION["email"] ?? '';
            $type = $_SESSION["auth_type"] ?? '';
            $plain_token = trim($_POST['secure_token'] ?? '');

            $result = $this->authService->validateToken($email, $plain_token, $type);

            if ($result["message"] === "Too many attempts.") {
                $_SESSION['auth_error'] = "Too many failed attempts. Please request a new token.";
                header("Location: index.php?page=forgot_password");
                exit();
            }

            if (!$result["success"]) {
                $_SESSION['auth_error'] = $result['message'];
                header("Location: index.php?page=secure_token");
                exit();
            }

            $_SESSION['token_verified'] = true;

            if ($type === 'EMAIL_VERIFICATION') {
                $verifyResult = $this->authService->verifyEmailLogic($email);

                if ($verifyResult['success']) {
                    $_SESSION['is_email_verified'] = 1;
                    unset($_SESSION['email'], $_SESSION['auth_type'], $_SESSION['token_verified']);
                    $_SESSION['flash_success'] = "Your email has been verified successfully!";
                    header("Location: index.php");
                } else {
                    $_SESSION['auth_error'] = $verifyResult['message'];
                    header("Location: index.php?page=secure_token");
                }
            } else {
                // FORGOT_PASSWORD or CHANGE_PASSWORD
                header("Location: index.php?page=reset_password");
            }
            exit();
        }

        require_once ROOT_PATH . '/app/modules/auth/views/secure_token.php';
    }

    public function resetPassword()
    {
        if (!isset($_SESSION['email']) || !isset($_SESSION['auth_type']) || !isset($_SESSION['token_verified'])) {
            header("Location: index.php?page=forgot_password");
            exit();
        }

        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            $email = $_SESSION['email'];
            $type = $_SESSION['auth_type'] ?? '';
            $new_password = $_POST['new_password'] ?? '';

            $result = $this->authService->createNewPassword($email, $new_password, $type);

            if ($result['success']) {
                unset($_SESSION['email'], $_SESSION['auth_type'], $_SESSION['token_verified']);
                $_SESSION['auth_success'] = "Password updated successfully. Please log in again.";
                header("Location: index.php?page=signin");
            } else {
                $_SESSION['auth_error'] = $result['message'];
                header("Location: index.php?page=reset_password");
            }
            exit();
        }

        require_once ROOT_PATH . '/app/modules/auth/views/reset_password.php';
    }

    public function changePassword()
    {
        if (!isset($_SESSION['user_id'])) {
            $_SESSION['auth_error'] = "Cannot change password without logging in.";
            header("Location: index.php?page=signin");
            exit();
        }

        $userInfo = $this->authService->getUserInfoById($_SESSION['user_id']);
        $email = $userInfo['email'] ?? '';
        $result = $this->authService->initiateSecureProcess($email, 'CHANGE_PASSWORD');

        if (!$result['success']) {
            $_SESSION['flash_error'] = $result['message'];
            header("Location: index.php");
            exit();
        }

        $_SESSION["email"] = $email;
        $_SESSION["auth_type"] = 'CHANGE_PASSWORD';

        header("Location: index.php?page=secure_token");
        exit();
    }

    public function verifyEmailRequest()
    {
        if (!isset($_SESSION['user_id'])) {
            header("Location: index.php?page=signin");
            exit();
        }

        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            $userInfo = $this->authService->getUserInfoById($_SESSION['user_id']);
            $email = $userInfo['email'] ?? '';
            $result = $this->authService->initiateSecureProcess($email, 'EMAIL_VERIFICATION');

            if ($result['success']) {
                $_SESSION['email'] = $email;
                $_SESSION['auth_type'] = 'EMAIL_VERIFICATION';

                header("Location: index.php?page=secure_token");
                exit();
            } else {
                $_SESSION['auth_error'] = $result["message"];
                header("Location: index.php?page=verify_email");
                exit();
            }
        }

        require_once ROOT_PATH . '/app/modules/auth/views/verify_email.php';
    }
}
