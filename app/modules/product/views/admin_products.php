<?php
if (!isset($products)) {
    require_once ROOT_PATH . '/app/modules/product/admin_product_controller.php';
    $admin_product_controller = new AdminProductController();
    $products = $admin_product_controller->getAllProductsForAdmin();
    $categories = $admin_product_controller->getCategories();
    $locations = $admin_product_controller->getLocations();
}
?>

<div class="container-fluid px-0">
    <div class="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3">
        <div>
            <h2 class="fw-bold mb-1" style="color: #1f1712;">Product Management</h2>
            <p class="text-muted small mb-0">Add, edit, or hide dishes across restaurant branches</p>
        </div>
        <button type="button" class="btn btn-custom-primary rounded-pill px-4 py-2 fw-semibold"
            data-bs-toggle="modal" data-bs-target="#addProductModal">
            <i class="bi bi-plus-circle me-2"></i>Add New Dish
        </button>
    </div>

    <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0" style="min-width: 900px;">
                <thead class="table-dark">
                    <tr>
                        <th class="ps-4" style="width: 70px;">ID</th>
                        <th style="width: 80px;">Image</th>
                        <th style="min-width: 200px;">Dish Name</th>
                        <th style="width: 140px;">Category</th>
                        <th style="width: 110px;">Price</th>
                        <th style="width: 100px;">Rating</th>
                        <th style="width: 100px;">Status</th>
                        <th class="pe-4 text-end" style="width: 170px;">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (empty($products)): ?>
                        <tr>
                            <td colspan="8" class="text-center text-muted py-5">No dishes found.</td>
                        </tr>
                    <?php else: ?>
                        <?php foreach ($products as $product): ?>
                            <?php $isDeleted = $product['deleted_at'] !== null; ?>
                            <tr class="<?= $isDeleted ? 'table-secondary opacity-75' : '' ?>">
                                <td class="ps-4 fw-bold">#<?= (int)$product['id'] ?></td>
                                <td>
                                    <img src="<?= e($product['image_path']) ?>"
                                        alt="<?= e($product['name']) ?>"
                                        class="rounded-3 shadow-sm"
                                        style="width: 52px; height: 52px; object-fit: cover;">
                                </td>
                                <td>
                                    <div class="fw-bold" style="color: #1f1712;"><?= e($product['name']) ?></div>
                                    <div class="text-muted small text-truncate" style="max-width: 260px;">
                                        <?= e($product['description']) ?>
                                    </div>
                                </td>
                                <td>
                                    <span class="badge bg-light text-dark border">
                                        <?= e($product['category_name'] ?? 'N/A') ?>
                                    </span>
                                </td>
                                <td class="fw-bold text-nowrap" style="color: #d9381e;">
                                    <?= format_price($product['price']) ?>
                                </td>
                                <td>
                                    <?php if (!empty($product['average_rating'])): ?>
                                        <span class="badge bg-warning text-dark">
                                            ★ <?= number_format((float)$product['average_rating'], 1) ?>
                                        </span>
                                    <?php else: ?>
                                        <span class="text-muted small">—</span>
                                    <?php endif; ?>
                                </td>
                                <td>
                                    <?php if ($isDeleted): ?>
                                        <span class="badge bg-secondary">Hidden</span>
                                    <?php else: ?>
                                        <span class="badge bg-success">Active</span>
                                    <?php endif; ?>
                                </td>
                                <td class="pe-4 text-end text-nowrap">
                                    <button type="button" class="btn btn-sm btn-outline-primary rounded-pill me-1"
                                        data-bs-toggle="modal" data-bs-target="#editProductModal<?= (int)$product['id'] ?>">
                                        <i class="bi bi-pencil me-1"></i>Edit
                                    </button>
                                    <form action="index.php?page=admin_products&action=toggle_delete" method="POST" class="d-inline">
                                        <?= csrf_field() ?>
                                        <input type="hidden" name="product_id" value="<?= (int)$product['id'] ?>">
                                        <button type="submit" class="btn btn-sm <?= $isDeleted ? 'btn-success' : 'btn-danger' ?> rounded-pill">
                                            <i class="bi <?= $isDeleted ? 'bi-arrow-counterclockwise' : 'bi-eye-slash' ?> me-1"></i>
                                            <?= $isDeleted ? 'Restore' : 'Hide' ?>
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

