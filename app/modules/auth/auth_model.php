<?php

require_once ROOT_PATH . '/app/core/Database.php';

class AuthModel
{
    private $db;

    public function __construct()
    {
        $this->db = Database::getInstance()->getConnection();
    }

    public function checkDuplicateInfo($email, $phone)
    {
        try {
            $stmt = $this->db->prepare(
                "SELECT email, phone
                FROM users
                WHERE (email = ? OR phone = ?) AND deleted_at IS NULL
                LIMIT 1"
            );
            $stmt->execute([$email, $phone]);
            return $stmt->fetch();
        } catch (PDOException $e) {
            return false;
        }
    }

    public function createNewUser($name, $email, $password, $phone)
    {
        try {
            $stmt = $this->db->prepare(
                "INSERT INTO users (name, email, password, phone)
                VALUES (?, ?, ?, ?)"
            );
            return $stmt->execute([$name, $email, $password, $phone]);
        } catch (PDOException $e) {
            return false;
        }
    }

    public function getUserRecord($email)
    {
        try {
            $stmt = $this->db->prepare(
                "SELECT *
                FROM users
                WHERE email = ? AND deleted_at IS NULL
                LIMIT 1"
            );
            $stmt->execute([$email]);
            $user = $stmt->fetch();
            return [
                "success" => (bool)$user,
                "user_record" => $user ?: null
            ];
        } catch (PDOException $e) {
            return [
                "success" => false,
                "user_record" => null,
                "message" => $e->getMessage()
            ];
        }
    }

    public function saveTokenData($user_id, $token, $type, $expired_at)
    {
        try {
            $this->deleteToken($user_id, $type);

            $driver = $this->db->getAttribute(PDO::ATTR_DRIVER_NAME);
            if ($driver === 'pgsql') {
                $sql = "INSERT INTO password_resets(user_id, token, type, expired_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP + (? * INTERVAL '1 minute'))";
            } elseif ($driver === 'sqlite') {
                $sql = "INSERT INTO password_resets(user_id, token, type, expired_at)
                        VALUES (?, ?, ?, datetime('now', '+' || ? || ' minutes'))";
            } else {
                $sql = "INSERT INTO password_resets(user_id, token, type, expired_at)
                        VALUES (?, ?, ?, DATE_ADD(NOW(), INTERVAL ? MINUTE))";
            }

            $stmt = $this->db->prepare($sql);
            return $stmt->execute([$user_id, $token, $type, (int)$expired_at]);
        } catch (PDOException $e) {
            return false;
        }
    }

    public function autoLoginWithCookie($hash_token)
    {
        try {
            $stmt = $this->db->prepare(
                "SELECT u.*
                FROM users u
                JOIN password_resets pr ON u.id = pr.user_id
                WHERE pr.token = ? AND pr.type = 'REMEMBER_ME' AND pr.expired_at > CURRENT_TIMESTAMP AND u.deleted_at IS NULL
                LIMIT 1"
            );

            $stmt->execute([$hash_token]);
            $user = $stmt->fetch();

            return [
                "success" => (bool)$user,
                "user_record" => $user ?: null
            ];
        } catch (PDOException $e) {
            return [
                "success" => false,
                "user_record" => null,
                "message" => $e->getMessage()
            ];
        }
    }

    public function deleteTokenByValue($hash, $type)
    {
        try {
            $stmt = $this->db->prepare(
                "DELETE FROM password_resets
                WHERE token = ? AND type = ?"
            );

            return $stmt->execute([$hash, $type]);
        } catch (PDOException $e) {
            return false;
        }
    }

    public function getAttempts($user_id, $type)
    {
        try {
            $stmt = $this->db->prepare(
                "SELECT attempts
                FROM password_resets
                WHERE user_id = ? AND type = ?
                LIMIT 1"
            );

            $stmt->execute([$user_id, $type]);
            return $stmt->fetch();
        } catch (PDOException $e) {
            return false;
        }
    }

    public function getValidToken($user_id, $type)
    {
        try {
            $stmt = $this->db->prepare(
                "SELECT token
                FROM password_resets
                WHERE user_id = ? AND type = ? AND expired_at > CURRENT_TIMESTAMP
                LIMIT 1"
            );

            $stmt->execute([$user_id, $type]);
            return $stmt->fetch();
        } catch (PDOException $e) {
            return false;
        }
    }

    public function incrementAttempts($user_id, $type)
    {
        try {
            $stmt = $this->db->prepare(
                "UPDATE password_resets
                SET attempts = CASE WHEN attempts < 5 THEN attempts + 1 ELSE 5 END
                WHERE user_id = ? AND type = ?"
            );
            return $stmt->execute([$user_id, $type]);
        } catch (PDOException $e) {
            return false;
        }
    }

    public function updatePassword($email, $hash_password)
    {
        try {
            $stmt = $this->db->prepare(
                "UPDATE users
                SET password = ?
                WHERE email = ? AND deleted_at IS NULL"
            );

            return $stmt->execute([$hash_password, $email]);
        } catch (PDOException $e) {
            return false;
        }
    }

    public function verifyEmail($email)
    {
        try {
            $stmt = $this->db->prepare(
                "UPDATE users
                SET is_email_verified = 1, email_verified_at = CURRENT_TIMESTAMP
                WHERE email = ?"
            );
            return $stmt->execute([$email]);
        } catch (PDOException $e) {
            return false;
        }
    }

    public function deleteToken($user_id, $type)
    {
        try {
            $stmt = $this->db->prepare(
                "DELETE FROM password_resets
                WHERE user_id = ? AND type = ?"
            );

            return $stmt->execute([$user_id, $type]);
        } catch (PDOException $e) {
            return false;
        }
    }

    public function getUserById($id)
    {
        try {
            $stmt = $this->db->prepare(
                "SELECT *
                FROM users
                WHERE id = ? AND deleted_at IS NULL
                LIMIT 1"
            );

            $stmt->execute([$id]);
            $user = $stmt->fetch();
            return [
                "success" => (bool)$user,
                "user_record" => $user ?: null
            ];
        } catch (PDOException $e) {
            return [
                "success" => false,
                "user_record" => null,
                "message" => $e->getMessage()
            ];
        }
    }
}
