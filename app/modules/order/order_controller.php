<?php

require_once ROOT_PATH . '/app/modules/order/order_service.php';
require_once ROOT_PATH . '/app/modules/order/momo_service.php';
require_once ROOT_PATH . '/app/modules/reservation/reservation_service.php';

class OrderController
{
    private $orderService;
    private $momoService;
    private $reservationService;

    public function __construct()
    {
        $this->orderService = new OrderService();
        $this->momoService = new MomoService();
        $this->reservationService = new ReservationService();
    }

    public function handleRequest(): void
    {
        if (!isset($_SESSION['user_id'])) {
            $_SESSION['auth_error'] = 'Please sign in to view your orders.';
            header("Location: index.php?page=signin");
            exit();
        }

        $userId = (int)$_SESSION['user_id'];
        $action = $_GET['action'] ?? 'index';

        if ($action === 'momo_pay') {
            $orderId = (int)($_GET['order_id'] ?? $_POST['order_id'] ?? 0);
            $paymentIntent = $this->momoService->createPaymentIntent($userId, $orderId);
            if (!$paymentIntent['success']) {
                $_SESSION['flash_error'] = $paymentIntent['message'];
                header("Location: index.php?page=orders");
                exit();
            }

            include ROOT_PATH . '/app/modules/order/views/momo_payment.php';
            exit();
        }

        if ($action === 'momo_return' || $action === 'momo_ipn') {
            $params = array_merge($_GET, $_POST);
            $result = $this->momoService->handleCallback($userId, $params);
            if ($result['success']) {
                $_SESSION['flash_success'] = $result['message'];
            } else {
                $_SESSION['flash_error'] = $result['message'];
            }
            header("Location: index.php?page=orders");
            exit();
        }

        if ($action === 'cancel' && $_SERVER['REQUEST_METHOD'] === 'POST') {
            $orderId = (int)($_POST['order_id'] ?? 0);
            $result = $this->orderService->cancelOrder($userId, $orderId);
            if ($result['success']) {
                $_SESSION['flash_success'] = $result['message'];
            } else {
                $_SESSION['flash_error'] = $result['message'];
            }
            header("Location: index.php?page=orders");
            exit();
        }

        $orders = $this->orderService->getUserOrders($userId);
        $reservations = $this->reservationService->getUserReservations($userId);
        $activeTab = ($_GET['tab'] ?? 'orders') === 'reservations' ? 'reservations' : 'orders';

        include ROOT_PATH . '/app/modules/order/views/orders.php';
        exit();
    }
}
