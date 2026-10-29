<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= $product ? e($product['name']) . ' - DaTeNO' : 'Dish Not Found - DaTeNO' ?></title>
    <!-- Bootstrap -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js" defer></script>
    <!-- Custom -->
    <link rel="stylesheet" href="<?= base_url('css/style.css') ?>">
    <link rel="stylesheet" href="<?= base_url('css/header.css') ?>">
    <link rel="stylesheet" href="<?= base_url('css/pages.css') ?>">
    <link rel="stylesheet" href="<?= base_url('css/footer.css') ?>">
    <script src="<?= base_url('js/header/search.js') ?>" defer></script>
    <script src="<?= base_url('js/cart/cart.js') ?>" defer></script>
</head>

<body class="d-flex flex-column min-vh-100 page-shell">
    <?php include ROOT_PATH . '/app/core/views/layouts/header.php'; ?>

    <main class="flex-grow-1 page-main">
        <div class="container">
            <!-- Breadcrumb -->
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb breadcrumb-warm">
                    <li class="breadcrumb-item"><a href="index.php?page=home">Home</a></li>
                    <li class="breadcrumb-item"><a href="index.php?page=home#menu-list">Menu</a></li>
                    <li class="breadcrumb-item active" aria-current="page"><?= e($product['name'] ?? 'Dish Not Found') ?></li>
                </ol>
            </nav>

            <?php if (!$product): ?>
                <div class="panel empty-panel">
                    <div class="empty-icon"><i class="bi bi-emoji-frown"></i></div>
                    <h3>Dish not found</h3>
                    <p>The dish you are looking for does not exist or is no longer available.</p>
                    <a href="index.php?page=home#menu-list" class="btn btn-custom-primary rounded-pill px-4 py-2">Back to Menu</a>
                </div>
            <?php else: ?>
                <?php
                $reviews = $product['reviews'] ?? [];
                $reviewCount = count($reviews);
                $avgRating = !empty($product['average_rating']) ? (float)$product['average_rating'] : null;
                ?>
                <div class="row g-4 g-lg-5 mb-5">
                    <!-- Image -->
                    <div class="col-lg-6">
                        <div class="detail-gallery">
                            <img src="<?= e($product['image_path']) ?>" alt="<?= e($product['name']) ?>">
                        </div>
                    </div>

                    <!-- Info & buy box -->
                    <div class="col-lg-6">
                        <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
                            <span class="chip-soft"><?= e($product['category_name'] ?? 'Signature Dish') ?></span>
                            <?php if ($avgRating): ?>
                                <a href="#reviews-section" class="rating-pill text-decoration-none">
                                    <i class="bi bi-star-fill"></i><?= number_format($avgRating, 1) ?>
                                    <span class="text-muted fw-normal">(<?= $reviewCount ?> review<?= $reviewCount === 1 ? '' : 's' ?>)</span>
                                </a>
                            <?php else: ?>
                                <span class="rating-pill"><i class="bi bi-stars"></i>New dish</span>
                            <?php endif; ?>
                        </div>

                        <h1 class="detail-title font-serif-bistro mb-2"><?= e($product['name']) ?></h1>
                        <div class="detail-price mb-3"><?= format_price($product['price']) ?></div>
                        <p class="detail-desc mb-4"><?= e($product['description']) ?></p>

                        <div class="detail-perks mb-4">
                            <div class="detail-perk"><i class="bi bi-clock-history"></i>Ready in ~15'</div>
                            <div class="detail-perk"><i class="bi bi-basket2"></i>Fresh daily</div>
                            <div class="detail-perk"><i class="bi bi-truck"></i>Hot delivery</div>
                        </div>

                        <form action="index.php?page=cart&action=add" method="POST" class="panel panel-pad mb-4">
                            <?= csrf_field() ?>
                            <input type="hidden" name="product_id" value="<?= (int)$product['id'] ?>">

                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <span class="fw-bold text-teal-dark">Quantity</span>
                                <div class="qty-stepper qty-lg">
                                    <button type="button" class="js-qty-btn" data-step="-1" aria-label="Decrease quantity"><i class="bi bi-dash"></i></button>
                                    <input type="number" name="quantity" id="qty-input" value="1" min="1" max="20" aria-label="Quantity">
                                    <button type="button" class="js-qty-btn" data-step="1" aria-label="Increase quantity"><i class="bi bi-plus"></i></button>
                                </div>
                            </div>

                            <div class="buy-bar">
                                <button type="submit" class="btn btn-custom-teal btn-lg rounded-pill px-4 flex-grow-1">
                                    <i class="bi bi-bag-plus me-2"></i>Add to cart
                                </button>
                                <button type="submit" name="redirect_cart" value="1" class="btn btn-custom-primary btn-lg rounded-pill px-4 flex-grow-1">
                                    <i class="bi bi-lightning-charge-fill me-2"></i>Order now
                                </button>
                            </div>
                        </form>

                        <?php if (!empty($product['locations'])): ?>
                            <div>
                                <div class="fw-bold text-teal-dark small mb-2">Available at</div>
                                <?php foreach ($product['locations'] as $loc): ?>
                                    <a href="<?= e($loc['url']) ?>" target="_blank" rel="noopener" class="branch-link">
                                        <i class="bi bi-geo-alt-fill"></i>
                                        <span><strong><?= e($loc['name']) ?></strong><br><span class="text-muted"><?= e($loc['address']) ?></span></span>
                                    </a>
                                <?php endforeach; ?>
                            </div>
                        <?php endif; ?>
                    </div>
                </div>

                <!-- Customer Reviews Section -->
                <section id="reviews-section">
                    <div class="row g-4">
                        <div class="col-lg-7">
                            <div class="panel panel-pad h-100">
                                <h2 class="panel-title fs-5">Customer reviews</h2>

                                <?php if ($avgRating): ?>
                                    <div class="rating-summary">
                                        <span class="big"><?= number_format($avgRating, 1) ?></span>
                                        <div>
                                            <div class="review-stars fs-6">
                                                <?php for ($s = 1; $s <= 5; $s++): ?>
                                                    <i class="bi <?= $s <= round($avgRating) ? 'bi-star-fill' : 'bi-star' ?>"></i>
                                                <?php endfor; ?>
                                            </div>
                                            <div class="small text-muted">Based on <?= $reviewCount ?> review<?= $reviewCount === 1 ? '' : 's' ?></div>
                                        </div>
                                    </div>
                                <?php endif; ?>

                                <?php if (empty($reviews)): ?>
                                    <div class="text-center py-4 text-muted">
                                        <i class="bi bi-chat-square-heart fs-1 text-primary-orange d-block mb-2"></i>
                                        No reviews yet. Be the first to share your experience!
                                    </div>
                                <?php else: ?>
                                    <?php foreach ($reviews as $rev): ?>
                                        <?php $revName = $rev['user_name'] ?? 'Guest'; ?>
                                        <div class="review-item">
                                            <span class="review-avatar"><?= e(mb_strtoupper(mb_substr($revName, 0, 1))) ?></span>
                                            <div class="flex-grow-1">
                                                <div class="d-flex flex-wrap justify-content-between align-items-center gap-2">
                                                    <strong class="text-teal-dark"><?= e($revName) ?></strong>
                                                    <small class="text-muted"><?= e(date('M d, Y', strtotime($rev['created_at']))) ?></small>
                                                </div>
                                                <div class="review-stars mb-1">
                                                    <?php for ($s = 1; $s <= 5; $s++): ?>
                                                        <i class="bi <?= $s <= (int)$rev['rating'] ? 'bi-star-fill' : 'bi-star' ?>"></i>
                                                    <?php endfor; ?>
                                                </div>
                                                <p class="mb-0 text-body"><?= e($rev['comment']) ?></p>
                                            </div>
                                        </div>
                                    <?php endforeach; ?>
                                <?php endif; ?>
                            </div>
                        </div>

                        <div class="col-lg-5">
                            <div class="panel panel-pad summary-card">
                                <h2 class="panel-title fs-5">Write a review</h2>
                                <?php if (isset($_SESSION['user_id'])): ?>
                                    <form action="index.php?page=detail&slug=<?= urlencode($product['slug']) ?>&action=review" method="POST" class="form-warm">
                                        <?= csrf_field() ?>
                                        <input type="hidden" name="product_id" value="<?= (int)$product['id'] ?>">

                                        <div class="mb-3">
                                            <div class="form-label fw-semibold small text-teal-dark">Your rating</div>
                                            <div class="star-input" role="radiogroup" aria-label="Rating">
                                                <?php for ($s = 5; $s >= 1; $s--): ?>
                                                    <input type="radio" name="rating" id="star<?= $s ?>" value="<?= $s ?>" <?= $s === 5 ? 'checked' : '' ?> required>
                                                    <label for="star<?= $s ?>" title="<?= $s ?> star<?= $s > 1 ? 's' : '' ?>"><i class="bi bi-star-fill"></i></label>
                                                <?php endfor; ?>
                                            </div>
                                        </div>

                                        <div class="mb-3">
                                            <label for="reviewComment" class="form-label fw-semibold small text-teal-dark">Your comment</label>
                                            <textarea id="reviewComment" name="comment" class="form-control" rows="4" placeholder="How was the flavour and presentation?" required></textarea>
                                        </div>

                                        <button type="submit" class="btn btn-custom-primary rounded-pill w-100 py-2">
                                            <i class="bi bi-send me-2"></i>Submit review
                                        </button>
                                    </form>
                                <?php else: ?>
                                    <p class="text-muted small mb-3">Please sign in to leave a rating and review for this dish.</p>
                                    <a href="index.php?page=signin" class="btn btn-custom-teal rounded-pill w-100">Sign in to review</a>
                                <?php endif; ?>
                            </div>
                        </div>
                    </div>
                </section>
            <?php endif; ?>
        </div>
    </main>

    <?php include ROOT_PATH . '/app/core/views/layouts/footer.php'; ?>
</body>

</html>
