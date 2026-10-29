<?php

use PHPUnit\Framework\TestCase;

require_once ROOT_PATH . '/app/modules/reservation/reservation_controller.php';
require_once ROOT_PATH . '/app/modules/reservation/admin_reservation_controller.php';
require_once ROOT_PATH . '/app/modules/user/admin_user_controller.php';

class ReservationAndAdminUserTest extends TestCase
{
    private ReservationService $reservationService;
    private AdminUserService $adminUserService;

    protected function setUp(): void
    {
        $_SESSION = [];
        TestDatabaseHelper::setup();
        $this->reservationService = new ReservationService();
        $this->adminUserService = new AdminUserService();
    }

    public function testReservationValidationAndLifecycle(): void
    {
        $resCtrl = new ReservationController();
        $locations = $resCtrl->getLocations();
        $this->assertCount(3, $locations);

        $tomorrow = date('Y-m-d', strtotime('+1 day'));

        // Empty fields
        $this->assertFalse($this->reservationService->createReservation([])['success']);

        // Invalid phone
        $badPhone = $this->reservationService->createReservation([
            'customer_name' => 'Alice',
            'customer_phone' => '123',
            'reservation_date' => $tomorrow,
            'reservation_time' => '19:00',
            'location_id' => 1,
            'guest_count' => 2
        ]);
        $this->assertFalse($badPhone['success']);

        // Past date
        $pastDate = $this->reservationService->createReservation([
            'customer_name' => 'Alice',
            'customer_phone' => '0901112223',
            'reservation_date' => date('Y-m-d', strtotime('-2 days')),
            'reservation_time' => '19:00',
            'location_id' => 1,
            'guest_count' => 2
        ]);
        $this->assertFalse($pastDate['success']);

        // Too far in future (>10 days)
        $farFuture = $this->reservationService->createReservation([
            'customer_name' => 'Alice',
            'customer_phone' => '0901112223',
            'reservation_date' => date('Y-m-d', strtotime('+15 days')),
            'reservation_time' => '19:00',
            'location_id' => 1,
            'guest_count' => 2
        ]);
        $this->assertFalse($farFuture['success']);

        // Valid reservation
        $validRes = $this->reservationService->createReservation([
            'customer_name' => 'Alice Wonderland',
            'customer_phone' => '0901112223',
            'reservation_date' => $tomorrow,
            'reservation_time' => '19:00',
            'location_id' => 1,
            'guest_count' => 4,
            'special_requests' => 'Window table please'
        ], 1);
        $this->assertTrue($validRes['success']);

        // User reservations list
        $userRes = $this->reservationService->getUserReservations(1);
        $this->assertCount(1, $userRes);
        $resId = (int)$userRes[0]['id'];

        // Admin reservation management
        $adminResCtrl = new AdminReservationController();
        $adminList = $adminResCtrl->getAllReservationsForAdmin('PENDING');
        $this->assertCount(1, $adminList);

        $this->assertTrue($this->reservationService->updateReservationStatus($resId, 'CONFIRMED')['success']);
        $this->assertTrue($this->reservationService->updateReservationStatus($resId, 'CANCELLED')['success']);
        $this->assertFalse($this->reservationService->updateReservationStatus($resId, 'INVALID')['success']);

        // Set back to PENDING to test user cancellation
        $this->reservationService->updateReservationStatus($resId, 'PENDING');
        $this->assertTrue($this->reservationService->cancelUserReservation(1, $resId)['success']);

        // Delete reservation
        $this->assertTrue($this->reservationService->deleteReservation($resId)['success']);
    }

    public function testAdminUserManagement(): void
    {
        $_SESSION['role'] = 'ADMIN';
        $adminUserCtrl = new AdminUserController();
        $users = $adminUserCtrl->getAllUsersForAdmin();
        $this->assertCount(2, $users);

        // Validation errors
        $this->assertFalse($this->adminUserService->saveUser(['name' => '', 'email' => '', 'phone' => ''])['success']);
        $this->assertFalse($this->adminUserService->saveUser(['name' => 'Bob', 'email' => 'bad', 'phone' => '0912345678'])['success']);
        $this->assertFalse($this->adminUserService->saveUser(['name' => 'Bob', 'email' => 'bob@test.com', 'phone' => '123'])['success']);

        // Create new user via Admin
        $created = $this->adminUserService->saveUser([
            'name' => 'Bob Builder',
            'email' => 'bob@dateno.com',
            'phone' => '0911223344',
            'role' => 'CUSTOMER',
            'password' => 'bobsecret123',
            'is_email_verified' => 1
        ]);
        $this->assertTrue($created['success']);

        // Update user #1 with new password
        $updated = $this->adminUserService->saveUser([
            'name' => 'Customer One Updated',
            'email' => 'customer1@dateno.com',
            'phone' => '0901234561',
            'role' => 'CUSTOMER',
            'password' => 'updatedpass123',
            'is_email_verified' => 1
        ], 1, 2);
        $this->assertTrue($updated['success']);

        // Prevent Admin #2 from demoting or deactivating themselves
        $selfDemote = $this->adminUserService->saveUser([
            'name' => 'Admin One',
            'email' => 'admin1@dateno.com',
            'phone' => '0901234562',
            'role' => 'CUSTOMER'
        ], 2, 2);
        $this->assertFalse($selfDemote['success']);

        $selfDeactivate = $this->adminUserService->toggleUserStatus(2, 2);
        $this->assertFalse($selfDeactivate['success']);

        // Deactivate and restore Customer #1
        $this->assertTrue($this->adminUserService->toggleUserStatus(1, 2)['success']);
        $this->assertTrue($this->adminUserService->toggleUserStatus(1, 2)['success']);
    }
}
