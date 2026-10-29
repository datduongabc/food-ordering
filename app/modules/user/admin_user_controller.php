<?php

require_once ROOT_PATH . '/app/modules/user/admin_user_service.php';

class AdminUserController
{
    private $adminService;

    public function __construct()
    {
        $this->adminService = new AdminUserService();
    }

    public function getAllUsersForAdmin()
    {
        if (isset($_SESSION['role']) && $_SESSION['role'] === 'ADMIN') {
            return $this->adminService->getAllUsersForAdmin();
        }
        return [];
    }

    public function handleAction(): void
    {
        if (!isset($_SESSION['role']) || $_SESSION['role'] !== 'ADMIN') {
            header("Location: index.php?page=signin");
            exit();
        }

        $action = $_GET['action'] ?? '';
        $currentAdminId = (int)($_SESSION['user_id'] ?? 0);

        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            if ($action === 'create') {
                $res = $this->adminService->saveUser($_POST, null, $currentAdminId);
                $_SESSION[$res['success'] ? 'admin_success' : 'admin_error'] = $res['message'];
            } elseif ($action === 'update') {
                $id = (int)($_POST['user_id'] ?? 0);
                $res = $this->adminService->saveUser($_POST, $id, $currentAdminId);
                $_SESSION[$res['success'] ? 'admin_success' : 'admin_error'] = $res['message'];
            } elseif ($action === 'toggle_delete') {
                $id = (int)($_POST['user_id'] ?? 0);
                $res = $this->adminService->toggleUserStatus($id, $currentAdminId);
                $_SESSION[$res['success'] ? 'admin_success' : 'admin_error'] = $res['message'];
            }
            header("Location: index.php?page=admin_users");
            exit();
        }
    }
}
