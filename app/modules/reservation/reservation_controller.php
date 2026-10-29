<?php
require_once ROOT_PATH . '/app/modules/reservation/reservation_service.php';

class ReservationController
{
    private $reservationService;

    public function __construct()
    {
        $this->reservationService = new ReservationService();
    }

    public function getLocations(): array
    {
        return $this->reservationService->getLocations();
    }

    public function createReservation()
    {
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            $user_id = $_SESSION['user_id'] ?? null;
            $result = $this->reservationService->createReservation($_POST, $user_id);

            if ($result['success']) {
                $_SESSION['reservation_success'] = $result['message'];
            } else {
                $_SESSION['reservation_error'] = $result['message'];
            }

            header("Location: index.php?page=home#reservation");
            exit();
        }
    }

    public function cancelMyReservation()
    {
        if (!isset($_SESSION['user_id'])) {
            header("Location: index.php?page=signin");
            exit();
        }

        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            $reservationId = (int)($_POST['reservation_id'] ?? 0);
            $result = $this->reservationService->cancelUserReservation((int)$_SESSION['user_id'], $reservationId);

            if ($result['success']) {
                $_SESSION['flash_success'] = $result['message'];
            } else {
                $_SESSION['flash_error'] = $result['message'];
            }
        }

        header("Location: index.php?page=orders&tab=reservations");
        exit();
    }
}
