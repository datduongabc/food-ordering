<?php

/**
 * Global Helper Functions for DaTeNO Restaurant Application
 */

if (!defined('BASE_URL')) {
    $scriptDir = str_replace('\\', '/', dirname($_SERVER['SCRIPT_NAME'] ?? ''));
    define('BASE_URL', rtrim($scriptDir, '/'));
}

/**
 * Build a full URL relative to the public front controller
 */
function base_url(string $path = ''): string
{
    $path = ltrim($path, '/');
    if ($path === '') {
        return BASE_URL !== '' ? BASE_URL . '/' : '/';
    }
    $url = (BASE_URL !== '' ? BASE_URL : '') . '/' . $path;

    // Cache-busting: static assets are served with long-lived "immutable" cache headers,
    // so append the file's modification time to force browsers to fetch updated CSS/JS.
    if (preg_match('/\.(css|js)$/i', $path) && defined('ROOT_PATH')) {
        $file = ROOT_PATH . '/public/' . $path;
        if (is_file($file)) {
            $url .= '?v=' . filemtime($file);
        }
    }
    return $url;
}

/**
 * Escape HTML output to prevent XSS
 */
function e($value): string
{
    return htmlspecialchars((string)($value ?? ''), ENT_QUOTES, 'UTF-8');
}

/**
 * Format price consistently in USD ($12.50)
 */
function format_price($amount): string
{
    return '$' . number_format((float)$amount, 2);
}

/**
 * Generate or retrieve CSRF token in current session
 */
function csrf_token(): string
{
    if (empty($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf_token'];
}

/**
 * Output hidden CSRF input field for forms
 */
function csrf_field(): string
{
    return '<input type="hidden" name="csrf_token" value="' . e(csrf_token()) . '">';
}

/**
 * Verify CSRF token on POST requests (returns true if valid or if token not enforced on legacy forms)
 */
function verify_csrf(): bool
{
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        return true;
    }
    $token = $_POST['csrf_token'] ?? $_SERVER['HTTP_X_CSRF_TOKEN'] ?? null;
    if ($token === null) {
        return false;
    }
    return hash_equals(csrf_token(), (string)$token);
}

/**
 * Whether the app runs in local/sandbox mode (APP_ENV=local).
 * Sandbox-only conveniences (on-screen OTP, simulated MoMo callbacks) are enabled ONLY in this mode.
 */
function app_is_local(): bool
{
    $env = $_ENV['APP_ENV'] ?? getenv('APP_ENV') ?: 'production';
    return strtolower(trim((string)$env)) === 'local';
}

/**
 * Get total items count in the cart (Database for logged-in user, Session for guest)
 */
function get_cart_count(): int
{
    if (isset($_SESSION['user_id'])) {
        try {
            $db = Database::getInstance()->getConnection();
            $stmt = $db->prepare("SELECT COALESCE(SUM(quantity), 0) FROM cart_items WHERE user_Id = ?");
            $stmt->execute([(int)$_SESSION['user_id']]);
            return (int)$stmt->fetchColumn();
        } catch ( Exception $e ) {
            return 0;
        }
    }

    if (!empty($_SESSION['guest_cart']) && is_array($_SESSION['guest_cart'])) {
        return (int)array_sum($_SESSION['guest_cart']);
    }

    return 0;
}
