<?php

require_once ROOT_PATH . '/app/modules/reservation/reservation_model.php';

class ReservationService
{
    private $reservationModel;

    public function __construct()
    {
        $this->reservationModel = new ReservationModel();
    }

    public function getLocations(): array
    {
        return $this->reservationModel->getLocations();
    }

    public function createReservation($data, $user_id = null)
    {
        $customer_name = trim($data['customer_name'] ?? '');
        $customer_phone = trim($data['customer_phone'] ?? '');
        $reservation_date = trim($data['reservation_date'] ?? '');
        $reservation_time = trim($data['reservation_time'] ?? '');
        $location_id = (int)($data['location_id'] ?? 0);
        $guest_count = (int)($data['guest_count'] ?? 0);
        $special_requests = trim($data['special_requests'] ?? '');

        if (
            empty($customer_name) ||
            empty($customer_phone) ||
            empty($reservation_date) ||
            empty($reservation_time) ||
            empty($guest_count) ||
            empty($location_id)
        ) {
            return [
                'success' => false,
                'message' => 'Please fill in all required fields.'
            ];
        }

        if ($location_id <= 0) {
            return [
                'success' => false,
                'message' => 'Invalid branch selection.'
            ];
        }

        if ($guest_count <= 0 || $guest_count > 20) {
            return [
                'success' => false,
                'message' => 'Invalid number of guests selection.'
            ];
        }

        if (strlen($customer_phone) !== 10 || !ctype_digit($customer_phone)) {
            return [
                'success' => false,
                'message' => 'Invalid phone number. Must be 10 digits.'
            ];
        }

        $today = date('Y-m-d');
        $parsedDate = strtotime($reservation_date);
        if ($parsedDate === false) {
            return [
                'success' => false,
                'message' => 'Invalid reservation date.'
            ];
        }

        $reservation_date = date('Y-m-d', $parsedDate);
        if ($reservation_date < $today) {
            return [
                'success' => false,
                'message' => 'Reservation date cannot be in the past.'
            ];
        }

        $max_date = date('Y-m-d', strtotime('+10 days'));
        if ($reservation_date > $max_date) {
            return [
                'success' => false,
                'message' => 'Reservations can only be made up to 10 days in advance.'
            ];
        }

        $reservation_time = date('H:i:s', strtotime($reservation_time));

        $status = $this->reservationModel->createReservation(
            $user_id,
            $location_id,
            $customer_name,
            $customer_phone,
            $reservation_date,
            $reservation_time,
            $guest_count,
            $special_requests
        );

        if (!$status) {
            return [
                'success' => false,
                'message' => 'An error occurred while booking your table. Please try again.'
            ];
        }

        return [
            'success' => true,
            'message' => 'Table reserved successfully! We look forward to welcoming you.'
        ];
    }

    public function getUserReservations(int $userId): array
    {
        return $this->reservationModel->getReservationsByUserId($userId);
    }

    public function cancelUserReservation(int $userId, int $reservationId): array
    {
        $cancelled = $this->reservationModel->cancelUserReservation($userId, $reservationId);
        return [
            'success' => $cancelled,
            'message' => $cancelled
                ? "Reservation #{$reservationId} has been cancelled."
                : "Cannot cancel this reservation."
        ];
    }

    public function getReservationForAdmin(?string $status = null): array
    {
        return $this->reservationModel->getReservationsForAdmin($status);
    }

    public function updateReservationStatus(int $id, string $status): array
    {
        $updated = $this->reservationModel->updateReservationStatus($id, $status);
        return [
            'success' => $updated,
            'message' => $updated
                ? "Reservation #{$id} status updated to {$status}."
                : "Failed to update reservation status."
        ];
    }

    public function deleteReservation(int $id): array
    {
        $deleted = $this->reservationModel->deleteReservation($id);
        return [
            'success' => $deleted,
            'message' => $deleted
                ? "Reservation #{$id} deleted."
                : "Failed to delete reservation."
        ];
    }
}
