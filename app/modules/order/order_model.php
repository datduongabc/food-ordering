<?php

require_once ROOT_PATH . '/app/core/Database.php';

class OrderModel
{
    private $db;

    public function __construct()
    {
        $this->db = Database::getInstance()->getConnection();
    }

    public function createOrderFromItems(int $userId, array $cartItems, string $paymentMethod = 'COD')
    {
        $paymentMethod = strtoupper(trim($paymentMethod)) === 'MOMO' ? 'MOMO' : 'COD';

        try {
            $this->db->beginTransaction();

            $stmtOrder = $this->db->prepare(
                "INSERT INTO orders (user_id, total_price, status, payment_method, payment_status)
                 VALUES (?, 0.00, 'PENDING', ?, 'UNPAID')"
            );
            $stmtOrder->execute([$userId, $paymentMethod]);
            $orderId = (int)$this->db->lastInsertId();

            $stmtItem = $this->db->prepare(
                "INSERT INTO order_items (order_id, product_id, price_at_purchase, quantity)
                 VALUES (?, ?, ?, ?)"
            );

            foreach ($cartItems as $item) {
                $stmtItem->execute([
                    $orderId,
                    (int)$item['product_id'],
                    (float)$item['price'],
                    (int)$item['quantity']
                ]);
            }

            // Ensure total_price is exact regardless of whether MySQL trigger is active
            $stmtTotal = $this->db->prepare(
                "UPDATE orders
                 SET total_price = (
                     SELECT COALESCE(SUM(price_at_purchase * quantity), 0.00)
                     FROM order_items
                     WHERE order_id = ?
                 )
                 WHERE id = ?"
            );
            $stmtTotal->execute([$orderId, $orderId]);

            // Clear user's cart
            $stmtClear = $this->db->prepare("DELETE FROM cart_items WHERE user_Id = ?");
            $stmtClear->execute([$userId]);

            $this->db->commit();
            return $orderId;
        } catch (PDOException $e) {
            if ($this->db->inTransaction()) {
                $this->db->rollBack();
            }
            error_log("Create Order Error: " . $e->getMessage());
            return false;
        }
    }

    public function getOrderByIdAndUser(int $orderId, int $userId)
    {
        $stmt = $this->db->prepare("SELECT * FROM orders WHERE id = ? AND user_id = ? LIMIT 1");
        $stmt->execute([$orderId, $userId]);
        $order = $stmt->fetch();
        if (!$order) {
            return false;
        }

        $itemsByOrder = $this->getOrderItemsByOrderIds([$orderId]);
        $order['items'] = $itemsByOrder[$orderId] ?? [];
        return $order;
    }

    public function attachMomoOrderId(int $orderId, string $momoOrderId): bool
    {
        $stmt = $this->db->prepare(
            "UPDATE orders SET payment_method = 'MOMO', momo_order_id = ? WHERE id = ?"
        );
        return $stmt->execute([$momoOrderId, $orderId]);
    }

    public function markOrderPaid(int $orderId, string $momoOrderId, string $transId): bool
    {
        $stmt = $this->db->prepare(
            "UPDATE orders
             SET payment_method = 'MOMO',
                 payment_status = 'PAID',
                 momo_order_id = ?,
                 momo_trans_id = ?,
                 status = CASE WHEN status = 'PENDING' THEN 'CONFIRMED' ELSE status END
             WHERE id = ?"
        );
        return $stmt->execute([$momoOrderId, $transId, $orderId]);
    }

    public function markOrderPaymentFailed(int $orderId, string $momoOrderId): bool
    {
        $stmt = $this->db->prepare(
            "UPDATE orders
             SET payment_method = 'MOMO',
                 payment_status = 'FAILED',
                 momo_order_id = ?
             WHERE id = ? AND payment_status != 'PAID'"
        );
        return $stmt->execute([$momoOrderId, $orderId]);
    }

    public function getOrdersByUserId(int $userId): array
    {
        $stmt = $this->db->prepare(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC, id DESC"
        );
        $stmt->execute([$userId]);
        $orders = $stmt->fetchAll();

        if (empty($orders)) {
            return [];
        }

        $orderIds = array_column($orders, 'id');
        $itemsByOrder = $this->getOrderItemsByOrderIds($orderIds);

        foreach ($orders as &$order) {
            $oid = (int)$order['id'];
            $order['items'] = $itemsByOrder[$oid] ?? [];
        }

        return $orders;
    }