<!-- Edit Modals (Placed OUTSIDE table for valid HTML5 DOM structure) -->
<?php if (!empty($products)): ?>
    <?php foreach ($products as $product): ?>
        <div class="modal fade" id="editProductModal<?= (int)$product['id'] ?>" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content rounded-4 border-0 shadow">
                    <form action="index.php?page=admin_products&action=update" method="POST" enctype="multipart/form-data">
                        <?= csrf_field() ?>
                        <input type="hidden" name="product_id" value="<?= (int)$product['id'] ?>">
                        <input type="hidden" name="image_url" value="<?= e($product['image_url']) ?>">

                        <div class="modal-header border-bottom">
                            <h5 class="modal-title fw-bold" style="color: #1f1712;">
                                Edit Dish #<?= (int)$product['id'] ?> - <?= e($product['name']) ?>
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>

                        <div class="modal-body p-4">
                            <div class="row g-3">
                                <div class="col-md-8">
                                    <label class="form-label fw-semibold">Dish Name</label>
                                    <input type="text" name="name" class="form-control" value="<?= e($product['name']) ?>" required>
                                </div>
                                <div class="col-md-4">
                                    <label class="form-label fw-semibold">Price (USD $)</label>
                                    <input type="number" step="0.01" min="0.50" name="price" class="form-control" value="<?= e($product['price']) ?>" required>
                                </div>

                                <div class="col-md-6">
                                    <label class="form-label fw-semibold">Category</label>
                                    <select name="category_id" class="form-select" required>
                                        <?php foreach ($categories as $cat): ?>
                                            <option value="<?= (int)$cat['id'] ?>" <?= ((int)$product['category_id'] === (int)$cat['id']) ? 'selected' : '' ?>>
                                                <?= e($cat['name']) ?>
                                            </option>
                                        <?php endforeach; ?>
                                    </select>
                                </div>

                                <div class="col-md-6">
                                    <label class="form-label fw-semibold">Slug (URL identifier)</label>
                                    <input type="text" name="slug" class="form-control" value="<?= e($product['slug']) ?>" required>
                                </div>

                                <div class="col-12">
                                    <label class="form-label fw-semibold">Description</label>
                                    <textarea name="description" class="form-control" rows="3" required><?= e($product['description']) ?></textarea>
                                </div>

                                <div class="col-md-6">
                                    <label class="form-label fw-semibold">Upload New Image (Optional)</label>
                                    <input type="file" name="image_file" class="form-control" accept=".webp,.jpg,.jpeg,.png">
                                    <div class="form-text small">Current image: <code><?= e($product['image_url']) ?></code></div>
                                </div>

                                <div class="col-md-6">
                                    <label class="form-label fw-semibold d-block">Available Branches</label>
                                    <?php foreach ($locations as $loc): ?>
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox"
                                                name="locations[]"
                                                value="<?= (int)$loc['id'] ?>"
                                                id="loc_<?= (int)$product['id'] ?>_<?= (int)$loc['id'] ?>"
                                                <?= in_array((int)$loc['id'], $product['location_id_array'] ?? [], true) ? 'checked' : '' ?>>
                                            <label class="form-check-label small" for="loc_<?= (int)$product['id'] ?>_<?= (int)$loc['id'] ?>">
                                                <?= e($loc['name']) ?>
                                            </label>
                                        </div>
                                    <?php endforeach; ?>
                                </div>
                            </div>
                        </div>

                        <div class="modal-footer border-top">
                            <button type="button" class="btn btn-light rounded-pill px-4" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-custom-primary rounded-pill px-4">Save Changes</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    <?php endforeach; ?>
<?php endif; ?>

<!-- Add New Dish Modal -->
<div class="modal fade" id="addProductModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content rounded-4 border-0 shadow">
            <form action="index.php?page=admin_products&action=create" method="POST" enctype="multipart/form-data">
                <?= csrf_field() ?>
                <div class="modal-header border-bottom">
                    <h5 class="modal-title fw-bold" style="color: #1f1712;">Add New Dish</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>

                <div class="modal-body p-4">
                    <div class="row g-3">
                        <div class="col-md-8">
                            <label class="form-label fw-semibold">Dish Name</label>
                            <input type="text" name="name" class="form-control" placeholder="e.g. Truffle Mushroom Risotto" required>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label fw-semibold">Price (USD $)</label>
                            <input type="number" step="0.01" min="0.50" name="price" class="form-control" placeholder="18.50" required>
                        </div>

                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Category</label>
                            <select name="category_id" class="form-select" required>
                                <?php foreach ($categories as $cat): ?>
                                    <option value="<?= (int)$cat['id'] ?>"><?= e($cat['name']) ?></option>
                                <?php endforeach; ?>
                            </select>
                        </div>

                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Slug (Optional - auto-generated if blank)</label>
                            <input type="text" name="slug" class="form-control" placeholder="truffle-mushroom-risotto">
                        </div>

                        <div class="col-12">
                            <label class="form-label fw-semibold">Description</label>
                            <textarea name="description" class="form-control" rows="3" maxlength="255" placeholder="Describe the ingredients and flavor profile..." required></textarea>
                        </div>

                        <div class="col-md-6">
                            <label class="form-label fw-semibold">Dish Image (WEBP, JPG, PNG)</label>
                            <input type="file" name="image_file" class="form-control" accept=".webp,.jpg,.jpeg,.png">
                            <div class="form-text small">Leave empty to use default category placeholder image.</div>
                        </div>

                        <div class="col-md-6">
                            <label class="form-label fw-semibold d-block">Available Branches</label>
                            <?php foreach ($locations as $loc): ?>
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox"
                                        name="locations[]"
                                        value="<?= (int)$loc['id'] ?>"
                                        id="new_loc_<?= (int)$loc['id'] ?>"
                                        checked>
                                    <label class="form-check-label small" for="new_loc_<?= (int)$loc['id'] ?>">
                                        <?= e($loc['name']) ?>
                                    </label>
                                </div>
                            <?php endforeach; ?>
                        </div>
                    </div>
                </div>

                <div class="modal-footer border-top">
                    <button type="button" class="btn btn-light rounded-pill px-4" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-custom-primary rounded-pill px-4">Create Dish</button>
                </div>
            </form>
        </div>
    </div>
</div>
