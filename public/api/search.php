<?php
if (!defined('ROOT_PATH')) {
    define('ROOT_PATH', dirname(__DIR__, 2));
}
require_once ROOT_PATH . '/app/core/Database.php';

header('Content-Type: application/json');

try {
    $db = Database::getInstance()->getConnection();

    $query = isset($_GET['query']) ? trim($_GET['query']) : '';

    if (strlen($query) > 0) {
        $sql = "SELECT p.*, c.slug AS category_slug, c.name AS category_name
                FROM products AS p
                LEFT JOIN categories AS c ON p.category_id = c.id
                WHERE LOWER(p.name) LIKE LOWER(:search) AND p.deleted_at IS NULL
                ORDER BY p.average_rating DESC, p.id ASC
                LIMIT 5";

        $stmt = $db->prepare($sql);
        $stmt->execute(['search' => '%' . $query . '%']);
        $results = $stmt->fetchAll();

        echo json_encode($results);
    } else {
        echo json_encode([]);
    }
} catch (PDOException $e) {
    echo json_encode(['error' => 'Database connection failed']);
}
