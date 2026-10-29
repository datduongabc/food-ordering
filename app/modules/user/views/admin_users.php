<?php
if (!isset($users)) {
    require_once ROOT_PATH . '/app/modules/user/admin_user_controller.php';
    $admin_user_controller = new AdminUserController();
    $users = $admin_user_controller->getAllUsersForAdmin();
}
$currentAdminId = (int)($_SESSION['user_id'] ?? 0);
?>

<div class="container-fluid px-0">
    <div class="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3">
        <div>
            <h2 class="fw-bold mb-1" style="color: #1f1712;">User Management</h2>
            <p class="text-muted small mb-0">Manage customer accounts, administrator roles, and verification status</p>
        </div>
        <button type="button" class="btn btn-custom-primary rounded-pill px-4 py-2 fw-semibold"
            data-bs-toggle="modal" data-bs-target="#addUserModal">
            <i class="bi bi-person-plus me-2"></i>Add New User
        </button>
    </div>

    <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0" style="min-width: 900px;">
                <thead class="table-dark">
                    <tr>
                        <th class="ps-4" style="width: 70px;">ID</th>
                        <th style="min-width: 180px;">Full Name</th>
                        <th style="min-width: 200px;">Email</th>
                        <th style="width: 110px;">Role</th>
                        <th style="width: 120px;">Phone</th>
                        <th style="width: 140px;">Email Verification</th>
                        <th style="width: 100px;">Status</th>
                        <th class="pe-4 text-end" style="width: 160px;">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (empty($users)): ?>
                        <tr>
                            <td colspan="8" class="text-center text-muted py-5">No users found.</td>
                        </tr>
                    <?php else: ?>
                        <?php foreach ($users as $user): ?>
                            <?php
                            $isDeleted = $user['deleted_at'] !== null;
                            $isSelf = ((int)$user['id'] === $currentAdminId);
                            ?>
                            <tr class="<?= $isDeleted ? 'table-secondary opacity-75' : '' ?>">
                                <td class="ps-4 fw-bold">#<?= (int)$user['id'] ?></td>
                                <td>
                                    <div class="fw-bold" style="color: #1f1712;">
                                        <?= e($user['name']) ?>
                                        <?php if ($isSelf): ?>
                                            <span class="badge bg-info text-dark ms-1">You</span>
                                        <?php endif; ?>
                                    </div>
                                </td>
                                <td><?= e($user['email']) ?></td>
                                <td>
                                    <span class="badge <?= $user['role'] === 'ADMIN' ? 'bg-dark' : 'bg-secondary bg-opacity-25 text-dark' ?> rounded-pill px-3">
                                        <?= e($user['role']) ?>
                                    </span>
                                </td>
                                <td><?= e($user['phone']) ?></td>
                                <td>
                                    <?php if ((int)$user['is_email_verified'] === 1): ?>
                                        <span class="badge bg-success bg-opacity-10 text-success">
                                            <i class="bi bi-check-circle-fill me-1"></i>Verified
                                        </span>
                                    <?php else: ?>
                                        <span class="badge bg-warning bg-opacity-25 text-dark">Unverified</span>
                                    <?php endif; ?>
                                </td>
                                <td>
                                    <?php if ($isDeleted): ?>
                                        <span class="badge bg-danger rounded-pill">Deactivated</span>
                                    <?php else: ?>
                                        <span class="badge bg-success rounded-pill">Active</span>
                                    <?php endif; ?>
                                </td>
                                <td class="pe-4 text-end text-nowrap">
                                    <button type="button" class="btn btn-sm btn-warning me-1 rounded-pill"
                                        data-bs-toggle="modal" data-bs-target="#editUserModal<?= (int)$user['id'] ?>">
                                        <i class="bi bi-pencil-square me-1"></i>Edit
                                    </button>

                                    <?php if (!$isSelf): ?>
                                        <form action="index.php?page=admin_users&action=toggle_delete" method="POST" class="d-inline">
                                            <?= csrf_field() ?>
                                            <input type="hidden" name="user_id" value="<?= (int)$user['id'] ?>">
                                            <button type="submit" class="btn btn-sm <?= $isDeleted ? 'btn-success' : 'btn-danger' ?> rounded-pill">
                                                <?= $isDeleted ? 'Restore' : 'Deactivate' ?>
                                            </button>
                                        </form>
                                    <?php endif; ?>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Edit User Modals (Placed OUTSIDE table for valid HTML5 DOM structure) -->
