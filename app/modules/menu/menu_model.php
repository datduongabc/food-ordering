<?php

require_once ROOT_PATH . '/app/core/Database.php';

class MenuDetailModel
{
    private $db;

    public function __construct()
    {
        $this->db = Database::getInstance()->getConnection();
    }

    public function getProductBySlug($slug)
    {
        $stmt = $this->db->prepare(
            "SELECT p.*, c.name AS category_name, c.slug AS category_slug
             FROM products p
             LEFT JOIN categories c ON p.category_id = c.id
             WHERE p.slug = :slug AND p.deleted_at IS NULL
             LIMIT 1"
        );
        $stmt->execute(['slug' => $slug]);
        $product = $stmt->fetch();

        if (!$product) {
            return null;
        }

        // Fetch available locations for this product
        $stmtLoc = $this->db->prepare(
            "SELECT l.*
             FROM locations l
             JOIN product_availabilities pa ON l.id = pa.location_id
             WHERE pa.product_id = ?
             ORDER BY l.id ASC"
        );
        $stmtLoc->execute([$product['id']]);
        $product['locations'] = $stmtLoc->fetchAll();

        return $product;
    }

    public function getReviewsByProductId(int $productId): array
    {
        $stmt = $this->db->prepare(
            "SELECT r.*, u.name AS user_name
             FROM reviews r
             LEFT JOIN users u ON r.user_id = u.id
             WHERE r.product_id = ?
             ORDER BY r.created_at DESC, r.id DESC"
        );
        $stmt->execute([$productId]);
        return $stmt->fetchAll();
    }

    public function addReview(int $userId, int $productId, int $rating, string $comment): bool
    {
        try {
            $stmt = $this->db->prepare(
                "INSERT INTO reviews (user_id, product_id, rating, comment)
                 VALUES (?, ?, ?, ?)"
            );
            $ok = $stmt->execute([$userId, $productId, $rating, $comment]);

            if ($ok) {
                // Ensure average_rating is updated even if trigger is not active
                $stmtAvg = $this->db->prepare(
                    "UPDATE products
                     SET average_rating = (SELECT ROUND(AVG(rating), 2) FROM reviews WHERE product_id = ?)
                     WHERE id = ?"
                );
                $stmtAvg->execute([$productId, $productId]);
            }

            return $ok;
        } catch (PDOException $e) {
            error_log("Add Review Error: " . $e->getMessage());
            return false;
        }
    }
}
