<?php

require_once ROOT_PATH . '/app/modules/order/order_model.php';
require_once ROOT_PATH . '/app/modules/cart/cart_service.php';

class OrderService
{
    private $orderModel;
    private $cartService;

    public function __construct()
    {
        $this->orderModel = new OrderModel();
        $this->cartService = new CartService();
    }

    private function formatImagePath($categorySlug, $imageName): string
    {
        $categorySlug = $categorySlug ?: 'starters';
        return base_url("images/{$categorySlug}/{$imageName}");
    }

    public function checkout(int $userId, string $paymentMethod = 'COD'): array
    {
        $paymentMethod = strtoupper(trim($paymentMethod)) === 'MOMO' ? 'MOMO' : 'COD';
        $cartDetails = $this->cartService->getCartDetails($userId);

        if (empty($cartDetails['items'])) {
            return [
                'success' => false,
                'message' => 'Your cart is empty. Please add dishes before placing an order.'
            ];
        }

        $orderId = $this->orderModel->createOrderFromItems($userId, $cartDetails['items'], $paymentMethod);
        if (!$orderId) {
            return [
                'success' => false,
                'message' => 'Could not place your order. Please try again.'
            ];
        }

        return [
            'success' => true,
            'order_id' => $orderId,
            'payment_method' => $paymentMethod,
            'message' => $paymentMethod === 'MOMO'
                ? "Order #{$orderId} created. Proceeding to MoMo Payment Gateway..."
                : "Order #{$orderId} placed successfully! Thank you for dining with DaTeNO."
        ];
    }

    public function getUserOrders(int $userId): array
    {
        $orders = $this->orderModel->getOrdersByUserId($userId);
        foreach ($orders as &$order) {
            foreach ($order['items'] as &$item) {
                $item['image_path'] = $this->formatImagePath(
                    $item['category_slug'] ?? 'starters',
                    $item['image_url'] ?? ''
                );
            }
        }
        return $orders;
    }

    public function cancelOrder(int $userId, int $orderId): array
    {
        if ($orderId <= 0) {
            return ['success' => false, 'message' => 'Invalid order ID.'];
        }

        $cancelled = $this->orderModel->cancelUserOrder($userId, $orderId);
        if (!$cancelled) {
            return [
                'success' => false,
                'message' => 'Order cannot be cancelled (only PENDING orders can be cancelled).'
            ];
        }

        return [
            'success' => true,
            'message' => "Order #{$orderId} has been cancelled."
        ];
    }

    public function getOrdersForAdmin(?string $status = null): array
    {
        $orders = $this->orderModel->getAllOrdersForAdmin($status);
        foreach ($orders as &$order) {
            foreach ($order['items'] as &$item) {
                $item['image_path'] = $this->formatImagePath(
                    $item['category_slug'] ?? 'starters',
                    $item['image_url'] ?? ''
                );
            }
        }
        return $orders;
    }

    public function updateOrderStatus(int $orderId, string $status): array
    {
        $updated = $this->orderModel->updateOrderStatus($orderId, $status);
        return [
            'success' => $updated,
            'message' => $updated ? "Order #{$orderId} status updated to {$status}." : "Failed to update order status."
        ];
    }

    public function deleteOrder(int $orderId): array
    {
        $deleted = $this->orderModel->deleteOrder($orderId);
        return [
            'success' => $deleted,
            'message' => $deleted ? "Order #{$orderId} deleted." : "Failed to delete order."
        ];
    }

    public function getDashboardStats(): array
    {
        return $this->orderModel->getDashboardSummary();
    }
}
