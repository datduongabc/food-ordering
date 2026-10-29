<!-- Menu list body -->
<?php if (empty($products)): ?>
    <div class="col-12">
        <div class="empty-state">
            <i class="bi bi-basket"></i>
            <h3>No dishes found</h3>
            <p>Try another category or check back later – our chefs are always cooking something new.</p>
        </div>
    </div>
<?php else: ?>
    <?php foreach ($products as $product): ?>
        <div class="col-6 col-md-4 col-lg-3">
            <article class="dish-card h-100">
                <a href="index.php?page=detail&slug=<?= e($product['slug']) ?>" class="dish-media">
                    <img src="<?= e($product['image_path']) ?>" alt="<?= e($product['name']) ?>" loading="lazy" decoding="async">

                    <?php if (!empty($product['category_name'])): ?>
                        <span class="dish-chip"><?= e($product['category_name']) ?></span>
                    <?php endif; ?>
                </a>

                <div class="dish-body">
                    <div class="d-flex justify-content-between align-items-start gap-2">
                        <a href="index.php?page=detail&slug=<?= e($product['slug']) ?>" class="text-decoration-none">
                            <h3 class="dish-title" title="<?= e($product['name']) ?>"><?= e($product['name']) ?></h3>
                        </a>
                        <?php if (!empty($product['average_rating'])): ?>
                            <span class="dish-rating"><i class="bi bi-star-fill"></i><?= number_format((float)$product['average_rating'], 1) ?></span>
                        <?php endif; ?>
                    </div>

                    <?php if (!empty($product['description'])): ?>
                        <p class="dish-desc"><?= e($product['description']) ?></p>
                    <?php endif; ?>

                    <div class="dish-meta">
                        <?php if (!empty($product['location_address'])): ?>
                            <a href="<?= e($product['location_link'] ?? '#') ?>" target="_blank" rel="noopener"
                                title="<?= e($product['location_address']) ?>" class="text-truncate">
                                <i class="bi bi-geo-alt"></i><?= e($product['location_address']) ?>
                            </a>
                        <?php else: ?>
                            <span><i class="bi bi-shop"></i>All branches</span>
                        <?php endif; ?>
                    </div>

                    <div class="dish-footer">
                        <span class="dish-price"><?= format_price($product['price']) ?></span>
                        <button type="button" class="btn-add-round js-add-to-cart"
                            data-product-id="<?= (int)$product['id'] ?>" data-quantity="1"
                            aria-label="Add <?= e($product['name']) ?> to cart" title="Add to cart">
                            <i class="bi bi-plus-lg"></i>
                        </button>
                    </div>
                </div>
            </article>
        </div>
    <?php endforeach; ?>
<?php endif; ?>

<!-- Displaying pagination -->
<?php if (($total_pages ?? 1) > 1): ?>
    <div class="col-12 mt-4">
        <nav aria-label="Menu pagination">
            <ul class="pagination justify-content-center custom-pagination">
                <?php
                $sort_param = isset($_GET['sort']) ? '&sort=' . e($_GET['sort']) : '';
                ?>

                <li class="page-product <?= ($current_page <= 1) ? 'disabled' : '' ?>">
                    <a class="page-link" href="?page=home&p=<?= $current_page - 1 ?><?= $sort_param ?>" aria-label="Previous page">
                        <i class="bi bi-chevron-left"></i>
                    </a>
                </li>

                <?php for ($i = 1; $i <= $total_pages; $i++): ?>
                    <li class="page-product <?= ($i === (int)$current_page) ? 'active' : '' ?>">
                        <a class="page-link" href="?page=home&p=<?= $i ?><?= $sort_param ?>"><?= $i ?></a>
                    </li>
                <?php endfor; ?>

                <li class="page-product <?= ($current_page >= $total_pages) ? 'disabled' : '' ?>">
                    <a class="page-link" href="?page=home&p=<?= $current_page + 1 ?><?= $sort_param ?>" aria-label="Next page">
                        <i class="bi bi-chevron-right"></i>
                    </a>
                </li>
            </ul>
        </nav>
    </div>
<?php endif; ?>
