<?php

/**
 * Central Router for DaTeNO Restaurant MVC Architecture
 * Supports query-based routing (?page=...&action=...) with lazy controller instantiation
 * and role-based access control.
 */
class Router
{
    public function dispatch(): void
    {
        require_once ROOT_PATH . '/app/modules/auth/auth_controller.php';
        $authController = new AuthController();

        // Automatically authenticate via Remember Me token if session not active
        $authController->signInWithToken();

        $page = trim($_GET['page'] ?? '');
        $action = trim($_GET['action'] ?? '');

        // Enforce CSRF protection on every state-changing request
        if ($_SERVER['REQUEST_METHOD'] === 'POST' && !verify_csrf()) {
            http_response_code(419);
            if (!empty($_SERVER['HTTP_X_REQUESTED_WITH'])) {
                header('Content-Type: application/json');
                echo json_encode(['success' => false, 'message' => 'Session expired. Please reload the page and try again.']);
            } else {
                $_SESSION['flash_error'] = 'Your session has expired. Please try again.';
                header('Location: ' . ($_SERVER['HTTP_REFERER'] ?? 'index.php'));
            }
            exit();
        }

        // Backward-compatible Reservation POST handling on home/main
        if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($page === 'home' || $page === 'main')) {
            require_once ROOT_PATH . '/app/modules/reservation/reservation_controller.php';
            (new ReservationController())->createReservation();
            return;
        }

