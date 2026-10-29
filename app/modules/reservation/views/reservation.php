<?php
if (!isset($locations)) {
    require_once ROOT_PATH . '/app/modules/reservation/reservation_controller.php';
    $resCtrl = new ReservationController();
    $locations = $resCtrl->getLocations();
}
$minDate = date('Y-m-d');
$maxDate = date('Y-m-d', strtotime('+10 days'));
?>
<!-- Reservation -->
<section class="py-5" id="reservation">
    <div class="container">
        <div class="reservation-bistro-card">
            <div class="row g-0">
                <!-- Left: info panel -->
                <aside class="col-lg-5 reservation-aside p-4 p-md-5">
                    <span class="section-eyebrow text-warning">Reservation</span>
                    <h2 class="font-serif-bistro fw-bold display-6 mb-3">Save your table at DaTeNO</h2>
                    <p class="opacity-75 mb-4">Celebrate birthdays, family dinners or business meetings in a warm, cozy atmosphere. We'll confirm your booking shortly.</p>

                    <ul class="reservation-info list-unstyled mb-4">
                        <li><i class="bi bi-clock"></i><div><strong>Opening hours</strong><span>Mon – Sun · 09:00 – 22:00</span></div></li>
                        <li><i class="bi bi-telephone"></i><div><strong>Hotline</strong><span>0819 152 362</span></div></li>
                        <li><i class="bi bi-geo-alt"></i><div><strong>Locations</strong><span>3 branches across Ho Chi Minh City</span></div></li>
                    </ul>

                    <div class="d-flex flex-wrap gap-2">
                        <span class="aside-pill"><i class="bi bi-people"></i>Up to 10 guests</span>
                        <span class="aside-pill"><i class="bi bi-gift"></i>Birthday setup</span>
                        <span class="aside-pill"><i class="bi bi-x-circle"></i>Free cancellation</span>
                    </div>
                </aside>

                <!-- Right: booking form -->
                <div class="col-lg-7 p-4 p-md-5">
                    <h3 class="fw-bold text-teal-dark h4 mb-1">Book a table</h3>
                    <p class="text-muted small mb-4">Reserve up to 10 days in advance at your preferred branch.</p>

                    <?php if (isset($_SESSION['reservation_success'])): ?>
                        <div class="alert alert-success rounded-4 d-flex align-items-center">
                            <i class="bi bi-check-circle-fill me-2"></i>
                            <?= e($_SESSION['reservation_success']);
                            unset($_SESSION['reservation_success']); ?>
                        </div>
                    <?php elseif (isset($_SESSION['reservation_error'])): ?>
                        <div class="alert alert-danger rounded-4 d-flex align-items-center">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            <?= e($_SESSION['reservation_error']);
                            unset($_SESSION['reservation_error']); ?>
                        </div>
                    <?php endif; ?>

                    <form id="reservationForm" action="index.php?page=reservation&action=create" method="POST">
                        <?= csrf_field() ?>
                        <div class="row g-3">
                            <div class="col-md-6">
                                <label for="fullName" class="form-label">Full name</label>
                                <input type="text" class="form-control" id="fullName" name="customer_name"
                                    value="<?= e($_SESSION['name'] ?? '') ?>" placeholder="Enter your full name" required>
                            </div>
                            <div class="col-md-6">
                                <label for="phone" class="form-label">Phone number</label>
                                <input type="tel" class="form-control" id="phone" name="customer_phone"
                                    value="<?= e($_SESSION['phone'] ?? '') ?>" placeholder="0123456789"
                                    minlength="10" maxlength="10" required>
                            </div>
                            <div class="col-md-6">
                                <label for="bookingDate" class="form-label">Date</label>
                                <input type="date" class="form-control" id="bookingDate" name="reservation_date"
                                    min="<?= $minDate ?>" max="<?= $maxDate ?>" value="<?= $minDate ?>" required>
                            </div>
                            <div class="col-md-6">
                                <label for="arrivalTime" class="form-label">Arrival time</label>
                                <input type="time" class="form-control" id="arrivalTime" name="reservation_time" value="18:30" required>
                            </div>
                            <div class="col-md-6">
                                <label for="bookingBranch" class="form-label">Branch</label>
                                <select id="bookingBranch" class="form-select" name="location_id" required>
                                    <option value="" disabled selected>Select a branch</option>
                                    <?php if (!empty($locations)): ?>
                                        <?php foreach ($locations as $loc): ?>
                                            <option value="<?= (int)$loc['id'] ?>"><?= e($loc['name']) ?> (<?= e($loc['address']) ?>)</option>
                                        <?php endforeach; ?>
                                    <?php else: ?>
                                        <option value="1">Ascent Restaurant - District 1</option>
                                        <option value="2">Ascent Restaurant - District 7</option>
                                        <option value="3">Ascent Restaurant - Thu Duc</option>
                                    <?php endif; ?>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label for="guests" class="form-label">Guests</label>
                                <select class="form-select" id="guests" name="guest_count" required>
                                    <?php for ($i = 1; $i <= 10; $i++): ?>
                                        <option value="<?= $i ?>" <?= $i === 2 ? 'selected' : '' ?>><?= $i ?> <?= $i === 1 ? 'person' : 'people' ?></option>
                                    <?php endfor; ?>
                                </select>
                            </div>
                            <div class="col-12">
                                <label for="bookingNotes" class="form-label">Special requests <span class="text-muted fw-normal">(optional)</span></label>
                                <textarea id="bookingNotes" class="form-control" name="special_requests" rows="3"
                                    placeholder="Birthday setup, window seat, dietary restrictions..."></textarea>
                            </div>
                            <div class="col-12 mt-4">
                                <button type="submit" class="btn btn-custom-primary btn-lg rounded-pill w-100">
                                    <i class="bi bi-calendar-check me-2"></i>Confirm reservation
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</section>
