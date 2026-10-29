<?php

require_once ROOT_PATH . '/app/modules/product/product_service.php';

class AdminProductController
{
    private $adminService;

    public function __construct()
    {
        $this->adminService = new ProductService();
    }

    public function getAllProductsForAdmin()
    {
        return $this->adminService->getProductsForAdmin();
    }

    public function getCategories(): array
    {
        return $this->adminService->getCategories();
    }

    public function getLocations(): array
    {
        return $this->adminService->getLocations();
    }

    public function handleAction(): void
    {
        if (!isset($_SESSION['role']) || $_SESSION['role'] !== 'ADMIN') {
            header("Location: index.php?page=signin");
            exit();
        }

        $action = $_GET['action'] ?? '';
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            if ($action === 'create') {
                $res = $this->adminService->saveProduct($_POST, $_FILES['image_file'] ?? null, null);
                $_SESSION[$res['success'] ? 'admin_success' : 'admin_error'] = $res['message'];
            } elseif ($action === 'update') {
                $id = (int)($_POST['product_id'] ?? 0);
                $res = $this->adminService->saveProduct($_POST, $_FILES['image_file'] ?? null, $id);
                $_SESSION[$res['success'] ? 'admin_success' : 'admin_error'] = $res['message'];
            } elseif ($action === 'toggle_delete') {
                $id = (int)($_POST['product_id'] ?? 0);
                $res = $this->adminService->toggleProductStatus($id);
                $_SESSION[$res['success'] ? 'admin_success' : 'admin_error'] = $res['message'];
            }
            header("Location: index.php?page=admin_products");
            exit();
        }
    }
}