        switch ($page) {
            // --- Authentication Module ---
            case 'signup':
                $authController->signUp();
                break;

            case 'signin':
                $authController->signIn();
                break;

            case 'signout':
                $authController->signOut();
                break;

            case 'forgot_password':
                $authController->forgotPassword();
                break;

            case 'change_password':
                $authController->changePassword();
                break;

            case 'secure_token':
                $authController->secureToken();
                break;

            case 'reset_password':
                $authController->resetPassword();
                break;

            case 'verify_email':
                $authController->verifyEmailRequest();
                break;

            // --- Menu Detail & Review Module ---
            case 'detail':
                require_once ROOT_PATH . '/app/modules/menu/menu_controller.php';
                (new MenuDetailController())->showDetail();
                break;

            // --- AJAX Product Sort & Pagination ---
            case 'product_sort':
                require_once ROOT_PATH . '/app/modules/product/product_controller.php';
                $p = isset($_GET['p']) ? max(1, (int)$_GET['p']) : 1;
                $limit = 12;
                $sort = $_GET['sort'] ?? 'default';

                $productController = new ProductController();
                $data = $productController->getProductsPaginated($p, $limit, $sort);

                $products = $data['products'];
                $current_page = $data['current_page'];
                $total_pages = $data['total_pages'];

                include ROOT_PATH . '/app/modules/product/views/menu_list_pagination.php';
                exit();

            // --- AJAX Live Search ---
            case 'product_search':
                include ROOT_PATH . '/public/api/search.php';
                exit();

            // --- Cart Module ---
            case 'cart':
                require_once ROOT_PATH . '/app/modules/cart/cart_controller.php';
                (new CartController())->handleRequest();
                break;

            // --- Customer Orders & Bookings Module ---
            case 'orders':
                require_once ROOT_PATH . '/app/modules/order/order_controller.php';
                (new OrderController())->handleRequest();
                break;

            // --- Reservation Module ---
            case 'reservation':
                require_once ROOT_PATH . '/app/modules/reservation/reservation_controller.php';
                $resController = new ReservationController();
                if ($action === 'cancel') {
                    $resController->cancelMyReservation();
                } else {
                    $resController->createReservation();
                }
                break;

            // --- Admin Routes (RBAC Protected) ---
            case 'admin_dashboard':
            case 'admin_products':
            case 'admin_orders':
            case 'admin_reservations':
            case 'admin_users':
                $this->requireAdmin();
                $this->dispatchAdmin($page);
                break;

            // --- Home / Storefront ---
            case 'home':
            default:
                if (
                    isset($_SESSION['role']) &&
                    $_SESSION['role'] === 'ADMIN' &&
                    $page === '' &&
                    ($_GET['view'] ?? '') !== 'store'
                ) {
                    $this->dispatchAdmin('admin_dashboard');
                } else {
                    $this->renderCustomerHome();
                }
                break;
        }
    }

    private function requireAdmin(): void
    {
        if (!isset($_SESSION['role']) || $_SESSION['role'] !== 'ADMIN') {
            $_SESSION['auth_error'] = 'Administrator access required.';
            header("Location: index.php?page=signin");
            exit();
        }
    }

    private function dispatchAdmin(string $page): void
    {
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            switch ($page) {
                case 'admin_products':
                    require_once ROOT_PATH . '/app/modules/product/admin_product_controller.php';
                    (new AdminProductController())->handleAction();
                    break;
                case 'admin_orders':
                    require_once ROOT_PATH . '/app/modules/order/admin_order_controller.php';
                    (new AdminOrderController())->handleAction();
                    break;
                case 'admin_reservations':
                    require_once ROOT_PATH . '/app/modules/reservation/admin_reservation_controller.php';
                    (new AdminReservationController())->handleAction();
                    break;
                case 'admin_users':
                    require_once ROOT_PATH . '/app/modules/user/admin_user_controller.php';
                    (new AdminUserController())->handleAction();
                    break;
            }
        }

        // Preload view data cleanly before rendering admin layout
        switch ($page) {
            case 'admin_products':
                require_once ROOT_PATH . '/app/modules/product/admin_product_controller.php';
                $ctrl = new AdminProductController();
                $products = $ctrl->getAllProductsForAdmin();
                $categories = $ctrl->getCategories();
                $locations = $ctrl->getLocations();
                break;

            case 'admin_orders':
                require_once ROOT_PATH . '/app/modules/order/admin_order_controller.php';
                $ctrl = new AdminOrderController();
                $orders = $ctrl->getAllOrdersForAdmin($_GET['status'] ?? null);
                break;

            case 'admin_reservations':
                require_once ROOT_PATH . '/app/modules/reservation/admin_reservation_controller.php';
                $ctrl = new AdminReservationController();
                $reservations = $ctrl->getAllReservationsForAdmin($_GET['status'] ?? null);
                break;

            case 'admin_users':
                require_once ROOT_PATH . '/app/modules/user/admin_user_controller.php';
                $ctrl = new AdminUserController();
                $users = $ctrl->getAllUsersForAdmin();
                break;

            case 'admin_dashboard':
            default:
                require_once ROOT_PATH . '/app/modules/order/admin_order_controller.php';
                require_once ROOT_PATH . '/app/modules/reservation/admin_reservation_controller.php';
                $orderCtrl = new AdminOrderController();
                $resCtrl = new AdminReservationController();
                $stats = $orderCtrl->getDashboardStats();
                $recentOrders = array_slice($orderCtrl->getAllOrdersForAdmin(), 0, 5);
                $recentReservations = array_slice($resCtrl->getAllReservationsForAdmin(), 0, 5);
                break;
        }

        include ROOT_PATH . '/app/modules/user/views/admin_page.php';
        exit();
    }

    private function renderCustomerHome(): void
    {
        require_once ROOT_PATH . '/app/modules/product/product_controller.php';
        require_once ROOT_PATH . '/app/modules/feedback/feedback_controller.php';
        require_once ROOT_PATH . '/app/modules/reservation/reservation_controller.php';

        $productController = new ProductController();
        $feedbackController = new FeedbackController();
        $reservationController = new ReservationController();

        $highest_rating_item = $productController->getHighestRating();

        $p = isset($_GET['p']) ? max(1, (int)$_GET['p']) : 1;
        $limit = 12;
        $sort = $_GET['sort'] ?? 'default';
        $menuData = $productController->getProductsPaginated($p, $limit, $sort);
        $products = $menuData['products'];
        $current_page = $menuData['current_page'];
        $total_pages = $menuData['total_pages'];

        $feedbacks = $feedbackController->getTopFeedback();
        $locations = $reservationController->getLocations();

        include ROOT_PATH . '/app/modules/user/views/customer_page.php';
        exit();
    }
}
