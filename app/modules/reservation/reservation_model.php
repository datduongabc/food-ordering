<?php

require_once ROOT_PATH . '/app/core/Database.php';

class ReservationModel
{
    private $db;

    public function __construct()
    {
        $this->db = Database::getInstance()->getConnection();
    }

    public function getLocations(): array
    {
        try {
            return $this->db->query("SELECT * FROM locations ORDER BY id ASC")->fetchAll();
        } catch (PDOException $e) {
            return [];
        }
    }

    public function createReservation(
        $user_id,
        $location_id,
        $customer_name,
        $customer_phone,
        $reservation_date,
        $reservation_time,
        $guest_count,
        $special_requests
    ) {
        try {
            $stmt = $this->db->prepare(
                "INSERT INTO reservations (user_id, location_id, customer_name, customer_phone, reservation_date, reservation_time, guest_count, special_requests)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            );
            return $stmt->execute([
                $user_id,
                $location_id,
                $customer_name,
                $customer_phone,
                $reservation_date,
                $reservation_time,
                $guest_count,
                $special_requests
            ]);
        } catch (PDOException $e) {
            error_log("Create Reservation Error: " . $e->getMessage());
            return false;
        }
    }

    public function getReservationsByUserId(int $userId): array
    {
        try {
            $sql = "SELECT r.*, l.name AS branch_title, l.address AS branch_name, l.url AS branch_url
                    FROM reservations r
                    LEFT JOIN locations l ON r.location_id = l.id
                    WHERE r.user_id = ?
                    ORDER BY r.reservation_date DESC, r.reservation_time DESC";
            $stmt = $this->db->prepare($sql);
            $stmt->execute([$userId]);
            return $stmt->fetchAll();
        } catch (PDOException $e) {
            return [];
        }
    }

    public function cancelUserReservation(int $userId, int $reservationId): bool
    {
        try {
            $stmt = $this->db->prepare(
                "UPDATE reservations
                 SET status = 'CANCELLED', cancelled_at = CURRENT_TIMESTAMP
                 WHERE id = ? AND user_id = ? AND status = 'PENDING'"
            );
            $stmt->execute([$reservationId, $userId]);
            return $stmt->rowCount() > 0;
        } catch (PDOException $e) {
            return false;
        }
    }

    public function getReservationsForAdmin(?string $status = null): array
    {
        try {
            $sql = "SELECT r.*, l.name AS branch_title, l.address AS branch_name, u.email AS user_email
                    FROM reservations r
                    LEFT JOIN locations l ON r.location_id = l.id
                    LEFT JOIN users u ON r.user_id = u.id";
            $params = [];

            if ($status && in_array($status, ['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED'], true)) {
                $sql .= " WHERE r.status = ?";
                $params[] = $status;
            }

            $sql .= " ORDER BY r.reservation_date DESC, r.reservation_time DESC";
            $stmt = $this->db->prepare($sql);
            $stmt->execute($params);
            return $stmt->fetchAll();
        } catch (PDOException $e) {
            return [];
        }
    }

    public function updateReservationStatus(int $id, string $status): bool
    {
        if (!in_array($status, ['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED'], true)) {
            return false;
        }
        try {
            if ($status === 'CANCELLED') {
                $stmt = $this->db->prepare(
                    "UPDATE reservations SET status = ?, cancelled_at = CURRENT_TIMESTAMP WHERE id = ?"
                );
            } else {
                $stmt = $this->db->prepare(
                    "UPDATE reservations SET status = ?, cancelled_at = NULL WHERE id = ?"
                );
            }
            return $stmt->execute([$status, $id]);
        } catch (PDOException $e) {
            return false;
        }
    }

    public function deleteReservation(int $id): bool
    {
        try {
            $stmt = $this->db->prepare("DELETE FROM reservations WHERE id = ?");
            return $stmt->execute([$id]);
        } catch (PDOException $e) {
            return false;
        }
    }
}
