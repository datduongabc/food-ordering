<?php

require_once ROOT_PATH . '/app/core/Database.php';

class ProductModel
{
    private $db;

    public function __construct()
    {
        $this->db = Database::getInstance()->getConnection();
    }

    public function getFeatured()
    {
        $driver = $this->db->getAttribute(PDO::ATTR_DRIVER_NAME);
        $orderRating = ($driver === 'pgsql')
            ? "p.average_rating DESC NULLS LAST, p.id ASC"
            : "p.average_rating DESC, p.id ASC";

        $sql = "SELECT p.*, c.slug AS category_slug, c.name AS category_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.deleted_at IS NULL
                ORDER BY {$orderRating}
                LIMIT 1";
        return $this->db->query($sql)->fetch();
    }

    // For displaying menu lists on the screen (compatible with PostgreSQL, MySQL, and SQLite)
    public function getProducts($limit, $offset, $sort)
    {
        $driver = $this->db->getAttribute(PDO::ATTR_DRIVER_NAME);
        if ($driver === 'pgsql') {
            $aggAddress = "STRING_AGG(l.address, ', ')";
        } elseif ($driver === 'sqlite') {
            $aggAddress = "GROUP_CONCAT(l.address, ', ')";
        } else {
            $aggAddress = "GROUP_CONCAT(l.address SEPARATOR ', ')";
        }

        $sql = "SELECT p.*, c.slug AS category_slug, c.name AS category_name,
                {$aggAddress} AS location_address,
                MIN(l.url) AS location_link
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN product_availabilities pa ON p.id = pa.product_id
                LEFT JOIN locations l ON pa.location_id = l.id
                WHERE p.deleted_at IS NULL";

        if ($sort === "starters" || $sort === "main_dishes") {
            $sql .= " AND c.slug = :category_slug";
        }

        $sql .= " GROUP BY p.id, c.slug, c.name";

        switch ($sort) {
            case 'price_asc':
                $sql .= " ORDER BY p.price ASC, p.id ASC";
                break;
            case 'price_desc':
                $sql .= " ORDER BY p.price DESC, p.id ASC";
                break;
            case 'rating_asc':
                $sql .= ($driver === 'pgsql')
                    ? " ORDER BY p.average_rating ASC NULLS FIRST, p.id ASC"
                    : " ORDER BY p.average_rating ASC, p.id ASC";
                break;
            case 'rating_desc':
                $sql .= ($driver === 'pgsql')
                    ? " ORDER BY p.average_rating DESC NULLS LAST, p.id ASC"
                    : " ORDER BY p.average_rating DESC, p.id ASC";
                break;
            default:
                $sql .= " ORDER BY p.id ASC";
                break;
        }

        $sql .= " LIMIT :limit OFFSET :offset";

        $stmt = $this->db->prepare($sql);

        if ($sort === "starters" || $sort === "main_dishes") {
            $stmt->bindValue(':category_slug', $sort, PDO::PARAM_STR);
        }
        $stmt->bindValue(':limit', (int)$limit, PDO::PARAM_INT);
        $stmt->bindValue(':offset', (int)$offset, PDO::PARAM_INT);

        $stmt->execute();
        return $stmt->fetchAll();
    }

    public function countProducts($sort)
    {
        $sql = "SELECT COUNT(p.id) FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.deleted_at IS NULL";

        if ($sort === "starters" || $sort === "main_dishes") {
            $sql .= " AND c.slug = :category_slug";
            $stmt = $this->db->prepare($sql);
            $stmt->bindValue(':category_slug', $sort, PDO::PARAM_STR);
            $stmt->execute();
        } else {
            $stmt = $this->db->query($sql);
        }

        return (int)$stmt->fetchColumn();
    }

    // For Admin Management
    public function getAllProductsForAdmin()
    {
        $driver = $this->db->getAttribute(PDO::ATTR_DRIVER_NAME);
        $aggLocIds = ($driver === 'pgsql')
            ? "STRING_AGG(CAST(pa.location_id AS TEXT), ',')"
            : "GROUP_CONCAT(pa.location_id)";

        $sql = "SELECT p.*, c.name AS category_name, c.slug AS category_slug,
                       {$aggLocIds} AS location_ids
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN product_availabilities pa ON p.id = pa.product_id
                GROUP BY p.id, c.name, c.slug
                ORDER BY p.id ASC";
        return $this->db->query($sql)->fetchAll();
    }

    public function getProductById(int $id)
    {
        $stmt = $this->db->prepare(
            "SELECT p.*, c.slug AS category_slug
             FROM products p
             LEFT JOIN categories c ON p.category_id = c.id
             WHERE p.id = ?
             LIMIT 1"
        );
        $stmt->execute([$id]);
        return $stmt->fetch();
    }

    public function getCategories(): array
    {
        return $this->db->query("SELECT * FROM categories WHERE deleted_at IS NULL ORDER BY id ASC")->fetchAll();
    }

    public function getLocations(): array
    {
        return $this->db->query("SELECT * FROM locations ORDER BY id ASC")->fetchAll();
    }

    public function createProduct(array $data, array $locationIds): bool
    {
        try {
            $this->db->beginTransaction();

            $stmt = $this->db->prepare(
                "INSERT INTO products (category_id, image_url, name, description, price, slug)
                 VALUES (?, ?, ?, ?, ?, ?)"
            );
            $stmt->execute([
                $data['category_id'],
                $data['image_url'],
                $data['name'],
                $data['description'],
                $data['price'],
                $data['slug']
            ]);

            $productId = (int)$this->db->lastInsertId();
            $this->syncProductLocations($productId, $locationIds);

            $this->db->commit();
            return true;
        } catch (PDOException $e) {
            if ($this->db->inTransaction()) {
                $this->db->rollBack();
            }
            error_log("Create Product Error: " . $e->getMessage());
            return false;
        }
    }

    public function updateProduct(int $id, array $data, array $locationIds): bool
    {
        try {
            $this->db->beginTransaction();

            $stmt = $this->db->prepare(
                "UPDATE products
                 SET category_id = ?, image_url = ?, name = ?, description = ?, price = ?, slug = ?
                 WHERE id = ?"
            );
            $stmt->execute([
                $data['category_id'],
                $data['image_url'],
                $data['name'],
                $data['description'],
                $data['price'],
                $data['slug'],
                $id
            ]);

            $this->syncProductLocations($id, $locationIds);

            $this->db->commit();
            return true;
        } catch (PDOException $e) {
            if ($this->db->inTransaction()) {
                $this->db->rollBack();
            }
            error_log("Update Product Error: " . $e->getMessage());
            return false;
        }
    }

    private function syncProductLocations(int $productId, array $locationIds): void
    {
        $stmtDel = $this->db->prepare("DELETE FROM product_availabilities WHERE product_id = ?");
        $stmtDel->execute([$productId]);

        if (!empty($locationIds)) {
            $stmtIns = $this->db->prepare(
                "INSERT INTO product_availabilities (product_id, location_id) VALUES (?, ?)"
            );
            foreach ($locationIds as $locId) {
                $locId = (int)$locId;
                if ($locId > 0) {
                    $stmtIns->execute([$productId, $locId]);
                }
            }
        }
    }

    public function toggleSoftDelete(int $id): bool
    {
        $product = $this->getProductById($id);
        if (!$product) {
            return false;
        }

        if ($product['deleted_at'] === null) {
            $stmt = $this->db->prepare("UPDATE products SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?");
        } else {
            $stmt = $this->db->prepare("UPDATE products SET deleted_at = NULL WHERE id = ?");
        }

        return $stmt->execute([$id]);
    }
}
