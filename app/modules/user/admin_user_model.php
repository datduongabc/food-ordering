<?php

require_once ROOT_PATH . '/app/core/Database.php';

class AdminUserModel
{
    private $db;

    public function __construct()
    {
        $this->db = Database::getInstance()->getConnection();
    }

    public function getAllUsers()
    {
        $sql = "SELECT * FROM users ORDER BY id ASC";
        $stmt = $this->db->prepare($sql);
        $stmt->execute();
        return $stmt->fetchAll();
    }

    public function getUserById(int $id)
    {
        $stmt = $this->db->prepare("SELECT * FROM users WHERE id = ? LIMIT 1");
        $stmt->execute([$id]);
        return $stmt->fetch();
    }

    public function createUser(
        string $name,
        string $email,
        string $passwordHash,
        string $phone,
        string $role,
        int $isVerified
    ): bool {
        try {
            $verifiedAt = $isVerified ? date('Y-m-d H:i:s') : null;
            $stmt = $this->db->prepare(
                "INSERT INTO users (name, email, password, role, phone, is_email_verified, email_verified_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?)"
            );
            return $stmt->execute([$name, $email, $passwordHash, $role, $phone, $isVerified, $verifiedAt]);
        } catch (PDOException $e) {
            error_log("Admin Create User Error: " . $e->getMessage());
            return false;
        }
    }

    public function updateUser(
        int $id,
        string $name,
        string $email,
        string $phone,
        string $role,
        int $isVerified,
        ?string $passwordHash = null
    ): bool {
        try {
            if ($passwordHash) {
                $stmt = $this->db->prepare(
                    "UPDATE users
                     SET name = ?, email = ?, phone = ?, role = ?, is_email_verified = ?,
                         email_verified_at = CASE WHEN ? = 1 THEN COALESCE(email_verified_at, CURRENT_TIMESTAMP) ELSE NULL END,
                         password = ?
                     WHERE id = ?"
                );
                return $stmt->execute([$name, $email, $phone, $role, $isVerified, $isVerified, $passwordHash, $id]);
            }

            $stmt = $this->db->prepare(
                "UPDATE users
                 SET name = ?, email = ?, phone = ?, role = ?, is_email_verified = ?,
                     email_verified_at = CASE WHEN ? = 1 THEN COALESCE(email_verified_at, CURRENT_TIMESTAMP) ELSE NULL END
                 WHERE id = ?"
            );
            return $stmt->execute([$name, $email, $phone, $role, $isVerified, $isVerified, $id]);
        } catch (PDOException $e) {
            error_log("Admin Update User Error: " . $e->getMessage());
            return false;
        }
    }

    public function toggleSoftDelete(int $id): bool
    {
        $user = $this->getUserById($id);
        if (!$user) {
            return false;
        }

        if ($user['deleted_at'] === null) {
            $stmt = $this->db->prepare("UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?");
        } else {
            $stmt = $this->db->prepare("UPDATE users SET deleted_at = NULL WHERE id = ?");
        }
        return $stmt->execute([$id]);
    }
}