<?php if (!empty($users)): ?>
    <?php foreach ($users as $user): ?>
        <?php $isSelf = ((int)$user['id'] === $currentAdminId); ?>
        <div class="modal fade" id="editUserModal<?= (int)$user['id'] ?>" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content rounded-4 border-0 shadow">
                    <form action="index.php?page=admin_users&action=update" method="POST">
                        <?= csrf_field() ?>
                        <input type="hidden" name="user_id" value="<?= (int)$user['id'] ?>">

                        <div class="modal-header border-bottom">
                            <h5 class="modal-title fw-bold" style="color: #1f1712;">
                                Edit User #<?= (int)$user['id'] ?>
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>

                        <div class="modal-body p-4">
                            <div class="mb-3">
                                <label class="form-label fw-semibold">Full Name</label>
                                <input type="text" name="name" class="form-control" value="<?= e($user['name']) ?>" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label fw-semibold">Email Address</label>
                                <input type="email" name="email" class="form-control" value="<?= e($user['email']) ?>" required>
                            </div>
                            <div class="row g-3 mb-3">
                                <div class="col-md-6">
                                    <label class="form-label fw-semibold">Phone (10 digits)</label>
                                    <input type="tel" name="phone" class="form-control" minlength="10" maxlength="10" value="<?= e($user['phone']) ?>" required>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label fw-semibold">Role</label>
                                    <select name="role" class="form-select" <?= $isSelf ? 'disabled' : '' ?>>
                                        <option value="CUSTOMER" <?= $user['role'] === 'CUSTOMER' ? 'selected' : '' ?>>CUSTOMER</option>
                                        <option value="ADMIN" <?= $user['role'] === 'ADMIN' ? 'selected' : '' ?>>ADMIN</option>
                                    </select>
                                    <?php if ($isSelf): ?>
                                        <input type="hidden" name="role" value="ADMIN">
                                    <?php endif; ?>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label class="form-label fw-semibold">New Password (leave blank to keep current)</label>
                                <input type="password" name="password" class="form-control" minlength="8" placeholder="••••••••">
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="is_email_verified" value="1"
                                    id="verify_user_<?= (int)$user['id'] ?>"
                                    <?= (int)$user['is_email_verified'] === 1 ? 'checked' : '' ?>>
                                <label class="form-check-label fw-semibold" for="verify_user_<?= (int)$user['id'] ?>">
                                    Email Verified
                                </label>
                            </div>
                        </div>

                        <div class="modal-footer border-top">
                            <button type="button" class="btn btn-light rounded-pill px-4" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-custom-primary rounded-pill px-4">Save User</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    <?php endforeach; ?>
<?php endif; ?>

<!-- Add New User Modal -->
<div class="modal fade" id="addUserModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4 border-0 shadow">
            <form action="index.php?page=admin_users&action=create" method="POST">
                <?= csrf_field() ?>
                <div class="modal-header border-bottom">
                    <h5 class="modal-title fw-bold" style="color: #1f1712;">Create New User</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>

                <div class="modal-body p-4">
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Full Name</label>
                        <input type="text" name="name" class="form-control" placeholder="John Doe" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Email Address</label>
                        <input type="email" name="email" class="form-control" placeholder="john@example.com" required>
                    </div>
                    <div class="row g-3 mb-3">
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Phone Number</label>
                            <input type="tel" name="phone" class="form-control" minlength="10" maxlength="10" placeholder="0123456789" required>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Role</label>
                            <select name="role" class="form-select">
                                <option value="CUSTOMER" selected>CUSTOMER</option>
                                <option value="ADMIN">ADMIN</option>
                            </select>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Initial Password (min 8 chars)</label>
                        <input type="password" name="password" class="form-control" minlength="8" placeholder="••••••••" required>
                    </div>
                </div>

                <div class="modal-footer border-top">
                    <button type="button" class="btn btn-light rounded-pill px-4" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-custom-primary rounded-pill px-4">Create User</button>
                </div>
            </form>
        </div>
    </div>
</div>
