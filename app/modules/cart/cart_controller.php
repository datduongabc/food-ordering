<?php

require_once ROOT_PATH . '/app/modules/cart/cart_service.php';
require_once ROOT_PATH . '/app/modules/order/order_service.php';

class CartController
{
    private $cartService;
    private $orderService;

    public function __construct()
    {
        $this->cartService = new CartService();
        $this->orderService = new OrderService();
    }

    private function isAjax(): bool
    {
        return (
            (!empty($_SERVER['HTTP_X_REQUESTED_WITH']) &&
                strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) === 'xmlhttprequest') ||
            isset($_POST['ajax']) ||
            isset($_GET['ajax'])
        );
    }

    public function handleRequest(): void
    {
        $action = $_GET['action'] ?? 'index';
        $userId = isset($_SESSION['user_id']) ? (int)$_SESSION['user_id'] : null;

        switch ($action) {
            case 'add':
                $productId = (int)($_POST['product_id'] ?? $_GET['product_id'] ?? 0);
                $quantity = (int)($_POST['quantity'] ?? $_GET['quantity'] ?? 1);
                $redirectCart = !empty($_POST['redirect_cart']) || !empty($_GET['redirect_cart']);

                $result = $this->cartService->addToCart($userId, $productId, $quantity);

                if ($this->isAjax()) {
                    header('Content-Type: application/json');
                    echo json_encode($result);
                    exit();
                }

                if ($result['success']) {
                    $_SESSION['flash_success'] = $result['message'];
                } else {
                    $_SESSION['flash_error'] = $result['message'];
                }

                if ($redirectCart) {
                    header("Location: index.php?page=cart");
                } else {
                    $referer = $_SERVER['HTTP_REFERER'] ?? 'index.php?page=cart';
                    header("Location: " . $referer);
                }
                exit();

            case 'update':
                $productId = (int)($_POST['product_id'] ?? 0);
                $quantity = (int)($_POST['quantity'] ?? 1);
                $result = $this->cartService->updateQuantity($userId, $productId, $quantity);

                if ($this->isAjax()) {
                    header('Content-Type: application/json');
                    echo json_encode($result);
                    exit();
                }

                header("Location: index.php?page=cart");
                exit();

            case 'remove':
                $productId = (int)($_POST['product_id'] ?? $_GET['product_id'] ?? 0);
                $result = $this->cartService->removeFromCart($userId, $productId);

                if ($this->isAjax()) {
                    header('Content-Type: application/json');
                    echo json_encode($result);
                    exit();
                }

                $_SESSION['flash_success'] = $result['message'];
                header("Location: index.php?page=cart");
                exit();

            case 'clear':
                $this->cartService->clearCart($userId);
                $_SESSION['flash_success'] = 'Your cart has been cleared.';
                header("Location: index.php?page=cart");
                exit();

            case 'checkout':
                if (!$userId) {
                    $_SESSION['auth_error'] = 'Please sign in to place your order. Your cart items will be saved!';
                    header("Location: index.php?page=signin");
                    exit();
                }

                $paymentMethod = strtoupper(trim((string)($_POST['payment_method'] ?? 'COD')));
                $result = $this->orderService->checkout($userId, $paymentMethod);
                if ($result['success']) {
                    if (($result['payment_method'] ?? 'COD') === 'MOMO') {
                        header("Location: index.php?page=orders&action=momo_pay&order_id=" . (int)$result['order_id']);
                    } else {
                        $_SESSION['flash_success'] = $result['message'];
                        header("Location: index.php?page=orders");
                    }
                } else {
                    $_SESSION['flash_error'] = $result['message'];
                    header("Location: index.php?page=cart");
                }
                exit();

            case 'index':
            default:
                $cartData = $this->cartService->getCartDetails($userId);
                $cartItems = $cartData['items'];
                $totalPrice = $cartData['total_price'];
                $totalCount = $cartData['total_count'];
                include ROOT_PATH . '/app/modules/cart/views/cart.php';
                exit();
        }
    }
}
