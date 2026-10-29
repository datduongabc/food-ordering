<?php

require_once ROOT_PATH . '/app/modules/user/admin_user_model.php';

class AdminUserService
{
    private $userModel;

    public function __construct()
    {
        $this->userModel = new AdminUserModel();
    }

    public function getAllUsersForAdmin()
    {
        $users = $this->userModel->getAllUsers();

        foreach ($users as &$user) {
            $user['role_label'] = (strtoupper($user['role']) === 'ADMIN') ? 'ADMIN' : 'CUSTOMER';
        }
        return $users;
    }

    public function saveUser(array $data, ?int $userId = null, ?int $currentAdminId = null): array
    {
        $name = trim($data['name'] ?? '');
        $email = trim($data['email'] ?? '');
        $phone = trim($data['phone'] ?? '');
        $role = strtoupper(trim($data['role'] ?? 'CUSTOMER')) === 'ADMIN' ? 'ADMIN' : 'CUSTOMER';
        $isVerified = !empty($data['is_email_verified']) ? 1 : 0;
        $password = $data['password'] ?? '';

        if (empty($name) || empty($email) || empty($phone)) {
            return ['success' => false, 'message' => 'Full name, email, and phone are required.'];
        }

        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            return ['success' => false, 'message' => 'Invalid email format.'];
        }

        if (strlen($phone) !== 10 || !ctype_digit($phone)) {
            return ['success' => false, 'message' => 'Phone number must be 10 digits.'];
        }

        if ($userId && $currentAdminId && $userId === $currentAdminId && $role !== 'ADMIN') {
            return ['success' => false, 'message' => 'You cannot demote your own admin account.'];
        }

        if ($userId) {
            $passHash = null;
            if (!empty($password)) {
                if (strlen($password) < 8) {
                    return ['success' => false, 'message' => 'New password must be at least 8 characters.'];
                }
                $passHash = password_hash($password, PASSWORD_DEFAULT);
            }

            $ok = $this->userModel->updateUser($userId, $name, $email, $phone, $role, $isVerified, $passHash);
            return [
                'success' => $ok,
                'message' => $ok
                    ? "User #{$userId} updated successfully."
                    : "Failed to update user (email or phone may already be in use)."
            ];
        } else {
            if (strlen($password) < 8) {
                return ['success' => false, 'message' => 'Password must be at least 8 characters.'];
            }
            $passHash = password_hash($password, PASSWORD_DEFAULT);
            $ok = $this->userModel->createUser($name, $email, $passHash, $phone, $role, $isVerified);
            return [
                'success' => $ok,
                'message' => $ok
                    ? "User \"{$name}\" created successfully."
                    : "Failed to create user (email or phone may already be in use)."
            ];
        }
    }

    public function toggleUserStatus(int $userId, int $currentAdminId): array
    {
        if ($userId === $currentAdminId) {
            return ['success' => false, 'message' => 'You cannot deactivate your own admin account.'];
        }

        $ok = $this->userModel->toggleSoftDelete($userId);
        return [
            'success' => $ok,
            'message' => $ok ? "User #{$userId} status updated." : "Failed to update user status."
        ];
    }
}
