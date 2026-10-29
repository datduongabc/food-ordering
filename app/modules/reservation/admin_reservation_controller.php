<?php
require_once ROOT_PATH . '/app/modules/reservation/reservation_service.php';

class AdminReservationController
{
    private $reservationService;

    public function __construct()
    {
        $this->reservationService = new ReservationService();
    }

    public function getAllReservationsForAdmin(?string $status = null)
    {
        return $this->reservationService->getReservationForAdmin($status);
    }

    public function handleAction(): void
    {
        if (!isset($_SESSION['role']) || $_SESSION['role'] !== 'ADMIN') {
            header("Location: index.php?page=signin");
            exit();
        }

        $action = $_GET['action'] ?? '';

        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            if ($action === 'update_status') {
                $id = (int)($_POST['reservation_id'] ?? 0);
                $status = trim($_POST['status'] ?? '');
                $res = $this->reservationService->updateReservationStatus($id, $status);
                $_SESSION[$res['success'] ? 'admin_success' : 'admin_error'] = $res['message'];
            } elseif ($action === 'delete') {
                $id = (int)($_POST['reservation_id'] ?? 0);
                $res = $this->reservationService->deleteReservation($id);
                $_SESSION[$res['success'] ? 'admin_success' : 'admin_error'] = $res['message'];
            }
            header("Location: index.php?page=admin_reservations");
            exit();
        }
    }
}
