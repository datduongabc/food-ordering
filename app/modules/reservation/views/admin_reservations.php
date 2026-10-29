<?php
$statusFilter = $_GET['status'] ?? null;
if (!isset($reservations)) {
    require_once ROOT_PATH . '/app/modules/reservation/admin_reservation_controller.php';
    $admin_reservation_controller = new AdminReservationController();
    $reservations = $admin_reservation_controller->getAllReservationsForAdmin($statusFilter);
}
$statuses = ['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED'];
?>

<div class="container-fluid px-0">
    <div class="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3">
        <div>
            <h2 class="fw-bold mb-1" style="color: #1f1712;">Reservation Management</h2>
            <p class="text-muted small mb-0">Manage customer table bookings and branch availability</p>
        </div>

        <div class="d-flex gap-2">
            <a href="index.php?page=admin_reservations"
                class="btn btn-sm rounded-pill px-3 <?= empty($statusFilter) ? 'btn-teal-dark' : 'btn-outline-secondary' ?>">
                All
            </a>
            <?php foreach ($statuses as $st): ?>
                <a href="index.php?page=admin_reservations&status=<?= $st ?>"
                    class="btn btn-sm rounded-pill px-3 <?= $statusFilter === $st ? 'btn-teal-dark' : 'btn-outline-secondary' ?>">
                    <?= $st ?>
                </a>
            <?php endforeach; ?>
        </div>
    </div>

    <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0" style="min-width: 900px;">
                <thead class="table-dark">
                    <tr>
                        <th class="ps-4" style="width: 70px;">ID</th>
                        <th style="min-width: 180px;">Customer</th>
                        <th style="min-width: 180px;">Branch</th>
                        <th style="width: 120px;">Date</th>
                        <th style="width: 90px;">Time</th>
                        <th style="width: 90px;">Guests</th>
                        <th style="width: 160px;">Status</th>
                        <th class="pe-4 text-end" style="width: 120px;">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (empty($reservations)): ?>
                        <tr>
                            <td colspan="8" class="text-center text-muted py-5">No reservations found.</td>
                        </tr>
                    <?php else: ?>
                        <?php foreach ($reservations as $res): ?>
                            <?php
                            $badgeClass = match ($res['status']) {
                                'COMPLETED' => 'bg-success',
                                'CONFIRMED' => 'bg-info text-dark',
                                'CANCELLED' => 'bg-danger',
                                default     => 'bg-warning text-dark'
                            };
                            ?>
                            <tr>
                                <td class="ps-4 fw-bold">#<?= (int)$res['id'] ?></td>
                                <td>
                                    <div class="fw-semibold" style="color: #1f1712;">
                                        <?= e($res['customer_name']) ?>
                                    </div>
                                    <div class="text-muted small">
                                        <?= e($res['customer_phone']) ?>
                                    </div>
                                </td>
                                <td>
                                    <div class="fw-semibold"><?= e($res['branch_title'] ?? '') ?></div>
                                    <div class="text-muted small"><?= e($res['branch_name'] ?? '') ?></div>
                                </td>
                                <td class="fw-semibold text-nowrap"><?= e($res['reservation_date']) ?></td>
                                <td class="text-nowrap"><?= e($res['reservation_time']) ?></td>
                                <td>
                                    <span class="badge bg-secondary bg-opacity-10 text-dark">
                                        <?= (int)$res['guest_count'] ?> guests
                                    </span>
                                </td>
                                <td>
                                    <form action="index.php?page=admin_reservations&action=update_status" method="POST" class="d-inline-flex align-items-center gap-1 mb-0">
                                        <?= csrf_field() ?>
                                        <input type="hidden" name="reservation_id" value="<?= (int)$res['id'] ?>">
                                        <select name="status" class="form-select form-select-sm fw-semibold" style="width: 140px;" onchange="this.form.submit()">
                                            <?php foreach ($statuses as $st): ?>
                                                <option value="<?= $st ?>" <?= $res['status'] === $st ? 'selected' : '' ?>>
                                                    <?= $st ?>
                                                </option>
                                            <?php endforeach; ?>
                                        </select>
                                    </form>
                                </td>
                                <td class="pe-4 text-end text-nowrap">
                                    <button type="button" class="btn btn-sm btn-info text-white me-1"
                                        data-bs-toggle="modal" data-bs-target="#viewResModal<?= (int)$res['id'] ?>">
                                        <i class="bi bi-eye"></i>
                                    </button>
                                    <form action="index.php?page=admin_reservations&action=delete" method="POST" class="d-inline"
                                        onsubmit="return confirm('Delete Reservation #<?= (int)$res['id'] ?>?');">
                                        <?= csrf_field() ?>
                                        <input type="hidden" name="reservation_id" value="<?= (int)$res['id'] ?>">
                                        <button type="submit" class="btn btn-sm btn-danger">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    </form>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- View Reservation Modals (Placed OUTSIDE table for valid HTML5 DOM structure) -->
<?php if (!empty($reservations)): ?>
    <?php foreach ($reservations as $res): ?>
        <?php
        $badgeClass = match ($res['status']) {
            'COMPLETED' => 'bg-success',
            'CONFIRMED' => 'bg-info text-dark',
            'CANCELLED' => 'bg-danger',
            default     => 'bg-warning text-dark'
        };
        ?>
        <div class="modal fade" id="viewResModal<?= (int)$res['id'] ?>" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content rounded-4 border-0 shadow">
                    <div class="modal-header border-bottom">
                        <h5 class="modal-title fw-bold" style="color: #1f1712;">
                            Reservation #<?= (int)$res['id'] ?> Details
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-4">
                        <dl class="row mb-0">
                            <dt class="col-sm-4 text-muted">Customer Name</dt>
                            <dd class="col-sm-8 fw-bold"><?= e($res['customer_name']) ?></dd>

                            <dt class="col-sm-4 text-muted">Phone Number</dt>
                            <dd class="col-sm-8"><?= e($res['customer_phone']) ?></dd>

                            <dt class="col-sm-4 text-muted">Branch</dt>
                            <dd class="col-sm-8"><?= e($res['branch_title'] ?? '') ?><br><small class="text-muted"><?= e($res['branch_name'] ?? '') ?></small></dd>

                            <dt class="col-sm-4 text-muted">Date & Time</dt>
                            <dd class="col-sm-8"><?= e($res['reservation_date']) ?> at <?= e($res['reservation_time']) ?></dd>

                            <dt class="col-sm-4 text-muted">Guests</dt>
                            <dd class="col-sm-8"><?= (int)$res['guest_count'] ?> people</dd>

                            <dt class="col-sm-4 text-muted">Status</dt>
                            <dd class="col-sm-8"><span class="badge <?= $badgeClass ?>"><?= e($res['status']) ?></span></dd>

                            <dt class="col-sm-4 text-muted">Special Requests</dt>
                            <dd class="col-sm-8 mb-0"><?= e($res['special_requests'] ?: 'None') ?></dd>
                        </dl>
                    </div>
                    <div class="modal-footer border-top">
                        <button type="button" class="btn btn-secondary rounded-pill px-4" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    <?php endforeach; ?>
<?php endif; ?>
