<?php

require_once ROOT_PATH . '/app/modules/order/order_service.php';

class AdminOrderController
{
    private $orderService;

    public function __construct()
    {
        $this->orderService = new OrderService();
    }

    public function getAllOrdersForAdmin(?string $status = null): array
    {
        return $this->orderService->getOrdersForAdmin($status);
    }

    public function getDashboardStats(): array
    {
        return $this->orderService->getDashboardStats();
    }

    public function handleAction(): void
    {
        if (!isset($_SESSION['role']) || $_SESSION['role'] !== 'ADMIN') {
            header("Location: index.php?page=signin");
            exit();
        }

        $action = $_GET['action'] ?? '';
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            if ($action === 'update_status') {
                $orderId = (int)($_POST['order_id'] ?? 0);
                $status = trim($_POST['status'] ?? '');
                $res = $this->orderService->updateOrderStatus($orderId, $status);
                $_SESSION[$res['success'] ? 'admin_success' : 'admin_error'] = $res['message'];
            } elseif ($action === 'delete') {
                $orderId = (int)($_POST['order_id'] ?? 0);
                $res = $this->orderService->deleteOrder($orderId);
                $_SESSION[$res['success'] ? 'admin_success' : 'admin_error'] = $res['message'];
            }
            header("Location: index.php?page=admin_orders");
            exit();
        }
    }
}
