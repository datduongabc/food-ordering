<?php
if (!isset($highest_rating_item)) {
    require_once ROOT_PATH . '/app/modules/product/product_controller.php';
    $product_controller = new ProductController();
    $highest_rating_item = $product_controller->getHighestRating();
}
?>

<!-- Hero Section (Deliveroo / Uber Eats inspired: value proposition + featured dish) -->
<section class="hero-section">
    <div class="container">
        <div class="row align-items-center g-5">
            <div class="col-lg-6">
                <span class="hero-eyebrow"><i class="bi bi-stars me-1"></i>Freshly cooked · Delivered hot</span>
                <h1 class="hero-title font-serif-bistro">
                    Delicious food,<br>delivered to <span class="text-primary-orange">your door</span>.
                </h1>
                <p class="hero-subtitle">
                    Order chef-crafted dishes from DaTeNO in a few taps, pay securely with MoMo,
                    or reserve a table for a night out with family and friends.
                </p>

                <div class="d-flex flex-wrap gap-3 mb-4">
                    <a href="#menu-list" class="btn btn-custom-primary btn-lg rounded-pill px-4">
                        <i class="bi bi-bag-heart me-2"></i>Order Now
                    </a>
                    <a href="#reservation" class="btn btn-custom-teal btn-lg rounded-pill px-4">
                        <i class="bi bi-calendar2-check me-2"></i>Book a Table
                    </a>
                </div>

                <div class="hero-stats">
                    <div>
                        <strong>4.8<i class="bi bi-star-fill text-warning ms-1 small"></i></strong>
                        <span>Average rating</span>
                    </div>
                    <div>
                        <strong>25–35'</strong>
                        <span>Delivery time</span>
                    </div>
                    <div>
                        <strong>3</strong>
                        <span>Branches in HCMC</span>
                    </div>
                </div>
            </div>

            <div class="col-lg-6">
                <?php if ($highest_rating_item): ?>
                    <div class="hero-visual">
                        <a href="index.php?page=detail&slug=<?= e($highest_rating_item['slug']); ?>" class="hero-img-wrap">
                            <img src="<?= e($highest_rating_item['image_path']); ?>"
                                alt="<?= e($highest_rating_item['name']); ?>"
                                fetchpriority="high">
                        </a>

                        <div class="hero-float hero-float-top">
                            <span class="hero-float-icon bg-success-subtle text-success"><i class="bi bi-lightning-charge-fill"></i></span>
                            <div>
                                <div class="fw-bold small text-teal-dark">Fast preparation</div>
                                <div class="text-muted" style="font-size: .75rem;">Ready in ~15 minutes</div>
                            </div>
                        </div>

                        <div class="hero-float hero-float-bottom">
                            <span class="badge-best-seller mb-2"><i class="bi bi-trophy-fill"></i>Best seller</span>
                            <h2 class="h5 fw-bold text-teal-dark mb-1 text-truncate"><?= e($highest_rating_item['name']); ?></h2>
                            <div class="d-flex align-items-center justify-content-between gap-3">
                                <div>
                                    <span class="fw-bold text-primary-orange fs-5"><?= format_price($highest_rating_item['price']); ?></span>
                                    <?php if (!empty($highest_rating_item['average_rating'])): ?>
                                        <span class="small text-muted ms-2"><i class="bi bi-star-fill text-warning"></i>
                                            <?= number_format((float)$highest_rating_item['average_rating'], 1) ?></span>
                                    <?php endif; ?>
                                </div>
                                <button type="button" class="btn-add-round js-add-to-cart"
                                    data-product-id="<?= (int)$highest_rating_item['id'] ?>" data-quantity="1"
                                    aria-label="Add <?= e($highest_rating_item['name']); ?> to cart">
                                    <i class="bi bi-plus-lg"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                <?php endif; ?>
            </div>
        </div>
    </div>
</section>
