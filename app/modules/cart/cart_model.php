<?php

require_once ROOT_PATH . '/app/core/Database.php';

class CartModel
{
    private $db;

    public function __construct()
    {
        $this->db = Database::getInstance()->getConnection();
    }

    public function getUserCartItems(int $userId): array
    {
        $sql = "SELECT ci.id AS cart_item_id, ci.product_id, ci.quantity,
                       p.name, p.price, p.slug, p.image_url, p.description,
                       c.slug AS category_slug, c.name AS category_name
                FROM cart_items ci
                JOIN products p ON ci.product_id = p.id
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE ci.user_Id = ? AND p.deleted_at IS NULL
                ORDER BY ci.id ASC";
        $stmt = $this->db->prepare($sql);
        $stmt->execute([$userId]);
        return $stmt->fetchAll();
    }

    public function getProductsByIds(array $productIds): array
    {
        if (empty($productIds)) {
            return [];
        }
        $placeholders = implode(',', array_fill(0, count($productIds), '?'));
        $sql = "SELECT p.id AS product_id, p.name, p.price, p.slug, p.image_url, p.description,
                       c.slug AS category_slug, c.name AS category_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.id IN ($placeholders) AND p.deleted_at IS NULL";
        $stmt = $this->db->prepare($sql);
        $stmt->execute(array_values($productIds));
        return $stmt->fetchAll();
    }

    public function findProductById(int $productId)
    {
        $stmt = $this->db->prepare(
            "SELECT p.*, c.slug AS category_slug
             FROM products p
             LEFT JOIN categories c ON p.category_id = c.id
             WHERE p.id = ? AND p.deleted_at IS NULL
             LIMIT 1"
        );
        $stmt->execute([$productId]);
        return $stmt->fetch();
    }

    public function getCartItem(int $userId, int $productId)
    {
        $stmt = $this->db->prepare(
            "SELECT * FROM cart_items WHERE user_Id = ? AND product_id = ? LIMIT 1"
        );
        $stmt->execute([$userId, $productId]);
        return $stmt->fetch();
    }

    public function addOrIncrementItem(int $userId, int $productId, int $quantity): bool
    {
        $existing = $this->getCartItem($userId, $productId);
        if ($existing) {
            $newQty = min(99, (int)$existing['quantity'] + $quantity);
            $stmt = $this->db->prepare(
                "UPDATE cart_items SET quantity = ? WHERE id = ? AND user_Id = ?"
            );
            return $stmt->execute([$newQty, $existing['id'], $userId]);
        }

        $qty = min(99, max(1, $quantity));
        $stmt = $this->db->prepare(
            "INSERT INTO cart_items (user_Id, product_id, quantity) VALUES (?, ?, ?)"
        );
        return $stmt->execute([$userId, $productId, $qty]);
    }

    public function updateItemQuantity(int $userId, int $productId, int $quantity): bool
    {
        if ($quantity <= 0) {
            return $this->removeItem($userId, $productId);
        }
        $qty = min(99, $quantity);
        $stmt = $this->db->prepare(
            "UPDATE cart_items SET quantity = ? WHERE user_Id = ? AND product_id = ?"
        );
        return $stmt->execute([$qty, $userId, $productId]);
    }

    public function removeItem(int $userId, int $productId): bool
    {
        $stmt = $this->db->prepare(
            "DELETE FROM cart_items WHERE user_Id = ? AND product_id = ?"
        );
        return $stmt->execute([$userId, $productId]);
    }

    public function clearUserCart(int $userId): bool
    {
        $stmt = $this->db->prepare("DELETE FROM cart_items WHERE user_Id = ?");
        return $stmt->execute([$userId]);
    }

    public function countUserCartItems(int $userId): int
    {
        $stmt = $this->db->prepare("SELECT COALESCE(SUM(quantity), 0) FROM cart_items WHERE user_Id = ?");
        $stmt->execute([$userId]);
        return (int)$stmt->fetchColumn();
    }
}
