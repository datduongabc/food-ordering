<?php

require_once ROOT_PATH . '/app/modules/menu/menu_service.php';

class MenuDetailController
{
    private $menuDetailService;

    public function __construct()
    {
        $this->menuDetailService = new MenuDetailService();
    }

    public function showDetail()
    {
        $slug = trim($_GET['slug'] ?? '');
        $action = $_GET['action'] ?? '';

        if ($action === 'review' && $_SERVER['REQUEST_METHOD'] === 'POST') {
            if (!isset($_SESSION['user_id'])) {
                $_SESSION['auth_error'] = 'Please sign in to write a review.';
                header("Location: index.php?page=signin");
                exit();
            }

            $productId = (int)($_POST['product_id'] ?? 0);
            $rating = (int)($_POST['rating'] ?? 5);
            $comment = $_POST['comment'] ?? '';

            $res = $this->menuDetailService->submitReview((int)$_SESSION['user_id'], $productId, $rating, $comment);
            if ($res['success']) {
                $_SESSION['flash_success'] = $res['message'];
            } else {
                $_SESSION['flash_error'] = $res['message'];
            }
            header("Location: index.php?page=detail&slug=" . urlencode($slug) . "#reviews-section");
            exit();
        }

        $product = $this->menuDetailService->getProductDetail($slug);
        include ROOT_PATH . '/app/modules/menu/views/menu_detail.php';
        exit();
    }
}