    public function getOrderItemsByOrderIds(array $orderIds): array
    {
        if (empty($orderIds)) {
            return [];
        }

        $placeholders = implode(',', array_fill(0, count($orderIds), '?'));
        $sql = "SELECT oi.*, p.name AS product_name, p.slug AS product_slug, p.image_url,
                       c.slug AS category_slug
                FROM order_items oi
                LEFT JOIN products p ON oi.product_id = p.id
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE oi.order_id IN ($placeholders)
                ORDER BY oi.id ASC";
        $stmt = $this->db->prepare($sql);
        $stmt->execute(array_values($orderIds));
        $rows = $stmt->fetchAll();

        $grouped = [];
        foreach ($rows as $row) {
            $oid = (int)$row['order_id'];
            $grouped[$oid][] = $row;
        }
        return $grouped;
    }

    public function cancelUserOrder(int $userId, int $orderId): bool
    {
        $stmt = $this->db->prepare(
            "UPDATE orders
             SET status = 'CANCELLED'
             WHERE id = ? AND user_id = ? AND status = 'PENDING'"
        );
        $stmt->execute([$orderId, $userId]);
        return $stmt->rowCount() > 0;
    }

    public function getAllOrdersForAdmin(?string $status = null): array
    {
        $sql = "SELECT o.*, u.name AS customer_name, u.email AS customer_email, u.phone AS customer_phone
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.id";
        $params = [];

        if ($status && in_array($status, ['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED'], true)) {
            $sql .= " WHERE o.status = ?";
            $params[] = $status;
        }

        $sql .= " ORDER BY o.created_at DESC, o.id DESC";
        $stmt = $this->db->prepare($sql);
        $stmt->execute($params);
        $orders = $stmt->fetchAll();

        if (!empty($orders)) {
            $orderIds = array_column($orders, 'id');
            $itemsByOrder = $this->getOrderItemsByOrderIds($orderIds);
            foreach ($orders as &$order) {
                $oid = (int)$order['id'];
                $order['items'] = $itemsByOrder[$oid] ?? [];
            }
        }

        return $orders;
    }

    public function updateOrderStatus(int $orderId, string $status): bool
    {
        if (!in_array($status, ['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED'], true)) {
            return false;
        }
        $stmt = $this->db->prepare("UPDATE orders SET status = ? WHERE id = ?");
        return $stmt->execute([$status, $orderId]);
    }

    public function deleteOrder(int $orderId): bool
    {
        $stmt = $this->db->prepare("DELETE FROM orders WHERE id = ?");
        return $stmt->execute([$orderId]);
    }

    public function getDashboardSummary(): array
    {
        $totalRevenue = (float)$this->db->query(
            "SELECT COALESCE(SUM(total_price), 0) FROM orders WHERE status = 'COMPLETED'"
        )->fetchColumn();

        $totalOrders = (int)$this->db->query(
            "SELECT COUNT(*) FROM orders"
        )->fetchColumn();

        $pendingOrders = (int)$this->db->query(
            "SELECT COUNT(*) FROM orders WHERE status = 'PENDING'"
        )->fetchColumn();

        $totalProducts = (int)$this->db->query(
            "SELECT COUNT(*) FROM products WHERE deleted_at IS NULL"
        )->fetchColumn();

        $totalUsers = (int)$this->db->query(
            "SELECT COUNT(*) FROM users WHERE deleted_at IS NULL"
        )->fetchColumn();

        $totalReservations = (int)$this->db->query(
            "SELECT COUNT(*) FROM reservations"
        )->fetchColumn();

        $pendingReservations = (int)$this->db->query(
            "SELECT COUNT(*) FROM reservations WHERE status = 'PENDING'"
        )->fetchColumn();

        return [
            'total_revenue' => $totalRevenue,
            'total_orders' => $totalOrders,
            'pending_orders' => $pendingOrders,
            'total_products' => $totalProducts,
            'total_users' => $totalUsers,
            'total_reservations' => $totalReservations,
            'pending_reservations' => $pendingReservations
        ];
    }
}
